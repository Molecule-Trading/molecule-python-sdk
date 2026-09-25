from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

from molecule.auth import apply_ws_query

if TYPE_CHECKING:
    from molecule.client import Molecule

WS_PATHS = {
    "orders": "/v1/ws/orders",
    "fills": "/v1/ws/fills",
    "positions": "/v1/ws/positions",
    "balances": "/v1/ws/balances",
    "orderbooks": "/v1/ws/orderbooks",
    "tradeprints": "/v1/ws/tradeprints",
}


def http_to_ws(base_url: str) -> str:
    parts = urlsplit(base_url)
    scheme = "wss" if parts.scheme in {"https", "wss"} else "ws"
    if parts.scheme in {"ws", "wss"}:
        scheme = parts.scheme
    return urlunsplit((scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


class WebSocketAPI:
    def __init__(self, client: Molecule) -> None:
        self._client = client

    def url(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        if not path.startswith("/"):
            if path.startswith("generic-asset/"):
                path = f"/v1/ws/orderbooks/{path}"
            else:
                path = WS_PATHS.get(path, f"/v1/ws/{path}")
        root = http_to_ws(self._client.base_url)
        url = urljoin(root + "/", path.lstrip("/"))
        query = dict(params or {})
        if self._client.signer is not None:
            signed = self._client.signer.ws_query(path, query)
            return apply_ws_query(url, signed)
        if query:
            parts = urlsplit(url)
            query_str = urlencode(query, doseq=True)
            return urlunsplit((parts.scheme, parts.netloc, parts.path, query_str, ""))
        return url

    def orders(self, params: Mapping[str, Any] | None = None) -> str:
        return self.url("/v1/ws/orders", params)

    def fills(self, params: Mapping[str, Any] | None = None) -> str:
        return self.url("/v1/ws/fills", params)

    def positions(self, params: Mapping[str, Any] | None = None) -> str:
        return self.url("/v1/ws/positions", params)

    def balances(self, params: Mapping[str, Any] | None = None) -> str:
        return self.url("/v1/ws/balances", params)

    def orderbooks(self, params: Mapping[str, Any] | None = None) -> str:
        return self.url("/v1/ws/orderbooks", params)

    def generic_asset_orderbook(
        self,
        generic_asset_id: int | str,
        params: Mapping[str, Any] | None = None,
    ) -> str:
        return self.url(f"/v1/ws/orderbooks/generic-asset/{generic_asset_id}", params)

    def tradeprints(self, params: Mapping[str, Any] | None = None) -> str:
        return self.url("/v1/ws/tradeprints", params)

    def iter(self, path: str, params: Mapping[str, Any] | None = None) -> Iterator[Any]:
        return self._client.iter_ws(path, params)
