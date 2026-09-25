# molecule

Official Python SDK for the Molecule prediction-market execution API.

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
    private_key=os.environ["MOLECULE_PRIVATE_KEY"],  # stays in this process
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

Live venues: Demo, Polymarket, Kalshi.

## Environment

| Variable | Purpose |
| --- | --- |
| `MOLECULE_BASE_URL` | API base if `base_url` is omitted |
| `MOLECULE_KEY_ID` | Trading key id (example only; pass explicitly if you prefer) |
| `MOLECULE_PRIVATE_KEY` | Base64 32-byte Ed25519 seed |

`base_url` is required at init via the constructor or `MOLECULE_BASE_URL`.

## Docs

Product docs: `/docs` on the product site.
