from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from molecule.client import Molecule


def _idempotency_headers(key: str | None) -> dict[str, str] | None:
    if not key:
        return None
    return {"Idempotency-Key": key}


class OrdersAPI:
    def __init__(self, client: Molecule) -> None:
        self._client = client

    def create(self, **payload: Any) -> Any:
        """POST /v1/orders. Simple-order idempotency key is client_order_id."""
        key = payload.get("client_order_id") or payload.get("idempotency_key")
        return self._client.request(
            "POST",
            "/v1/orders",
            json=payload,
            headers=_idempotency_headers(str(key) if key else None),
        )

    def batch(self, orders: list[dict[str, Any]] | None = None, **payload: Any) -> Any:
        """POST /v1/orders/batch."""
        data: Any = orders if orders is not None else payload
        return self._client.request("POST", "/v1/orders/batch", json=data)

    def get(self, order_id: int | str) -> Any:
        """GET /v1/orders/{id}."""
        return self._client.request("GET", f"/v1/orders/{order_id}")

    def list(self, subaccount_id: str, status: str | None = None, **params: Any) -> Any:
        """GET /v1/orders."""
        query = {"subaccount_id": subaccount_id, "status": status}
        query.update(params)
        return self._client.request("GET", "/v1/orders", params=query)

    def amend(self, order_id: int | str, **payload: Any) -> Any:
        """PATCH /v1/orders/{id}."""
        return self._client.request("PATCH", f"/v1/orders/{order_id}", json=payload or None)

    def cancel(self, order_id: int | str) -> Any:
        """DELETE /v1/orders/{id}."""
        return self._client.request("DELETE", f"/v1/orders/{order_id}")

    def cancel_all(self, subaccount_id: str | None = None, **payload: Any) -> Any:
        """POST /v1/orders/cancel-all."""
        data = dict(payload)
        if subaccount_id is not None:
            data["subaccount_id"] = subaccount_id
        return self._client.request("POST", "/v1/orders/cancel-all", json=data or None)

    def fills(self, subaccount_id: str, **params: Any) -> Any:
        """GET /v1/fills."""
        query = {"subaccount_id": subaccount_id}
        query.update(params)
        return self._client.request("GET", "/v1/fills", params=query)


class ComplexOrdersAPI:
    def __init__(self, client: Molecule) -> None:
        self._client = client

    def create(self, **payload: Any) -> Any:
        """POST /v1/complex-orders.

        Parents: ICEBERG, PEG, STOP, TP_SL, SMART_ROUTE.
        Cancel parent cancels children. Idempotency key is idempotency_key.
        """
        key = payload.get("idempotency_key")
        return self._client.request(
            "POST",
            "/v1/complex-orders",
            json=payload,
            headers=_idempotency_headers(str(key) if key else None),
        )

    def get(self, order_id: int | str) -> Any:
        """GET /v1/complex-orders/{id}."""
        return self._client.request("GET", f"/v1/complex-orders/{order_id}")

    def list(self, subaccount_id: str, **params: Any) -> Any:
        """GET /v1/complex-orders."""
        query = {"subaccount_id": subaccount_id}
        query.update(params)
        return self._client.request("GET", "/v1/complex-orders", params=query)

    def cancel(self, order_id: int | str) -> Any:
        """DELETE /v1/complex-orders/{id}."""
        return self._client.request("DELETE", f"/v1/complex-orders/{order_id}")

    def cancel_all(self, subaccount_id: str) -> Any:
        """POST /v1/complex-orders/cancel-all."""
        return self._client.request(
            "POST",
            "/v1/complex-orders/cancel-all",
            json={"subaccount_id": subaccount_id},
        )
