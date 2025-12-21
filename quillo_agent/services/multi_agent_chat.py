"""
Multi-Agent Chat Service (v0.1)

Multi-agent conversation with 4 peer agents:
- Primary (Quillo) frames
- Claude gives perspective
- DeepSeek gives contrasting/challenger perspective
- Gemini gives alternative angle / structured take
- Primary (Quillo) synthesizes

No tools execution. No streaming. Just conversation.
Feature: Prompt mode (raw vs tuned) for future specialist prompts.
"""
import uuid
from typing import Optional
from loguru import logger
import httpx

from ..config import settings


# Model IDs for multi-agent chat (env-configurable for reliability)
CLAUDE_MODEL = settings.openrouter_claude_agent_model
CHALLENGER_MODEL = settings.openrouter_challenger_agent_model  # DeepSeek (replaces Grok)
GEMINI_MODEL = settings.openrouter_gemini_agent_model
PRIMARY_MODEL = settings.openrouter_chat_model  # GPT-4o-mini (or GPT-4o)


def _get_agent_prompt(agent_name: str, mode: str = "raw") -> str:
    """
    Get system prompt for an agent based on the prompt mode.

    Args:
        agent_name: Name of agent ("claude", "deepseek", "gemini", "primary_frame", "primary_synth")
        mode: Prompt mode ("raw" or "tuned")

    Returns:
        System prompt string
    """
    # Raw mode: minimal constraints, model speaks naturally
    # Still prevents chain-of-thought and tool narration
    if mode == "raw":
        raw_prompts = {
            "primary_frame": """You are Quillo. Reply naturally in your own style.
Do not reveal chain-of-thought. Do not describe tool usage. Be concise and practical.""",
            "claude": """You are Claude. Reply naturally in your own style.
Do not reveal chain-of-thought. Do not describe tool usage. Be concise and practical.""",
            "deepseek": """You are DeepSeek. Reply naturally in your own style.
Do not reveal chain-of-thought. Do not describe tool usage. Be concise and practical.""",
            "gemini": """You are Gemini. Reply naturally in your own style.
Do not reveal chain-of-thought. Do not describe tool usage. Be concise and practical.""",
            "primary_synth": """You are Quillo. Reply naturally in your own style.
Do not reveal chain-of-thought. Do not describe tool usage. Be concise and practical."""
        }
        return raw_prompts.get(agent_name, raw_prompts["claude"])

    # Tuned mode: placeholder for future specialist prompts
    # For now, identical to raw (will add specialists later)
    # TODO: Load agent prompts from specialist configuration
    elif mode == "tuned":
        # Placeholder: same as raw for now
        return _get_agent_prompt(agent_name, mode="raw")

    # Default to raw
    return _get_agent_prompt(agent_name, mode="raw")


async def run_multi_agent_chat(
    text: str,
    user_id: Optional[str] = None,
    agents: Optional[list[str]] = None,
    trace_id: Optional[str] = None
) -> tuple[list[dict], str, Optional[str], bool]:
    """
    Run a multi-agent chat conversation.

    Args:
        text: User's input text
        user_id: Optional user identifier
        agents: List of agent names (default: ["primary", "claude", "deepseek"])
        trace_id: Optional trace ID for logging

    Returns:
        Tuple of (messages, provider, fallback_reason, peers_unavailable)
        - messages: List of dicts with {role, agent, content, model_id, live, unavailable_reason}
        - provider: "openrouter" or "template"
        - fallback_reason: None if live, or reason string if template fallback
        - peers_unavailable: True if Quillo succeeded but all peer agents failed
    """
    agents = agents or ["primary", "claude", "deepseek"]
    logger.info(f"Multi-agent chat: user_id={user_id}, agents={agents}, trace_id={trace_id}")

    # Check if OpenRouter is available
    if not settings.openrouter_api_key:
        fallback_reason = "openrouter_key_missing"
        logger.info(f"[{trace_id}] OpenRouter key missing, using template responses")
        return _generate_template_transcript(text), "template", fallback_reason, False

    # Use OpenRouter to generate real conversation
    try:
        messages = await _generate_openrouter_transcript(text)
        # Determine if all peers failed
        live_peer_count = sum(1 for m in messages if m.get("agent") in ["claude", "deepseek", "gemini"] and m.get("live", True))
        peers_unavailable = (live_peer_count == 0)
        return messages, "openrouter", None, peers_unavailable
    except httpx.TimeoutException as e:
        fallback_reason = "openrouter_timeout"
        logger.warning(f"[{trace_id}] Multi-agent fallback: {fallback_reason} ({e.__class__.__name__})")
        return _generate_template_transcript(text), "template", fallback_reason, False
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            fallback_reason = "openrouter_rate_limited"
        else:
            fallback_reason = "openrouter_http_error"
        logger.warning(f"[{trace_id}] Multi-agent fallback: {fallback_reason} ({e.__class__.__name__}: {e.response.status_code})")
        return _generate_template_transcript(text), "template", fallback_reason, False
    except httpx.HTTPError as e:
        fallback_reason = "openrouter_http_error"
        logger.warning(f"[{trace_id}] Multi-agent fallback: {fallback_reason} ({e.__class__.__name__})")
        return _generate_template_transcript(text), "template", fallback_reason, False
    except Exception as e:
        fallback_reason = "openrouter_exception"
        logger.warning(f"[{trace_id}] Multi-agent fallback: {fallback_reason} ({e.__class__.__name__})")
        return _generate_template_transcript(text), "template", fallback_reason, False


