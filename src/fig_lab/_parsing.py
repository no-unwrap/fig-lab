"""Shared low-level parsing and coercion utilities.

These helpers are used across readers, figure specs, and other modules that need
to validate and coerce raw JSON payloads into typed Python values.  Centralizing
them here eliminates the duplicate ``string_or_none`` / ``load_json_object`` /
``require_keys`` definitions that previously lived in three separate modules.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_json_object(path: Path) -> dict[str, object]:
    """Read a JSON file and return its top-level object.

    Raises:
        ValueError: If the file does not contain a JSON object.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return {str(key): value for key, value in payload.items()}


def require_keys(
    payload: dict[str, object],
    keys: tuple[str, ...],
    *,
    label: str = "",
) -> None:
    """Validate that *payload* contains every key in *keys*.

    Raises:
        ValueError: Listing the missing keys and optional *label* for context.
    """
    missing = [key for key in keys if key not in payload]
    if missing:
        prefix = f"{label} is missing" if label else "missing"
        raise ValueError(f"{prefix} required keys: {', '.join(sorted(missing))}")


def coerce_object(value: object) -> dict[str, object]:
    """Coerce *value* to a ``dict[str, object]``.

    Raises:
        ValueError: If *value* is not a ``dict``.
    """
    if not isinstance(value, dict):
        raise ValueError("expected object value")
    return {str(key): inner_value for key, inner_value in value.items()}


def coerce_optional_object(value: object) -> dict[str, object]:
    """Coerce *value* to a ``dict[str, object]``, treating ``None`` as empty."""
    if value is None:
        return {}
    return coerce_object(value)


def coerce_list(value: object) -> list[object]:
    """Coerce *value* to a ``list[object]``.

    Raises:
        ValueError: If *value* is not a ``list``.
    """
    if not isinstance(value, list):
        raise ValueError("expected list value")
    return list(value)


def string_or_none(value: object) -> str | None:
    """Return a stripped non-empty ``str``, or ``None``.

    Integer values are coerced to their string representation so that numeric
    JSON fields (``"id": 7``) survive normalization.
    """
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, int):
        return str(value)
    return None
