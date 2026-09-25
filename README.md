# molecule

Official Python SDK for the Molecule prediction-market execution API.

Source: https://github.com/Molecule-Trading/molecule-python-sdk
Docs: https://molelcule.mintlify.site/
Site: https://molecule-neon.vercel.app

```bash
pip install molecule
```

Until PyPI publish:

```bash
pip install "molecule @ git+https://github.com/Molecule-Trading/molecule-python-sdk.git"
```

## Auth

Trading calls use a key id plus an Ed25519 private key. The private key never leaves this process. The server stores the public key only.

Documented private-key format: base64 of the 32-byte Ed25519 seed. Hex and raw bytes are also accepted.

Human / org / key-management routes use a JWT (`token=`). A trading key on a management route returns `403 human_session_required`. The two modes are not interchangeable.

## Example

```python
import os
from molecule import Molecule

client = Molecule(
    base_url=os.environ["MOLECULE_BASE_URL"],
    key_id=os.environ["MOLECULE_KEY_ID"],
    private_key=os.environ["MOLECULE_PRIVATE_KEY"],
)

found = client.search_markets(q="house", venue="Demo")
demo = client.markets.match(ticker="FAKE-HOUSE-DEM")
book = client.markets.book(demo["instrument_id"])

order = client.create_order(
    subaccount_id=os.environ["MOLECULE_SUBACCOUNT_ID"],
    instrument_id=demo["instrument_id"],
    side="BUY",
    type="LIMIT",
    tif="GTC",
    price="0.48",
    qty="10",
    routing={"mode": "DIRECT"},
    client_order_id="desk-house-1",
)
print(order["id"], order["status"])
```

Live venues: Demo, Polymarket, Kalshi. Polymarket US and Crypto.com are unreleased.

`search_markets` and `create_order` are flat aliases of `markets.search` and `orders.create`. `iter_ws` is a synchronous iterator. Complex orders use `kind` (`ICEBERG`, `PEG`, `STOP`, `TP_SL`, `SMART_ROUTE`).

## Environment

| Variable | Purpose |
| --- | --- |
| `MOLECULE_BASE_URL` | API base if `base_url` is omitted |
| `MOLECULE_KEY_ID` | Trading key id. Pass it to the constructor. The client does not read this on its own. |
| `MOLECULE_PRIVATE_KEY` | Base64 32-byte Ed25519 seed. Pass it to the constructor. The client does not read this on its own. |

`base_url` is required at init via the constructor or `MOLECULE_BASE_URL`.

## Docs

https://molelcule.mintlify.site/
