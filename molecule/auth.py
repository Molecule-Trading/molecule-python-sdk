"""Local Ed25519 signing. The private key never leaves the caller process.

Matches the Molecule terminal verifier:
canonical REST = METHOD\\nPATH\\nSORTED_QUERY\\nTIMESTAMP\\nhex(sha256(body))
canonical WS   = WS\\nPATH\\nSORTED_QUERY(without signing params)\\nTIMESTAMP
signature      = base64(ed25519(canonical bytes))
"""

from __future__ import annotations

import base64
import hashlib
import time
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from nacl.signing import SigningKey

SIGNING_QUERY_PARAMS = frozenset({"key_id", "ts", "sig", "access_token"})
HEADER_KEY_ID = "X-Molecule-Key-Id"
HEADER_TIMESTAMP = "X-Molecule-Timestamp"
HEADER_SIGNATURE = "X-Molecule-Signature"
REPLAY_WINDOW_MS = 30_000


def load_private_key(private_key: str | bytes) -> SigningKey:
    """Load a 32-byte Ed25519 seed.

    Documented format: base64 of the 32-byte seed (same as key creation).
    Also accepted: raw 32 bytes, hex, or a 64-byte seed||public-key blob.
    """
    if isinstance(private_key, bytes):
        raw = private_key
    else:
        text = private_key.strip()
        raw = b""
        try:
            decoded = base64.b64decode(text, validate=True)
            if len(decoded) in {32, 64}:
                raw = decoded
        except Exception:
            raw = b""
        if len(raw) not in {32, 64}:
            try:
                raw = bytes.fromhex(text)
            except ValueError as exc:
                raise ValueError(
                    "private_key must be a 32-byte Ed25519 seed as base64"
                ) from exc
    if len(raw) == 64:
        raw = raw[:32]
    if len(raw) != 32:
        raise ValueError("Ed25519 seed must be 32 bytes")
    return SigningKey(raw)


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body or b"").hexdigest()


def empty_body_hash() -> str:
    return sha256_hex(b"")


def sorted_query(
    query: Mapping[str, Any] | Sequence[tuple[str, Any]] | str | None,
    *,
    drop: frozenset[str] | None = None,
) -> str:
    if not query:
        return ""
    if isinstance(query, str):
        items = parse_qsl(query, keep_blank_values=True)
    elif isinstance(query, Mapping):
        items = []
        for key, value in query.items():
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                items.extend((str(key), str(item)) for item in value)
            elif isinstance(value, bool):
                items.append((str(key), "true" if value else "false"))
            else:
                items.append((str(key), str(value)))
    else:
        items = [(str(k), str(v)) for k, v in query if v is not None]
    skip = drop or frozenset()
    filtered = [(k, v) for k, v in items if k not in skip]
    filtered.sort(key=lambda kv: (kv[0], kv[1]))
    return urlencode(filtered, doseq=True)


def canonical_string(
    method: str,
    path: str,
    query: Mapping[str, Any] | Sequence[tuple[str, Any]] | str | None,
    timestamp: str,
    body: bytes,
) -> bytes:
    digest = sha256_hex(body or b"")
    q = sorted_query(query)
    return f"{method.upper()}\n{path}\n{q}\n{timestamp}\n{digest}".encode()


def canonical_ws(
    path: str,
    query: Mapping[str, Any] | str | None,
    timestamp: str,
) -> bytes:
    q = sorted_query(query, drop=SIGNING_QUERY_PARAMS)
    return f"WS\n{path}\n{q}\n{timestamp}".encode()


def sign_message(signing_key: SigningKey, message: bytes) -> str:
    return base64.b64encode(signing_key.sign(message).signature).decode()


def normalize_timestamp(timestamp: int | str | None) -> str:
    """Unix milliseconds preferred; integer seconds are accepted and converted."""
    if timestamp is None:
        return str(int(time.time() * 1000))
    if isinstance(timestamp, str):
        if not timestamp.isdigit():
            raise ValueError("timestamp must be unix seconds or milliseconds")
        value = int(timestamp)
    else:
        value = int(timestamp)
    if value < 1_000_000_000_000:
        value *= 1000
    return str(value)


class Signer:
    def __init__(self, key_id: str, private_key: str | bytes) -> None:
        self.key_id = key_id
        self._key = load_private_key(private_key)

    def rest_headers(
        self,
        method: str,
        path: str,
        query: Mapping[str, Any] | None,
        body: bytes,
        timestamp: int | str | None = None,
    ) -> dict[str, str]:
        ts = normalize_timestamp(timestamp)
        signature = sign_message(self._key, canonical_string(method, path, query, ts, body))
        return {
            HEADER_KEY_ID: self.key_id,
            HEADER_TIMESTAMP: ts,
            HEADER_SIGNATURE: signature,
        }

    def ws_query(
        self,
        path: str,
        query: Mapping[str, Any] | None = None,
        timestamp: int | str | None = None,
    ) -> dict[str, str]:
        ts = normalize_timestamp(timestamp)
        params = {str(k): v for k, v in dict(query or {}).items() if v is not None}
        signature = sign_message(self._key, canonical_ws(path, params, ts))
        params["key_id"] = self.key_id
        params["ts"] = ts
        params["sig"] = signature
        return {k: str(v) for k, v in params.items()}


def apply_ws_query(url: str, signed_query: Mapping[str, str]) -> str:
    parts = urlsplit(url)
    existing = dict(parse_qsl(parts.query, keep_blank_values=True))
    existing.update(signed_query)
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(existing), parts.fragment)
    )


canonical_rest_string = canonical_string
sorted_query_string = sorted_query
