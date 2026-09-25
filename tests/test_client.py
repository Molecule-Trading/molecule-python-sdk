from __future__ import annotations

import base64

import json

import httpx
import pytest

from molecule import (
    ConflictError,
    ForbiddenError,
    Molecule,
    RoutingUnavailableError,
    UnauthorizedError,
)
from molecule.auth import HEADER_KEY_ID, HEADER_SIGNATURE, HEADER_TIMESTAMP, Signer, sha256_hex
from molecule.client import encode_body

SEED_B64 = "cgxIy78BcAUooPsgrAXQPYDW5h0zLru6Lg35Ga4pEP0="
KEY_ID = "key_test_1"
BASE = "https://api.molecule.example"


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if request.method == "GET" and path == "/v1/markets/search":
        assert request.url.params.get("q") == "house"
        assert request.url.params.get("venue") == "Demo"
        return httpx.Response(200, json={"items": [{"instrument_id": 42, "venue": "Demo"}]})
    if request.method == "POST" and path == "/v1/orders":
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["client_order_id"] == "desk-house-1"
        assert request.headers.get("Idempotency-Key") == "desk-house-1"
        assert request.headers.get(HEADER_KEY_ID) == KEY_ID
        assert HEADER_TIMESTAMP in request.headers
        assert HEADER_SIGNATURE in request.headers
        return httpx.Response(
            200,
            json={"id": "ord_1", "status": "PENDING_SUBMISSION", "client_order_id": "desk-house-1"},
        )
    if request.method == "POST" and path == "/v1/orders/conflict":
        return httpx.Response(
            409,
            json={
                "error": "idempotency_conflict",
                "message": "same key different body",
                "details": {"key": "desk-house-1"},
            },
        )
    if path == "/v1/human":
        return httpx.Response(
            403,
            json={"error": "human_session_required", "message": "trading key rejected"},
        )
    if path == "/v1/replay":
        return httpx.Response(401, json={"error": "replay", "message": "duplicate signature"})
    if path == "/v1/route":
        return httpx.Response(
            400,
            json={"error": "ROUTING_UNAVAILABLE", "message": "no live venue"},
        )
    return httpx.Response(404, json={"error": "not_found", "message": path})


def _client() -> Molecule:
    return Molecule(
        base_url=BASE,
        key_id=KEY_ID,
        private_key=SEED_B64,
        transport=httpx.MockTransport(_handler),
    )


def test_base_url_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MOLECULE_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="base_url"):
        Molecule(key_id=KEY_ID, private_key=SEED_B64)


def test_base_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOLECULE_BASE_URL", BASE)
    client = Molecule(key_id=KEY_ID, private_key=SEED_B64, transport=httpx.MockTransport(_handler))
    assert client.base_url == BASE


def test_search_markets_mocked() -> None:
    client = _client()
    out = client.search_markets(q="house", venue="Demo")
    assert out["items"][0]["instrument_id"] == 42


def test_create_order_mocked_and_signed() -> None:
    client = _client()
    order = client.create_order(
        subaccount_id="sa_1",
        instrument_id=42,
        side="BUY",
        type="LIMIT",
        tif="GTC",
        price="0.48",
        qty="10",
        routing={"mode": "DIRECT"},
        client_order_id="desk-house-1",
    )
    assert order["status"] == "PENDING_SUBMISSION"
    assert order["id"] == "ord_1"


def test_header_construction_matches_signer() -> None:
    body = {"side": "BUY", "qty": "10", "client_order_id": "desk-house-1"}
    raw = encode_body(body)
    signer = Signer(KEY_ID, SEED_B64)
    headers = signer.rest_headers("POST", "/v1/orders", None, raw, "1727270000000")
    assert set(headers) == {HEADER_KEY_ID, HEADER_TIMESTAMP, HEADER_SIGNATURE}
    assert headers[HEADER_TIMESTAMP] == "1727270000000"
    assert len(base64.b64decode(headers[HEADER_SIGNATURE])) == 64
    assert sha256_hex(raw) != sha256_hex(b"")


def test_idempotency_header_from_client_order_id() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["idem"] = request.headers.get("Idempotency-Key", "")
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(200, json={"ok": True})

    client = Molecule(
        base_url=BASE,
        key_id=KEY_ID,
        private_key=SEED_B64,
        transport=httpx.MockTransport(handler),
    )
    client.orders.create(client_order_id="abc-1", qty="1", side="BUY")
    assert captured["idem"] == "abc-1"
    assert "abc-1" in captured["body"]


def test_complex_order_idempotency_key() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["idem"] = request.headers.get("Idempotency-Key", "")
        assert request.url.path == "/v1/complex-orders"
        return httpx.Response(200, json={"id": "cpx_1", "status": "PENDING_SUBMISSION"})

    client = Molecule(
        base_url=BASE,
        key_id=KEY_ID,
        private_key=SEED_B64,
        transport=httpx.MockTransport(handler),
    )
    client.complex_orders.create(type="ICEBERG", idempotency_key="cpx-9", qty="100")
    assert captured["idem"] == "cpx-9"


def test_typed_errors() -> None:
    client = _client()
    with pytest.raises(ConflictError) as conflict:
        client.request("POST", "/v1/orders/conflict")
    assert conflict.value.error == "idempotency_conflict"

    with pytest.raises(ForbiddenError) as forbidden:
        client.request("GET", "/v1/human")
    assert forbidden.value.error == "human_session_required"

    with pytest.raises(UnauthorizedError) as unauthorized:
        client.request("GET", "/v1/replay")
    assert unauthorized.value.error == "replay"

    with pytest.raises(RoutingUnavailableError):
        client.request("GET", "/v1/route")


def test_ws_url_includes_signing_query() -> None:
    client = _client()
    url = client.ws.orders({"subaccount_id": "sa_1"})
    assert url.startswith("wss://api.molecule.example/v1/ws/orders?")
    assert "key_id=key_test_1" in url
    assert "ts=" in url
    assert "sig=" in url
    assert "subaccount_id=sa_1" in url
