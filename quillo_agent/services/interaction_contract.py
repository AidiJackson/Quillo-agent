"""
Quillo Interaction Contract v1

Central behavioral contract controlling Quillo's conversational behavior.
This contract enforces consistency across all interaction points.

CONTRACT RULES:
- User always speaks first (no auto-greeting)
- Quillo replies conversationally (ChatGPT-level: confident, helpful, natural)
- No chain-of-thought, no "here's my reasoning", no internal tool narration
- Stakes-aware confirmation:
  - low stakes: proceed automatically
  - medium/high stakes: ask for confirmation before executing
- Ask clarifying questions (1-3 max) only when needed to proceed safely
- For missing integrations: acknowledge gap, offer closest available workflow
- Proactive agent suggestions (v1): suggest additional agents when helpful, user must consent
- RAW_CHAT_MODE: disables suggestions, direct LLM responses only
"""
from enum import Enum
from typing import Literal, Optional, Dict, Any, List
from loguru import logger

from ..config import settings
from .agent_suggestion import (
    should_suggest_agents,
    build_agent_suggestion_message,
    detect_ambiguity
)


class Stakes(str, Enum):
    """Stakes level for user request"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionIntent(str, Enum):
    """Type of action user is requesting"""
    CHAT_ONLY = "chat_only"  # Just asking questions, no execution
    PLAN = "plan"  # Wants to plan out an approach
    EXECUTE = "execute"  # Ready to take action
    EXTERNAL_INTEGRATION = "external_integration"  # Requires external tool (email, calendar, etc.)


Mode = Literal["answer", "clarify", "confirm_required", "cannot_do_yet"]


# Forbidden phrases that leak internal implementation details
FORBIDDEN_PHRASES = [
    "chain-of-thought",
    "i'm thinking",
    "internal",
    "tool execution",
    "llm",
    "my reasoning",
    "here's my reasoning",
    "let me think",
    "internally",
    "behind the scenes",
    "under the hood",
    "my analysis",
    "processing",
]


def enforce_contract(
    message: str,
    stakes: str,
    intent: str,
    has_integrations: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """
    Enforce the Quillo Interaction Contract v1 for conversational behavior.

    Takes a user message and context, returns a contract-compliant response
    structure with the appropriate mode, message, and requirements.

    Args:
        message: User's input text
        stakes: Stakes level ("low", "medium", "high")
        intent: Action intent type
        has_integrations: Dict of integration availability (e.g., {"email": False})

    Returns:
        Dict with:
        - mode: "answer" | "clarify" | "confirm_required" | "cannot_do_yet"
        - assistant_message: str (the actual Quillo reply)
        - questions: list[str] (optional, for clarification)
        - requires_confirmation: bool
        - suggested_next_step: optional str (for cannot_do_yet mode)

    Examples:
        >>> enforce_contract("Draft an email", "medium", "execute", {"email": True})
        {
            "mode": "confirm_required",
            "assistant_message": "Got it. I'll draft an email for you. Want me to proceed?",
            "questions": [],
            "requires_confirmation": True,
            "suggested_next_step": None
        }

        >>> enforce_contract("Send all my emails", "high", "external_integration", {"email": False})
        {
            "mode": "cannot_do_yet",
            "assistant_message": "I can't pull your inbox yet. If you paste...",
            "questions": [],
            "requires_confirmation": False,
            "suggested_next_step": "Paste the email thread here and I can help you..."
        }
    """
    has_integrations = has_integrations or {}
    stakes_level = Stakes(stakes)
    action_intent = ActionIntent(intent)

    logger.debug(f"Contract enforcement: stakes={stakes}, intent={intent}, integrations={has_integrations}")

    # Check for missing integrations first
    if action_intent == ActionIntent.EXTERNAL_INTEGRATION:
        # Detect what integration is needed
        integration_needed = _detect_needed_integration(message)
        if integration_needed and not has_integrations.get(integration_needed, False):
            return _build_cannot_do_yet_response(integration_needed, message)

    # Check if clarification is needed
    needs_clarification, questions = _needs_clarification(message, action_intent)
    if needs_clarification:
        return _build_clarify_response(message, questions)

    # Build the response based on stakes and intent
    if stakes_level == Stakes.LOW:
        # Low stakes: proceed automatically
        response = _build_answer_response(message, action_intent, requires_confirmation=False)
    else:
        # Medium/high stakes: require confirmation
        response = _build_confirm_required_response(message, action_intent, stakes_level)

    # Check if we should suggest bringing in additional agents (v1)
    # Only suggest if not already in clarify/cannot_do_yet mode
    ambiguity = detect_ambiguity(message, intent)
    if should_suggest_agents(stakes, intent, ambiguity, message):
        # Append suggestion to assistant message
        suggestion = build_agent_suggestion_message(message)
        response["assistant_message"] = f"{response['assistant_message']}\n\n{suggestion}"
        response["suggested_next_step"] = "add_agents"
        response["requires_confirmation"] = True
        logger.debug("Agent suggestion added to response")

    return response


def _detect_needed_integration(message: str) -> Optional[str]:
    """
    Detect which integration the user is requesting.

    Args:
        message: User input text

    Returns:
        Integration name or None
    """
    message_lower = message.lower()

    # Email keywords
    if any(keyword in message_lower for keyword in [
        "inbox", "email", "emails", "gmail", "outlook", "send email", "check my email"
    ]):
        return "email"

    # Calendar keywords
    if any(keyword in message_lower for keyword in [
        "calendar", "schedule", "meeting", "appointment", "event"
    ]):
        return "calendar"

    # CRM keywords
    if any(keyword in message_lower for keyword in [
        "crm", "contacts", "client list", "customer"
    ]):
        return "crm"

    return None


def _needs_clarification(message: str, intent: ActionIntent) -> tuple[bool, List[str]]:
    """
    Determine if clarifying questions are needed.

    Only asks questions (1-3 max) when required to proceed safely.

    Args:
        message: User input text
        intent: Action intent

    Returns:
        Tuple of (needs_clarification: bool, questions: List[str])
    """
    questions = []
    message_lower = message.lower()

    # For execution intent, check if core details are missing
    if intent == ActionIntent.EXECUTE:
        # Check for vague action requests
        if len(message.strip()) < 20:
            questions.append("What specifically would you like me to do?")
            return True, questions

        # Check for missing recipient in communication tasks
        if any(word in message_lower for word in ["send", "email", "message"]):
            if not any(word in message_lower for word in ["to ", "recipient", "@", "client", "team"]):
                questions.append("Who should I send this to?")
                return True, questions

    # For external integrations, check if scope is clear
    if intent == ActionIntent.EXTERNAL_INTEGRATION:
        if "all" in message_lower or "every" in message_lower:
            questions.append("To make sure I get this right, which specific items should I focus on?")
            return True, questions

    return False, questions


def _build_answer_response(
    message: str,
    intent: ActionIntent,
    requires_confirmation: bool = False
) -> Dict[str, Any]:
    """Build an answer mode response for low-stakes requests."""
    # Generate a warm, conversational acknowledgment
    assistant_message = _craft_conversational_reply(message, intent, requires_confirmation=False)

    return {
        "mode": "answer",
        "assistant_message": assistant_message,
        "questions": [],
        "requires_confirmation": requires_confirmation,
        "suggested_next_step": None
    }


def _build_confirm_required_response(
    message: str,
    intent: ActionIntent,
    stakes: Stakes
) -> Dict[str, Any]:
    """Build a confirmation required response for medium/high stakes."""
    assistant_message = _craft_conversational_reply(message, intent, requires_confirmation=True)

    return {
        "mode": "confirm_required",
        "assistant_message": assistant_message,
        "questions": [],
        "requires_confirmation": True,
        "suggested_next_step": None
    }


def _build_clarify_response(message: str, questions: List[str]) -> Dict[str, Any]:
    """Build a clarification request response."""
    # Create a brief acknowledgment followed by the question(s)
    if len(questions) == 1:
        assistant_message = f"Quick question before I do that: {questions[0]}"
    else:
        questions_text = "\n".join(f"- {q}" for q in questions)
        assistant_message = f"Just a couple quick questions:\n{questions_text}"

    return {
        "mode": "clarify",
        "assistant_message": assistant_message,
        "questions": questions,
        "requires_confirmation": False,
        "suggested_next_step": None
    }


def _build_cannot_do_yet_response(integration: str, message: str) -> Dict[str, Any]:
    """Build a response for missing integration capabilities."""
    # Map integration to alternative workflow suggestions
    alternatives = {
        "email": (
            "I can't pull your inbox yet. If you paste the email thread here, "
            "I can help you draft a response, improve clarity, or argue your position."
        ),
        "calendar": (
            "I can't access your calendar yet. If you paste your current schedule, "
            "I can help you organize it or draft scheduling responses."
        ),
        "crm": (
            "I can't access your CRM yet. If you share the client details here, "
            "I can help you draft communications or plan your outreach."
        )
    }

    assistant_message = alternatives.get(
        integration,
        "I don't have that integration yet. If you share the relevant details here, I can still help."
    )

    # Suggest next step
    next_step_suggestions = {
        "email": "Paste the email thread here and I can help you craft the perfect response.",
        "calendar": "Share your current schedule and I can help you organize it.",
        "crm": "Share the client details and I can help you plan your approach."
    }

    suggested_next_step = next_step_suggestions.get(
        integration,
        "Share the details here and I'll help you work through it."
    )

    return {
        "mode": "cannot_do_yet",
        "assistant_message": assistant_message,
        "questions": [],
        "requires_confirmation": False,
        "suggested_next_step": suggested_next_step
    }


def _craft_conversational_reply(
    message: str,
    intent: ActionIntent,
    requires_confirmation: bool
) -> str:
    """
    Craft a warm, conversational reply in operator tone.

    Uses phrases like "Got it.", "Here's what I suggest.", etc.
    No chain-of-thought, no reasoning explanations.

    Args:
        message: User's message
        intent: Action intent
        requires_confirmation: Whether this requires user confirmation

    Returns:
        Conversational reply string
    """
    message_lower = message.lower()

    # Acknowledgment phrases (warm operator tone)
    acknowledgments = {
        ActionIntent.CHAT_ONLY: "Got it.",
        ActionIntent.PLAN: "Got it.",
        ActionIntent.EXECUTE: "On it.",
        ActionIntent.EXTERNAL_INTEGRATION: "Understood."
    }

    ack = acknowledgments.get(intent, "Got it.")

    # Build the main response based on intent
    if intent == ActionIntent.CHAT_ONLY:
        response = f"{ack} {_summarize_request(message)}"
    elif intent == ActionIntent.PLAN:
        response = f"{ack} Here's what I suggest: {_summarize_request(message)}"
    elif intent == ActionIntent.EXECUTE:
        response = f"{ack} I'll {_extract_action(message)}."
    else:
        response = f"{ack} I'll help with {_summarize_request(message)}."

    # Add confirmation prompt if required
    if requires_confirmation:
        response += " Want me to proceed?"

    return response


def _summarize_request(message: str) -> str:
    """
    Summarize the user's request in a natural way.

    Args:
        message: User input

    Returns:
        Brief summary
    """
    # For now, use first 100 chars or until first period
    summary = message.strip()
    if len(summary) > 100:
        # Find first sentence
        first_period = summary.find(".")
        if first_period > 0 and first_period < 100:
            summary = summary[:first_period]
        else:
            summary = summary[:97] + "..."

    # Make it lowercase and clean
    summary = summary[0].lower() + summary[1:] if summary else summary

    return summary


def _extract_action(message: str) -> str:
    """
    Extract the core action verb from the message.

    Args:
        message: User input

    Returns:
        Action verb phrase
    """
    message_lower = message.lower().strip()

    # Common action verbs
    action_verbs = [
        "draft", "write", "send", "create", "build", "make",
        "reply", "respond", "rewrite", "edit", "fix", "update",
        "schedule", "plan", "organize", "review"
    ]

    for verb in action_verbs:
        if message_lower.startswith(verb):
            # Extract up to the verb and a few words after
            words = message_lower.split()
            verb_idx = next((i for i, w in enumerate(words) if w.startswith(verb)), 0)
            action_phrase = " ".join(words[verb_idx:min(verb_idx + 4, len(words))])
            return action_phrase

    # Fallback: use beginning of message
    words = message_lower.split()
    return " ".join(words[:4]) if len(words) > 4 else message_lower


def validate_no_leakage(text: str) -> bool:
    """
    Validate that text doesn't contain forbidden chain-of-thought phrases.

    Args:
        text: Text to validate

    Returns:
        True if clean, False if contains forbidden phrases

    Raises:
        ValueError: If forbidden phrases detected (for testing)
    """
    text_lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text_lower:
            logger.error(f"Contract violation: forbidden phrase '{phrase}' detected in: {text}")
            raise ValueError(f"Contract violation: forbidden phrase '{phrase}' detected")
    return True
