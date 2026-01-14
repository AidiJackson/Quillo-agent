"""
UORIN Self-Explanation v1
Backend module for transparency detection and trust signal generation.

This module provides:
1. Transparency query detection (pattern matching)
2. Transparency card generation (structured disclosure)
3. Micro-disclosure formatting

NO LLM calls are made in this module.
"""

from typing import Dict, List, Optional


# Transparency query patterns - lowercase substrings to match
TRANSPARENCY_QUERY_PATTERNS = [
    "what do you remember",
    "what are you using",
    "why are you saying",
    "are you assuming",
    "is this up to date",
    "did you store",
    "what did you use",
    "what context",
]


def is_transparency_query(text: str) -> bool:
    """
    Detect if user text is a transparency query.

    Args:
        text: User input text

    Returns:
        True if text matches any transparency pattern
    """
    if not text:
        return False

    text_lower = text.lower()
    return any(pattern in text_lower for pattern in TRANSPARENCY_QUERY_PATTERNS)


def build_transparency_card(state: dict) -> str:
    """
    Build a transparency card showing what context is being used.

    Args:
        state: Dictionary with keys:
            - using_conversation_context: bool
            - using_session_context: bool
            - using_profile: bool
            - using_evidence: bool
            - stress_test_mode: bool
            - facts_used: list of dicts with 'text', 'source', 'timestamp' (optional)
            - not_assuming: list of strings
            - needs_from_user: list of strings

    Returns:
        Formatted transparency card as string
    """
    # Using right now section
    conversation_icon = "✅" if state.get("using_conversation_context", False) else "❌"
    session_icon = "✅" if state.get("using_session_context", False) else "❌"
    profile_icon = "✅" if state.get("using_profile", False) else "❌"
    evidence_icon = "✅" if state.get("using_evidence", False) else "❌"
    stress_icon = "✅" if state.get("stress_test_mode", False) else "❌"

    card = f"""Transparency
- Using right now:
  - Conversation context: {conversation_icon}
  - Session context (24h): {session_icon}
  - Judgment Profile: {profile_icon}
  - Live Evidence: {evidence_icon}
  - Stress Test mode: {stress_icon}

- What I'm treating as facts:
"""

    # Facts section
    facts_used = state.get("facts_used", [])
    if facts_used:
        for fact in facts_used:
            fact_text = fact.get("text", "")
            source = fact.get("source", "")
            timestamp = fact.get("timestamp", "")

            bullet = f"  - {fact_text}"
            if source:
                bullet += f" (source: {source}"
                if timestamp:
                    bullet += f", {timestamp}"
                bullet += ")"
            card += bullet + "\n"
    else:
        card += "  - No external facts fetched.\n"

    # Not assuming section
    card += "\n- What I'm not assuming:\n"
    not_assuming = state.get("not_assuming", [])
    if not_assuming:
        for item in not_assuming:
            card += f"  - {item}\n"
    else:
        card += "  - None\n"

    # Needs from user section
    card += "\n- What I need from you (if anything):\n"
    needs = state.get("needs_from_user", [])
    if needs:
        for need in needs:
            card += f"  - {need}\n"
    else:
        card += "  - Nothing needed\n"

    # Control section
    card += """
Control:
- Say "clear context" to reset this conversation.
- Say "view profile" to inspect saved preferences."""

    return card


def build_micro_disclosures(
    using_evidence: bool = False,
    stress_test_mode: bool = False,
    using_conversation_context: bool = False,
    using_profile: bool = False
) -> str:
    """
    Build micro-disclosure lines to prepend to response.

    Args:
        using_evidence: True if evidence was fetched and used
        stress_test_mode: True if stress test mode is active
        using_conversation_context: True if conversation history is used
        using_profile: True if user profile/preferences are used

    Returns:
        String with disclosure lines (empty string if no disclosures)
    """
    disclosures = []

    if using_evidence:
        disclosures.append("Evidence: on (sources + timestamps below)")

    if stress_test_mode:
        disclosures.append("Mode: Stress Test (consequential decision detected)")

    if using_conversation_context:
        disclosures.append("Context: using this conversation's history")

    if using_profile:
        disclosures.append("Profile: using your saved preferences (view/edit anytime)")

    if not disclosures:
        return ""

    # Join disclosures with newlines and add blank line separator
    return "\n".join(disclosures) + "\n\n"
