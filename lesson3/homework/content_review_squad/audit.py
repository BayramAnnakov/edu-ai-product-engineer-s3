"""Audit utilities."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_timestamp() -> str:
    """Return an ISO8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
