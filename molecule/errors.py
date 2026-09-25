from __future__ import annotations

from typing import Any


class MoleculeError(Exception):
    """Base SDK error."""

    def __init__(
        self,
        message: str,
        *,
        error: str | None = None,
        status_code: int | None = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error = error
        self.status_code = status_code
        self.details = details

    def __str__(self) -> str:
        code = f"{self.status_code} " if self.status_code is not None else ""
        kind = f"{self.error}: " if self.error else ""
        return f"{code}{kind}{self.message}"


class UnauthorizedError(MoleculeError):
    """401 unauthorized / signature / replay / stale_timestamp."""


class ForbiddenError(MoleculeError):
    """403 forbidden / human_session_required / kill_switch."""


class NotFoundError(MoleculeError):
    """404 not_found."""


class ConflictError(MoleculeError):
    """409 conflict / idempotency_conflict."""


class ValidationError(MoleculeError):
    """422 validation."""


class RateLimitedError(MoleculeError):
    """429 rate_limited."""


class RoutingUnavailableError(MoleculeError):
    """400 ROUTING_UNAVAILABLE."""


class BadRequestError(MoleculeError):
    """Other 400-class errors."""


class APIError(MoleculeError):
    """Unexpected HTTP or payload error."""


_ERROR_MAP: dict[str, type[MoleculeError]] = {
    "unauthorized": UnauthorizedError,
    "signature": UnauthorizedError,
    "replay": UnauthorizedError,
    "stale_timestamp": UnauthorizedError,
    "forbidden": ForbiddenError,
    "human_session_required": ForbiddenError,
    "kill_switch": ForbiddenError,
    "not_found": NotFoundError,
    "conflict": ConflictError,
    "idempotency_conflict": ConflictError,
    "validation": ValidationError,
    "rate_limited": RateLimitedError,
    "ROUTING_UNAVAILABLE": RoutingUnavailableError,
    "routing_unavailable": RoutingUnavailableError,
}


def error_from_response(status_code: int, payload: Any) -> MoleculeError:
    error = None
    message = f"HTTP {status_code}"
    details = None
    if isinstance(payload, dict):
        error = payload.get("error")
        message = str(payload.get("message") or error or message)
        details = payload.get("details")
    elif payload:
        message = str(payload)

    cls: type[MoleculeError]
    if isinstance(error, str) and error in _ERROR_MAP:
        cls = _ERROR_MAP[error]
    elif status_code == 401:
        cls = UnauthorizedError
    elif status_code == 403:
        cls = ForbiddenError
    elif status_code == 404:
        cls = NotFoundError
    elif status_code == 409:
        cls = ConflictError
    elif status_code == 422:
        cls = ValidationError
    elif status_code == 429:
        cls = RateLimitedError
    elif status_code == 400 and error in {"ROUTING_UNAVAILABLE", "routing_unavailable"}:
        cls = RoutingUnavailableError
    elif status_code == 400:
        cls = BadRequestError
    else:
        cls = APIError
    return cls(message, error=error, status_code=status_code, details=details)
