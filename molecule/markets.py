from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from molecule.client import Molecule


class MarketsAPI:
    def __init__(self, client: Molecule) -> None:
        self._client = client

    def search(
        self,
        q: str | None = None,
        venue: str | None = None,
        status: str | None = None,
        category: str | None = None,
        cursor: str | None = None,
        **params: Any,
    ) -> Any:
        """GET /v1/markets/search."""
        query = {"q": q, "venue": venue, "status": status, "category": category, "cursor": cursor}
        query.update(params)
        return self._client.request("GET", "/v1/markets/search", params=query)

    def match(self, ticker: str | None = None, slug: str | None = None, **params: Any) -> Any:
        """GET /v1/markets/match — ticker= or slug=."""
        query = {"ticker": ticker, "slug": slug}
        query.update(params)
        return self._client.request("GET", "/v1/markets/match", params=query)

    def get(self, instrument_id: int | str) -> Any:
        """GET /v1/markets/{id}."""
        return self._client.request("GET", f"/v1/markets/{instrument_id}")

    def list(self, q: str | None = None, venue: str | None = None, **params: Any) -> Any:
        """GET /v1/markets."""
        query = {"q": q, "venue": venue}
        query.update(params)
        return self._client.request("GET", "/v1/markets", params=query)

    def lookup(self, instrument_ids: list[int] | None = None, **payload: Any) -> Any:
        """POST /v1/markets/lookup."""
        body = dict(payload)
        if instrument_ids is not None:
            body["instrument_ids"] = instrument_ids
        return self._client.request("POST", "/v1/markets/lookup", json=body)

    def book(self, instrument_id: int | str) -> Any:
        """GET /v1/markets/{id}/book."""
        return self._client.request("GET", f"/v1/markets/{instrument_id}/book")

    def trades(self, instrument_id: int | str, limit: int = 100) -> Any:
        """GET /v1/markets/{id}/trades."""
        return self._client.request(
            "GET", f"/v1/markets/{instrument_id}/trades", params={"limit": limit}
        )

    def stats(self, instrument_id: int | str) -> Any:
        """GET /v1/markets/{id}/stats."""
        return self._client.request("GET", f"/v1/markets/{instrument_id}/stats")

    def candles(
        self,
        instrument_id: int | str,
        interval: str = "1h",
        limit: int = 500,
        **params: Any,
    ) -> Any:
        """GET /v1/candles."""
        query = {"instrument_id": instrument_id, "interval": interval, "limit": limit}
        query.update(params)
        return self._client.request("GET", "/v1/candles", params=query)

    def venues(self) -> Any:
        """GET /v1/venues — live: Demo, Polymarket, Kalshi."""
        return self._client.request("GET", "/v1/venues")

    def venue_health(self) -> Any:
        """GET /v1/venues/health."""
        return self._client.request("GET", "/v1/venues/health")

    def orderbook(self, instrument_id: int | str) -> Any:
        """GET /v1/orderbooks/{id}."""
        return self._client.request("GET", f"/v1/orderbooks/{instrument_id}")

    def generic_asset_orderbook(
        self,
        generic_asset_id: int | str,
        subaccount_id: str | None = None,
        **params: Any,
    ) -> Any:
        """GET /v1/orderbooks/generic-asset/{id}."""
        query = {"subaccount_id": subaccount_id}
        query.update(params)
        return self._client.request(
            "GET",
            f"/v1/orderbooks/generic-asset/{generic_asset_id}",
            params=query,
        )

    aggregated_book = generic_asset_orderbook

    def prices(
        self,
        instrument_id: int | str,
        type: str = "ticks",
        limit: int = 100,
        interval: str = "1h",
        **params: Any,
    ) -> Any:
        """GET /v1/prices."""
        query = {
            "instrument_id": instrument_id,
            "type": type,
            "limit": limit,
            "interval": interval,
        }
        query.update(params)
        return self._client.request("GET", "/v1/prices", params=query)

    def prints(self, instrument_id: int | str | None = None, limit: int = 100) -> Any:
        """GET /v1/tradeprints."""
        return self._client.request(
            "GET",
            "/v1/tradeprints",
            params={"instrument_id": instrument_id, "limit": limit},
        )
