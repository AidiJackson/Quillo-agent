"""
Utilities for building rationale and explanations
"""
from typing import List


def build_rationale(steps: List[str]) -> str:
    """
    Build a numbered rationale list from steps.

    Args:
        steps: List of rationale strings

    Returns:
        Numbered markdown list as a single string
    """
    if not steps:
        return ""

    return "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))


def merge_reasons(reasons: List[str]) -> str:
    """
    Merge multiple reasons into a single explanatory string.

    Args:
        reasons: List of reason strings

    Returns:
        Comma-separated string of reasons
    """
    if not reasons:
        return "No specific reasons detected"

    return ", ".join(reasons)
