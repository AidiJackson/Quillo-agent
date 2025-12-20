"""
Agent Suggestion Service (v1)

Proactively suggests bringing in additional agents when it improves judgment.
User must explicitly consent - Quillo never auto-adds agents.

Rules:
- Suggest when: high stakes, complex decisions, ambiguity
- No suggestion for: grammar, simple rewrites, factual lookups
- Natural, calm, professional tone
- No chain-of-thought or internal scoring
- RAW_CHAT_MODE disables all automatic suggestions
"""
import random
from loguru import logger

from ..config import settings


def should_suggest_agents(
    stakes: str,
    intent: str,
    ambiguity: bool = False,
    topic: str = ""
) -> bool:
    """
    Determine if Quillo should suggest bringing in additional agents.

    Uses simple heuristics (no ML):
    - Suggest for high stakes
    - Suggest for complex decision-making intents
    - Suggest when there's ambiguity
    - Do NOT suggest for simple tasks

    Args:
        stakes: Stakes level ("low", "medium", "high")
        intent: Action intent type
        ambiguity: Whether the request has ambiguity
        topic: Topic/context of the request

    Returns:
        True if agents should be suggested, False otherwise
    """
    # In raw chat mode, never suggest agents automatically
    if settings.raw_chat_mode:
        logger.debug("No agent suggestion: RAW_CHAT_MODE enabled")
        return False

    # Never suggest for simple tasks
    simple_intents = {"grammar", "rewrite", "typo", "lookup", "factual"}
    if intent.lower() in simple_intents:
        logger.debug(f"No agent suggestion: simple intent '{intent}'")
        return False

    # Check for simple topic keywords that don't need multiple perspectives
    topic_lower = topic.lower()
    simple_topics = ["grammar", "spelling", "typo", "define", "what is"]
    if any(simple_topic in topic_lower for simple_topic in simple_topics):
        logger.debug(f"No agent suggestion: simple topic detected")
        return False

    # Suggest for high stakes
    if stakes == "high":
        logger.debug("Agent suggestion: high stakes detected")
        return True

    # Suggest for complex decision-making intents
    complex_intents = {
        "decision", "negotiate", "negotiation", "strategy",
        "plan", "execute", "external_integration"
    }
    if intent.lower() in complex_intents:
        logger.debug(f"Agent suggestion: complex intent '{intent}'")
        return True

    # Suggest when there's ambiguity
    if ambiguity:
        logger.debug("Agent suggestion: ambiguity detected")
        return True

    # Default: no suggestion
    logger.debug("No agent suggestion: criteria not met")
    return False


def build_agent_suggestion_message(topic: str = "") -> str:
    """
    Build a natural, calm suggestion message for bringing in agents.

    Picks from a fixed set of professional suggestions.
    No agent names mentioned - keeps it abstract.

    Args:
        topic: Optional topic/context for personalization

    Returns:
        Suggestion message string
    """
    # Fixed set of natural suggestions
    suggestions = [
        "This one has a few angles. Want a second opinion?",
        "If you want, I can bring in another perspective to pressure-test this.",
        "Would it help to get a challenger view on this?",
        "I can bring in a couple other perspectives if that'd be useful.",
        "Want me to pull in some contrasting views on this?",
    ]

    # Pick one randomly for variety
    message = random.choice(suggestions)

    logger.debug(f"Built agent suggestion: {message}")
    return message


def detect_ambiguity(text: str, intent: str) -> bool:
    """
    Detect if a user request has ambiguity that would benefit from multiple perspectives.

    Simple heuristics:
    - Multiple questions in one request
    - Uncertainty markers ("not sure", "maybe", "might")
    - Conflicting requirements ("but", "however", "although")

    Args:
        text: User's input text
        intent: Detected intent

    Returns:
        True if ambiguity detected, False otherwise
    """
    text_lower = text.lower()

    # Multiple questions
    if text.count("?") > 1:
        return True

    # Uncertainty markers
    uncertainty_markers = [
        "not sure", "unsure", "maybe", "might", "could be",
        "don't know", "uncertain", "confused", "unclear"
    ]
    if any(marker in text_lower for marker in uncertainty_markers):
        return True

    # Conflicting requirements
    conflict_markers = ["but", "however", "although", "though", "yet"]
    if any(marker in text_lower for marker in conflict_markers):
        return True

    # Complex decisions (multiple options)
    if "or" in text_lower and text.count("or") >= 2:
        return True

    return False
