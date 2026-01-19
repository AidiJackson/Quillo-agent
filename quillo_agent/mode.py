"""
Uorin Mode Toggle v1

Single source of truth for Work vs Normal mode definitions.
"""

from typing import Optional

# Mode constants
UORIN_MODE_WORK = "work"
UORIN_MODE_NORMAL = "normal"

# Valid modes
VALID_MODES = {UORIN_MODE_WORK, UORIN_MODE_NORMAL}

# Default mode
DEFAULT_MODE = UORIN_MODE_WORK


def normalize_mode(value: Optional[str]) -> str:
    """
    Normalize mode value to a valid mode constant.

    Args:
        value: Raw mode value (can be None, empty, or any string)

    Returns:
        Normalized mode: "work" or "normal"

    Behavior:
        - None => "work" (default)
        - "" => "work" (default)
        - "work" (case-insensitive) => "work"
        - "normal" (case-insensitive) => "normal"
        - Anything else => "work" (fail-safe)
    """
    if value is None:
        return DEFAULT_MODE

    normalized = value.strip().lower()

    if not normalized:
        return DEFAULT_MODE

    if normalized in VALID_MODES:
        return normalized

    # Fail-safe: unknown values default to work mode
    return DEFAULT_MODE


def is_work_mode(mode: Optional[str]) -> bool:
    """Check if mode is work mode (including None/default)."""
    return normalize_mode(mode) == UORIN_MODE_WORK


def is_normal_mode(mode: Optional[str]) -> bool:
    """Check if mode is normal mode."""
    return normalize_mode(mode) == UORIN_MODE_NORMAL


def get_mode_description(mode: str) -> str:
    """Get human-readable description of a mode."""
    if mode == UORIN_MODE_WORK:
        return "Guardrails + evidence triggers + stress test"
    elif mode == UORIN_MODE_NORMAL:
        return "Free-form; no auto guardrails"
    else:
        return "Unknown mode"
