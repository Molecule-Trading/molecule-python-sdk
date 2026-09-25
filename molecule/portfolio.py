from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from molecule.client import Molecule


class PortfolioAPI:
    def __init__(self, client: Molecule) -> None:
        self._client = client

    def fills(self, subaccount_id: str | None = None, **params: Any) -> Any:
        """GET /v1/fills."""
        query = {"subaccount_id": subaccount_id}
        query.update(params)
        return self._client.request("GET", "/v1/fills", params=query)

    def positions(self, subaccount_id: str, **params: Any) -> Any:
        """GET /v1/positions."""
        query = {"subaccount_id": subaccount_id}
        query.update(params)
        return self._client.request("GET", "/v1/positions", params=query)

    def balances(self, subaccount_id: str, **params: Any) -> Any:
        """GET /v1/balances."""
        query = {"subaccount_id": subaccount_id}
        query.update(params)
        return self._client.request("GET", "/v1/balances", params=query)

    def pnl(self, subaccount_id: str, **params: Any) -> Any:
        """GET /v1/pnl."""
        query = {"subaccount_id": subaccount_id}
        query.update(params)
        return self._client.request("GET", "/v1/pnl", params=query)

    def pnl_history(self, subaccount_id: str, limit: int = 200, **params: Any) -> Any:
        """GET /v1/pnl/history."""
        query = {"subaccount_id": subaccount_id, "limit": limit}
        query.update(params)
        return self._client.request("GET", "/v1/pnl/history", params=query)

    def set_fair_values(self, subaccount_id: str, values: list[dict[str, Any]]) -> Any:
        """PUT /v1/fair-values."""
        return self._client.request(
            "PUT",
            "/v1/fair-values",
            json={"subaccount_id": subaccount_id, "values": values},
        )

    def lookup_fees(self, instrument_ids: list[int], **payload: Any) -> Any:
        """POST /v1/fees/lookup."""
        body = {"instrument_ids": instrument_ids}
        body.update(payload)
        return self._client.request("POST", "/v1/fees/lookup", json=body)

    def fees(self, venue: str | None = None) -> Any:
        """GET /v1/fees."""
        return self._client.request("GET", "/v1/fees", params={"venue": venue})


class RiskAPI:
    def __init__(self, client: Molecule) -> None:
        self._client = client

    def state(self, subaccount_id: str) -> Any:
        """GET /v1/risk."""
        return self._client.request("GET", "/v1/risk", params={"subaccount_id": subaccount_id})

    def limits(self, subaccount_id: str | None = None) -> Any:
        """GET /v1/risk/limits."""
        return self._client.request("GET", "/v1/risk/limits", params={"subaccount_id": subaccount_id})

    def set_limits(self, **payload: Any) -> Any:
        """PUT /v1/risk/limits."""
        return self._client.request("PUT", "/v1/risk/limits", json=payload)

    def kill_switch(self, enabled: bool) -> Any:
        """POST /v1/risk/kill-switch."""
        return self._client.request("POST", "/v1/risk/kill-switch", json={"enabled": enabled})

    def cancel_all(self, subaccount_id: str) -> Any:
        """POST /v1/risk/cancel-all."""
        return self._client.request(
            "POST", "/v1/risk/cancel-all", params={"subaccount_id": subaccount_id}
        )