def _generate_template_transcript(text: str) -> list[dict]:
    """
    Generate a deterministic template transcript (offline mode).

    Args:
        text: User's input text

    Returns:
        List of message dicts with new metadata fields
    """
    # Extract a short excerpt from user text for personalization
    excerpt = text[:50] + "..." if len(text) > 50 else text

    return [
        {
            "role": "assistant",
            "agent": "quillo",
            "content": f"Got it. Let me bring in a few perspectives on this. We'll hear from Claude, DeepSeek, and Gemini.",
            "model_id": None,
            "live": True,
            "unavailable_reason": None
        },
        {
            "role": "assistant",
            "agent": "claude",
            "content": f"Looking at your question about \"{excerpt}\", I'd consider the long-term implications first. The key is balancing immediate needs with sustainable outcomes. Whatever path you choose, documentation and clear communication will be critical.",
            "model_id": None,
            "live": True,
            "unavailable_reason": None
        },
        {
            "role": "assistant",
            "agent": "deepseek",
            "content": f"Hold up—before you get too comfortable with that, ask yourself: what if the opposite is true? Sometimes the 'thoughtful' path is just procrastination with better PR. What's the risk of moving fast and adjusting later versus overthinking and missing the window?",
            "model_id": None,
            "live": True,
            "unavailable_reason": None
        },
        {
            "role": "assistant",
            "agent": "gemini",
            "content": f"Here's a structured view: break this into phases. First, validate your core assumption. Second, test with a small pilot. Third, scale what works. This approach gives you Claude's thoughtfulness without DeepSeek's risk of paralysis.",
            "model_id": None,
            "live": True,
            "unavailable_reason": None
        },
        {
            "role": "assistant",
            "agent": "quillo",
            "content": f"All three perspectives add value. My recommendation: use Gemini's phased approach as your framework, with Claude's long-term lens and DeepSeek's urgency check at each phase. Quick question: what's the smallest pilot you could run to validate this?",
            "model_id": None,
            "live": True,
            "unavailable_reason": None
        }
    ]


async def _generate_openrouter_transcript(text: str) -> list[dict]:
    """
    Generate multi-agent conversation with partial-live support.

    Flow:
    1. Quillo frame (deterministic) - if this fails, exception propagates
    2. Claude, Grok, Gemini (independent) - failures replaced with unavailable messages
    3. Quillo synthesis (adapts to available peers) - uses available perspectives

    Args:
        text: User's input text

    Returns:
        List of message dicts with new metadata fields (model_id, live, unavailable_reason)
    """
    messages = []
    prompt_mode = settings.multi_agent_prompt_mode
    peer_responses = {}

    # Message 1: Primary frame (deterministic, always succeeds)
    primary_frame = _generate_short_frame(text)
    messages.append({
        "role": "assistant",
        "agent": "quillo",
        "content": primary_frame,
        "model_id": None,
        "live": True,
        "unavailable_reason": None
    })

    # Message 2: Claude perspective (safe call)
    claude_content, claude_reason = await _call_openrouter_safe(
        model=CLAUDE_MODEL,
        system_prompt=_get_agent_prompt("claude", mode=prompt_mode),
        user_message=text
    )
    if claude_content:
        peer_responses["claude"] = claude_content
        messages.append({
            "role": "assistant",
            "agent": "claude",
            "content": claude_content,
            "model_id": CLAUDE_MODEL,
            "live": True,
            "unavailable_reason": None
        })
    else:
        messages.append({
            "role": "assistant",
            "agent": "claude",
            "content": _generate_unavailable_message("claude", claude_reason),
            "model_id": CLAUDE_MODEL,
            "live": False,
            "unavailable_reason": claude_reason
        })

    # Message 3: DeepSeek perspective (safe call)
    deepseek_content, deepseek_reason = await _call_openrouter_safe(
        model=CHALLENGER_MODEL,
        system_prompt=_get_agent_prompt("deepseek", mode=prompt_mode),
        user_message=text
    )
    if deepseek_content:
        peer_responses["deepseek"] = deepseek_content
        messages.append({
            "role": "assistant",
            "agent": "deepseek",
            "content": deepseek_content,
            "model_id": CHALLENGER_MODEL,
            "live": True,
            "unavailable_reason": None
        })
    else:
        messages.append({
            "role": "assistant",
            "agent": "deepseek",
            "content": _generate_unavailable_message("deepseek", deepseek_reason),
            "model_id": CHALLENGER_MODEL,
            "live": False,
            "unavailable_reason": deepseek_reason
        })

    # Message 4: Gemini perspective (safe call)
    gemini_content, gemini_reason = await _call_openrouter_safe(
        model=GEMINI_MODEL,
        system_prompt=_get_agent_prompt("gemini", mode=prompt_mode),
        user_message=text
    )
    if gemini_content:
        peer_responses["gemini"] = gemini_content
        messages.append({
            "role": "assistant",
            "agent": "gemini",
            "content": gemini_content,
            "model_id": GEMINI_MODEL,
            "live": True,
            "unavailable_reason": None
        })
    else:
        messages.append({
            "role": "assistant",
            "agent": "gemini",
            "content": _generate_unavailable_message("gemini", gemini_reason),
            "model_id": GEMINI_MODEL,
            "live": False,
            "unavailable_reason": gemini_reason
        })

    # Message 5: Primary synthesis (adapts to available peers)
    synth_prompt = _build_synthesis_prompt(text, peer_responses)
    synth_content, synth_reason = await _call_openrouter_safe(
        model=PRIMARY_MODEL,
        system_prompt=_get_agent_prompt("primary_synth", mode=prompt_mode),
        user_message=synth_prompt
    )

    if synth_content:
        messages.append({
            "role": "assistant",
            "agent": "quillo",
            "content": synth_content,
            "model_id": PRIMARY_MODEL,
            "live": True,
            "unavailable_reason": None
        })
    else:
        # Fallback synthesis if PRIMARY_MODEL fails
        fallback_synth = "I've gathered perspectives from the available agents above. Let me know if you'd like me to explore any aspect further."
        messages.append({
            "role": "assistant",
            "agent": "quillo",
            "content": fallback_synth,
            "model_id": PRIMARY_MODEL,
            "live": False,
            "unavailable_reason": synth_reason
        })

    # Log response lengths for all agents (for truncation monitoring)
    logger.info("Multi-agent response lengths: " + ", ".join([
        f"{msg['agent']}={len(msg['content'])} chars (live={msg.get('live', True)})"
        for msg in messages
    ]))

    return messages


