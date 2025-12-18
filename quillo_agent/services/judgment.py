"""
Judgment Explanation Layer

Provides conversational, confident narration of intent, risk, and actions
without exposing internal chain-of-thought.
"""
from typing import Literal, Optional, Dict, Any
from loguru import logger
import re


StakeLevel = Literal["low", "medium", "high"]


def assess_stakes(text: str) -> StakeLevel:
    """
    Assess the stakes level of user input based on content and context.

    High stakes: conflict, money, legal, emotional situations
    Medium stakes: professional decisions, business communications
    Low stakes: simple tasks, informational queries

    Args:
        text: User input text to assess

    Returns:
        Stake level: "low", "medium", or "high"
    """
    text_lower = text.lower()
    text_length = len(text)

    # High-stakes keywords and phrases
    high_stakes_keywords = [
        "fire", "firing", "fired", "let go", "letting go",
        "terminate", "termination", "layoff",
        "lawsuit", "legal", "lawyer", "attorney", "sue", "court",
        "negotiate", "negotiation", "deal", "contract",
        "urgent", "emergency", "critical", "crisis",
        "conflict", "fight", "dispute", "argument",
        "complaint", "escalate", "escalation",
        "risk", "risky", "danger", "threat",
        "concerned", "worried", "anxious", "stressed",
        "vote", "decision", "choice", "consequence",
        "money", "payment", "salary", "compensation", "refund",
        "angry", "frustrated", "upset", "disappointed",
        "difficult conversation"
    ]

    # Medium-stakes keywords
    medium_stakes_keywords = [
        "professional", "business", "client", "customer",
        "meeting", "presentation", "proposal", "pitch",
        "email", "message", "communication", "response",
        "feedback", "review", "performance", "evaluation",
        "project", "deadline", "timeline", "schedule",
        "team", "colleague", "manager", "supervisor"
    ]

    # Check for questions first (typically low stakes unless combined with high stakes)
    question_markers = ["?", "how do i", "what is", "can you", "could you", "help me"]
    is_question = any(marker in text_lower for marker in question_markers)

    # Simple informational questions should be low stakes
    simple_question_markers = [
        "what is the best way",
        "how do i",
        "what's the best",
        "how should i structure",
        "please explain"
    ]
    is_simple_question = any(marker in text_lower for marker in simple_question_markers) and text_length < 100

    if is_simple_question:
        logger.debug("Low stakes: simple informational question")
        return "low"

    # Check for high stakes
    high_matches = sum(1 for keyword in high_stakes_keywords if keyword in text_lower)
    if high_matches >= 2:
        logger.debug(f"High stakes: {high_matches} high-stakes keywords found")
        return "high"

    # Single high-stakes keyword with context (not just a question)
    if high_matches >= 1 and not is_question:
        logger.debug(f"High stakes: high-stakes keyword found in action context")
        return "high"

    # Long emotional text (>500 chars) with any high-stakes keyword
    if text_length > 500 and high_matches >= 1:
        logger.debug(f"High stakes: long text ({text_length} chars) with emotional content")
        return "high"

    # Check for medium stakes (but not for simple questions)
    medium_matches = sum(1 for keyword in medium_stakes_keywords if keyword in text_lower)
    if not is_simple_question and (medium_matches >= 2 or (text_length > 200 and medium_matches >= 1)):
        logger.debug(f"Medium stakes: {medium_matches} medium-stakes keywords found")
        return "medium"

    # Simple rewrites, questions, informational queries
    simple_markers = [
        "rewrite", "rephrase", "edit", "fix typo",
        "what", "when", "where", "who", "why", "how",
        "explain", "clarify", "define"
    ]
    is_simple = any(marker in text_lower for marker in simple_markers) and text_length < 200

    if is_simple or (is_question and text_length < 150):
        logger.debug("Low stakes: simple task or short question")
        return "low"

    # Default to low stakes for unclear cases
    logger.debug("Low stakes: default classification")
    return "low"


def build_explanation(
    context: str,
    stakes: StakeLevel,
    recommendation: str,
    intent: Optional[str] = None,
    requires_confirmation: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Build a human-readable explanation of what Quillo sees and recommends.

    Uses conversational, confident tone appropriate for the stakes level.
    Never exposes internal chain-of-thought or technical reasoning.

    Args:
        context: What Quillo observes in the user's input
        stakes: The stakes level (low/medium/high)
        recommendation: What Quillo recommends doing
        intent: Optional detected intent for context
        requires_confirmation: Optional override for confirmation requirement
                             (defaults based on stakes if not provided)

    Returns:
        Dictionary with:
        - what_i_see: grounded observation
        - why_it_matters: context/reasoning (only for medium/high stakes)
        - recommendation: clear action proposal
        - requires_confirmation: whether user approval is needed
    """
    # Build the observation
    what_i_see = _craft_observation(context, intent, stakes)

    # Include "why it matters" for medium/high stakes
    why_it_matters = None
    if stakes in ["medium", "high"]:
        why_it_matters = _craft_reasoning(context, stakes)

    # Build the recommendation
    recommendation_text = _craft_recommendation(recommendation, stakes)

    # Determine if confirmation is required
    if requires_confirmation is None:
        requires_confirmation = stakes in ["medium", "high"]

    result = {
        "what_i_see": what_i_see,
        "why_it_matters": why_it_matters,
        "recommendation": recommendation_text,
        "requires_confirmation": requires_confirmation
    }

    logger.debug(f"Built explanation for {stakes} stakes (confirmation={requires_confirmation})")
    return result


def _craft_observation(context: str, intent: Optional[str], stakes: StakeLevel) -> str:
    """Craft a grounded observation statement."""
    # Ensure the observation is conversational and specific
    if intent:
        return f"What I'm seeing is {context.lower()} (detected as {intent})."
    return f"What I'm seeing is {context.lower()}."


def _craft_reasoning(context: str, stakes: StakeLevel) -> str:
    """Craft reasoning for why this matters (medium/high stakes only)."""
    if stakes == "high":
        return (
            "This situation has high stakes. Getting the tone, timing, and approach "
            "right matters for the outcome. A misstep could escalate things or "
            "undermine your position."
        )
    elif stakes == "medium":
        return (
            "The way this is handled matters. Clear, professional communication "
            "will help ensure the right outcome and maintain relationships."
        )
    return ""


def _craft_recommendation(recommendation: str, stakes: StakeLevel) -> str:
    """Craft a clear, confident recommendation."""
    # Ensure recommendation is actionable and clear
    if not recommendation.strip().endswith((".", "?", "!")):
        recommendation = recommendation.strip() + "."

    # Add appropriate phrasing based on stakes
    if stakes == "high":
        return f"I recommend we {recommendation}"
    elif stakes == "medium":
        return f"I recommend {recommendation}"
    else:
        return f"{recommendation}"


def format_for_user(explanation: Dict[str, Any]) -> str:
    """
    Format an explanation dict into a user-friendly message.

    Args:
        explanation: Dict from build_explanation()

    Returns:
        Formatted string ready for display
    """
    parts = []

    # What I'm seeing
    parts.append(explanation["what_i_see"])

    # Why it matters (if present)
    if explanation.get("why_it_matters"):
        parts.append(f"\n\n{explanation['why_it_matters']}")

    # Recommendation
    parts.append(f"\n\n{explanation['recommendation']}")

    # Confirmation prompt
    if explanation["requires_confirmation"]:
        parts.append("\n\nWant me to proceed?")

    return "".join(parts)
