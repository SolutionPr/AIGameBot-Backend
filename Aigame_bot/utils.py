from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def now_utc() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def iso_utc_now() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return now_utc().isoformat()


def clean_payload(data: dict[str, Any]) -> dict[str, Any]:
    """
    Remove keys with empty values while keeping valid falsey values like 0 and False.
    """
    return {key: value for key, value in data.items() if value not in (None, "")}


def api_response(message: str, data: Any = None, success: bool = True) -> dict[str, Any]:
    """Standard shape for API-style JSON responses."""
    response = {
        "success": success,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    return response