def _generate_short_frame(text: str) -> str:
    """Generate a short framing message for Primary."""
    # Keep it simple for v0.1
    return "Got it. Let me bring in a few perspectives on this. We'll hear from Claude, Grok, and Gemini."


async def _call_openrouter_safe(
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 1500
) -> tuple[Optional[str], Optional[str]]:
    """
    Safely call OpenRouter, returning (content, error_reason).

    Returns:
        (content, None) if successful
        (None, reason_bucket) if failed

    Reason buckets: rate_limited, not_found, timeout, http_error, exception
    """
    try:
        content = await _call_openrouter(model, system_prompt, user_message, max_tokens)
        # Log response length for monitoring truncation issues
        if content:
            logger.debug(f"OpenRouter response from {model.split('/')[-1]}: {len(content)} chars")
        return (content, None)
    except httpx.TimeoutException:
        return (None, "timeout")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return (None, "rate_limited")
        elif e.response.status_code == 404:
            return (None, "not_found")
        else:
            return (None, "http_error")
    except Exception as e:
        logger.warning(f"OpenRouter call failed: {e.__class__.__name__}")
        return (None, "exception")


def _generate_unavailable_message(agent_name: str, reason: str) -> str:
    """Generate user-friendly unavailable message."""
    reason_display = {
        "rate_limited": "rate-limited",
        "timeout": "timed out",
        "not_found": "unavailable",
        "http_error": "unavailable",
        "exception": "unavailable"
    }
    display = reason_display.get(reason, "unavailable")
    return f"[Agent unavailable: {display}]"


def _build_synthesis_prompt(text: str, peer_responses: dict[str, Optional[str]]) -> str:
    """Build synthesis prompt from available peer responses."""
    available = []

    if peer_responses.get("claude"):
        available.append(f"Claude's perspective: {peer_responses['claude']}")
    if peer_responses.get("deepseek"):
        available.append(f"DeepSeek's perspective: {peer_responses['deepseek']}")
    if peer_responses.get("gemini"):
        available.append(f"Gemini's perspective: {peer_responses['gemini']}")

    if not available:
        return f"""User asked: {text}

All peer agents were unavailable for this request. Provide a direct, thoughtful response and end with one follow-up question."""

    perspectives = "\n\n".join(available)
    return f"""User asked: {text}

{perspectives}

Now synthesize these available perspectives into a clear recommendation and end with one follow-up question."""


async def _call_openrouter(
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 1500
) -> str:
    """
    Call OpenRouter chat completion API.

    Args:
        model: Model ID (e.g., "anthropic/claude-3.5-sonnet")
        system_prompt: System prompt for the agent
        user_message: User's message
        max_tokens: Max tokens for response (default 1500 for multi-agent)

    Returns:
        Assistant's response content

    Raises:
        httpx.HTTPError: If API call fails
    """
    url = f"{settings.openrouter_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://quillography.ai",
        "X-Title": "Quillo Multi-Agent Chat"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        logger.debug(f"OpenRouter response from {model}: {content[:100]}...")
        return content
