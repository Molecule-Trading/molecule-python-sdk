from __future__ import annotations

import base64

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey

from molecule.auth import (
    HEADER_KEY_ID,
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    Signer,
    canonical_string,
    canonical_ws,
    empty_body_hash,
    load_private_key,
    sha256_hex,
    sorted_query,
)

# Throwaway key. Do not use in production.
SEED_B64 = "cgxIy78BcAUooPsgrAXQPYDW5h0zLru6Lg35Ga4pEP0="
SEED_HEX = "720c48cbbf01700528a0fb20ac05d03d80d6e61d332ebbba2e0df919ae2910fd"
PUB_HEX = "8e327a0b81c69835c15a957526da18a10522c7f8218fd2e35ff6cb0ef6b53714"
KEY_ID = "key_test_1"

REST_METHOD = "POST"
REST_PATH = "/v1/orders"
REST_QUERY = {"subaccount_id": "sa_1"}
REST_TS = "1727270000000"
REST_BODY = b'{"side":"BUY","qty":"10"}'


def _verify(canonical: bytes, signature_b64: str) -> None:
    verify_key = VerifyKey(PUB_HEX, encoder=HexEncoder)
    verify_key.verify(canonical, base64.b64decode(signature_b64))


def test_load_private_key_formats() -> None:
    a = load_private_key(SEED_B64)
    b = load_private_key(SEED_HEX)
    c = load_private_key(bytes.fromhex(SEED_HEX))
    assert a.encode() == b.encode() == c.encode()
    assert a.verify_key.encode().hex() == PUB_HEX


def test_empty_body_hash() -> None:
    assert empty_body_hash() == sha256_hex(b"")
    assert empty_body_hash() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_sorted_query_order() -> None:
    assert sorted_query({"b": "2", "a": "1"}) == "a=1&b=2"
    assert sorted_query(None) == ""
    assert sorted_query({"key_id": "x", "venue": "Demo"}, drop={"key_id"}) == "venue=Demo"


def test_rest_canonical_and_vector() -> None:
    body_hash = sha256_hex(REST_BODY)
    canonical = canonical_string(REST_METHOD, REST_PATH, REST_QUERY, REST_TS, REST_BODY)
    expected = "\n".join(
        [REST_METHOD, REST_PATH, "subaccount_id=sa_1", REST_TS, body_hash]
    ).encode()
    assert canonical == expected
    assert canonical.count(b"\n") == 4

    signer = Signer(KEY_ID, SEED_B64)
    headers = signer.rest_headers(REST_METHOD, REST_PATH, REST_QUERY, REST_BODY, REST_TS)
    assert headers[HEADER_KEY_ID] == KEY_ID
    assert headers[HEADER_TIMESTAMP] == REST_TS
    _verify(canonical, headers[HEADER_SIGNATURE])

    raw_sig = SigningKey(bytes.fromhex(SEED_HEX)).sign(canonical).signature
    assert headers[HEADER_SIGNATURE] == base64.b64encode(raw_sig).decode()


def test_rest_empty_body_blank_query() -> None:
    canonical = canonical_string("GET", "/v1/venues", None, "1727270000000", b"")
    assert canonical == (
        "GET\n"
        "/v1/venues\n"
        "\n"
        "1727270000000\n"
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    ).encode()
    signer = Signer(KEY_ID, SEED_HEX)
    headers = signer.rest_headers("GET", "/v1/venues", None, b"", "1727270000000")
    _verify(canonical, headers[HEADER_SIGNATURE])


def test_seconds_timestamp_converted_to_ms() -> None:
    signer = Signer(KEY_ID, SEED_B64)
    headers = signer.rest_headers("GET", "/v1/venues", None, b"", 1_727_270_000)
    assert headers[HEADER_TIMESTAMP] == "1727270000000"


def test_ws_canonical_and_vector() -> None:
    path = "/v1/ws/orders"
    query = {"subaccount_id": "sa_1", "key_id": "should_drop", "ts": "drop", "sig": "drop"}
    ts = "1727270000000"
    canonical = canonical_ws(path, query, ts)
    assert canonical == b"WS\n/v1/ws/orders\nsubaccount_id=sa_1\n1727270000000"

    signer = Signer(KEY_ID, SEED_B64)
    signed = signer.ws_query(path, {"subaccount_id": "sa_1"}, ts)
    assert signed["key_id"] == KEY_ID
    assert signed["ts"] == ts
    assert signed["subaccount_id"] == "sa_1"
    _verify(canonical, signed["sig"])
