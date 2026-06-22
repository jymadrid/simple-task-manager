"""Small value-normalization helpers used across TaskForge."""

from typing import Any


def enum_value(value: Any) -> str:
    """Return a stable string value for enum-like or plain-string fields."""
    return str(getattr(value, "value", value))


def enum_matches(value: Any, *candidates: Any) -> bool:
    """Compare enum-like values by their serialized string value."""
    current_value = enum_value(value)
    return any(current_value == enum_value(candidate) for candidate in candidates)


def enum_title(value: Any) -> str:
    """Return a human-readable title for enum-like values."""
    return enum_value(value).replace("_", " ").title()
