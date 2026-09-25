"""Shared types and literals for the Molecule execution API.

Live venues: Demo, Polymarket, Kalshi.
Unreleased (do not send live orders): Polymarket US, Crypto.com.
"""

from __future__ import annotations

from typing import Any, Literal, Mapping, MutableMapping, Sequence, TypedDict

JSONDict = dict[str, Any]
JSONMapping = Mapping[str, Any]
MutableJSON = MutableMapping[str, Any]

# Live venues exposed by the public client.
VenueName = Literal["Demo", "Polymarket", "Kalshi"]
LIVE_VENUES: tuple[str, ...] = ("Demo", "Polymarket", "Kalshi")
UNRELEASED_VENUES: tuple[str, ...] = ("Polymarket US", "Crypto.com")

Side = Literal["BUY", "SELL"]
Outcome = Literal["YES", "NO"]
OrderType = Literal["LIMIT", "MARKET"]
TimeInForce = Literal["GTC", "IOC", "FOK", "GTD"]
RoutingMode = Literal["DIRECT", "BEST_PRICE", "SPLIT"]
ComplexOrderType = Literal["ICEBERG", "PEG", "STOP", "TP_SL", "SMART_ROUTE"]
OrderStatus = Literal[
    "PENDING_SUBMISSION",
    "OPEN",
    "PARTIAL",
    "FILLED",
    "CANCELLED",
    "REJECTED",
    "EXPIRED",
]


class Routing(TypedDict, total=False):
    """Router never invents size.

    DIRECT uses instrument_id; BEST_PRICE and SPLIT use generic_asset_id.
    """

    mode: RoutingMode


class OrderRequest(TypedDict, total=False):
    subaccount_id: str
    instrument_id: int
    generic_asset_id: int
    side: Side
    outcome: Outcome
    type: OrderType
    tif: TimeInForce
    price: str
    qty: str
    routing: Routing
    client_order_id: str


class ComplexOrderRequest(TypedDict, total=False):
    subaccount_id: str
    instrument_id: int
    generic_asset_id: int
    type: ComplexOrderType
    side: Side
    outcome: Outcome
    qty: str
    price: str
    params: JSONDict
    routing: Routing
    idempotency_key: str


Params = Mapping[str, Any] | None
Headers = Mapping[str, str] | None
Body = Mapping[str, Any] | Sequence[Any] | None
