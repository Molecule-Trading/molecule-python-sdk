from __future__ import annotations

import json
import os
from collections.abc import Iterator, Mapping
from typing import Any

import httpx

from molecule.auth import Signer
from molecule.errors import error_from_response
from molecule.markets import MarketsAPI
from molecule.orders import ComplexOrdersAPI, OrdersAPI
from molecule.portfolio import PortfolioAPI, RiskAPI
from molecule.ws import WebSocketAPI

DEFAULT_TIMEOUT = 30.0
USER_AGENT = "molecule-python/0.1.0"


def encode_body(payload: Mapping[str, Any] | list[Any] | None) -> bytes:
    if payload is None:
        return b""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class Molecule:
    """Synchronous client. Private key stays in this process."""

    def __init__(
        self,
        base_url: str | None = None,
        key_id: str | None = None,
        private_key: str | bytes | None = None,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        resolved = (base_url or os.environ.get("MOLECULE_BASE_URL") or "").rstrip("/")
        if not resolved:
            raise ValueError("base_url is required (constructor arg or MOLECULE_BASE_URL)")
        self.base_url = resolved
        self.key_id = key_id
        self.token = token
        self.timeout = timeout
        self.signer = Signer(key_id, private_key) if key_id and private_key is not None else None
        self._transport = transport
        self.markets = MarketsAPI(self)
        self.orders = OrdersAPI(self)
        self.complex_orders = ComplexOrdersAPI(self)
        self.portfolio = PortfolioAPI(self)
        self.risk = RiskAPI(self)
        self.ws = WebSocketAPI(self)

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self._transport,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | list[Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        clean = None
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
        body = encode_body(json)
        req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if json is not None:
            req_headers["Content-Type"] = "application/json"
        if self.signer is not None:
            req_headers.update(self.signer.rest_headers(method, path, clean, body))
        elif self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        if headers:
            req_headers.update(headers)

        with self._client() as client:
            response = client.request(
                method,
                path,
                params=clean,
                content=body if body else None,
                headers=req_headers,
            )
        return self._parse(response)

    def _parse(self, response: httpx.Response) -> Any:
        payload: Any
        if not response.content:
            payload = None
        else:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
        if response.is_success:
            return payload
        raise error_from_response(response.status_code, payload)

    def search_markets(self, **params: Any) -> Any:
        return self.markets.search(**params)

    def create_order(self, **payload: Any) -> Any:
        return self.orders.create(**payload)

    def iter_ws(self, path: str, params: Mapping[str, Any] | None = None) -> Iterator[Any]:
        """Yield parsed JSON messages from a signed WebSocket path."""
        import websockets.sync.client

        url = self.ws.url(path, params)
        with websockets.sync.client.connect(url) as conn:
            for raw in conn:
                if raw is None:
                    continue
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                try:
                    yield json.loads(raw)
                except json.JSONDecodeError:
                    yield raw



    def close(self) -> None:
        return None

    def __enter__(self) -> "Molecule":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def create_complex_order(self, **payload: Any) -> Any:
        return self.complex_orders.create(**payload)

    def positions(self, subaccount_id: str, **params: Any) -> Any:
        return self.portfolio.positions(subaccount_id, **params)


class AsyncMolecule:
    """Optional async client with the same surface as Molecule."""

    def __init__(
        self,
        base_url: str | None = None,
        key_id: str | None = None,
        private_key: str | bytes | None = None,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._sync = Molecule(
            base_url=base_url,
            key_id=key_id,
            private_key=private_key,
            token=token,
            timeout=timeout,
        )
        self.base_url = self._sync.base_url
        self.signer = self._sync.signer
        self.token = token
        self.timeout = timeout
        self._transport = transport
        self.markets = self._sync.markets
        self.orders = self._sync.orders
        self.complex_orders = self._sync.complex_orders
        self.portfolio = self._sync.portfolio
        self.risk = self._sync.risk
        self.ws = self._sync.ws

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | list[Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        clean = None
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
        body = encode_body(json)
        req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if json is not None:
            req_headers["Content-Type"] = "application/json"
        if self.signer is not None:
            req_headers.update(self.signer.rest_headers(method, path, clean, body))
        elif self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        if headers:
            req_headers.update(headers)
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self._transport,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        ) as client:
            response = await client.request(
                method,
                path,
                params=clean,
                content=body if body else None,
                headers=req_headers,
            )
        return self._sync._parse(response)

    def search_markets(self, **params: Any) -> Any:
        return self._sync.search_markets(**params)

    def create_order(self, **payload: Any) -> Any:
        return self._sync.create_order(**payload)
