"""
Quillopreneur business advice service
"""
import uuid
import httpx
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session
from ..config import settings, is_offline_mode
from ..models import UserProfile
from .llm import LLMRouter

# Model mapping based on routing tier (Anthropic)
MODEL_MAP = {
    "fast": "claude-3-haiku-20240307",
    "balanced": "claude-3-5-sonnet-20241022",
    "premium": "claude-3-5-sonnet-20241022",  # Using sonnet for now; can upgrade to opus
}

# Initialize LLM router for OpenRouter support
llm_router = LLMRouter()

# Offline response templates for common business questions
OFFLINE_TEMPLATES = {
    "default": """As a business advisor, I'd recommend starting with these key considerations:

1. **Clarify your objectives**: Define what success looks like for this initiative.
2. **Assess resources**: Consider your time, budget, and team capabilities.
3. **Research the market**: Understand your customers, competitors, and trends.
4. **Start small and iterate**: Test assumptions quickly with a minimum viable approach.
5. **Measure and learn**: Set clear metrics and be ready to pivot based on data.

For more detailed, personalized advice, please ensure API keys are configured."""
}


async def answer_business_question(
    text: str,
    user_id: Optional[str] = None,
    db: Optional[Session] = None
) -> tuple[str, str]:
    """
    Answer a business question using Quillopreneur specialist knowledge.

    Args:
        text: The business question or topic
        user_id: Optional user ID for personalization
        db: Optional database session for profile loading

    Returns:
        Tuple of (answer, model_name)
    """
    # Truncate input to prevent prompt injection and excessive tokens
    safe_text = text[:2000]

    # Load user profile excerpt if available
    profile_excerpt = ""
    if user_id and db:
        try:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile and profile.profile_md:
                # Extract first 300 chars as context
                profile_excerpt = profile.profile_md[:300]
        except Exception as e:
            logger.warning(f"Failed to load user profile: {e}")

    # Check if we're in offline mode first
    if is_offline_mode():
        logger.info("Using offline business advice template (no API keys configured)")
        return OFFLINE_TEMPLATES["default"], "template"

    # In raw chat mode, ONLY use OpenRouter with chat model (no Anthropic fallback)
    if settings.raw_chat_mode:
        if not settings.openrouter_api_key:
            logger.warning("Raw chat mode enabled but OpenRouter not configured")
            return OFFLINE_TEMPLATES["default"], "template"

        try:
            answer = await llm_router.answer_business_question(safe_text, profile_excerpt)
            if answer:
                model_name = llm_router._get_openrouter_model(for_chat=True)
                logger.info(f"Using OpenRouter model (raw mode): {model_name}")
                return answer, f"openrouter/{model_name}"
            else:
                logger.warning("OpenRouter returned None in raw mode; using offline template")
                return OFFLINE_TEMPLATES["default"], "template"
        except Exception as e:
            logger.error(f"OpenRouter API failed in raw mode: {e}; using offline template")
            return OFFLINE_TEMPLATES["default"], "template"

    # Advanced mode: Try OpenRouter first if configured
    if settings.openrouter_api_key:
        try:
            answer = await llm_router.answer_business_question(safe_text, profile_excerpt)
            if answer:
                model_name = llm_router._get_openrouter_model(for_chat=True)
                logger.info(f"Using OpenRouter model: {model_name}")
                return answer, f"openrouter/{model_name}"
            else:
                logger.warning("OpenRouter returned None; trying Anthropic fallback")
        except Exception as e:
            logger.error(f"OpenRouter API failed: {e}; trying Anthropic fallback")

    # Try Anthropic if OpenRouter failed or not configured
    if settings.anthropic_api_key:
        try:
            answer = await _answer_with_anthropic(safe_text, profile_excerpt)
            model_name = MODEL_MAP.get(settings.model_routing, "claude-3-5-sonnet-20241022")
            return answer, model_name
        except Exception as e:
            logger.error(f"Anthropic API failed: {e}")
            # Fall through to offline response

    # Offline fallback (API call failed)
    logger.warning("API calls failed, falling back to offline template")
    return OFFLINE_TEMPLATES["default"], "template"


def _get_system_prompt() -> str:
    """
    Get the appropriate system prompt based on RAW_CHAT_MODE setting.

    Returns:
        System prompt string
    """
    if settings.raw_chat_mode:
        # Raw mode: minimal, ChatGPT-like prompt
        return """You are Quillo, a helpful AI assistant. Provide clear, direct answers to user questions."""
    else:
        # Advanced mode: Quillopreneur specialist
        return """You are Quillopreneur, an expert business advisor specializing in entrepreneurship,
strategy, and growth. Provide actionable, practical advice based on proven business principles.
Be concise, specific, and helpful. Focus on the user's question."""


async def _answer_with_anthropic(text: str, profile_excerpt: str) -> str:
    """
    Generate business advice using Anthropic API.

    Args:
        text: User's business question
        profile_excerpt: Short user profile context

    Returns:
        Business advice answer
    """
    # System message based on mode
    system_message = _get_system_prompt()

    # User message with optional profile context
    user_message = text
    if profile_excerpt:
        user_message = f"User context: {profile_excerpt}\n\nQuestion: {text}"

    model = MODEL_MAP.get(settings.model_routing, "claude-3-5-sonnet-20241022")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": 1000,
                "system": system_message,
                "messages": [{"role": "user", "content": user_message}]
            },
            timeout=30.0
        )
        response.raise_for_status()
        content = response.json()["content"][0]["text"]
        return content
