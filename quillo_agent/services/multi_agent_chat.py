"""
Multi-Agent Chat Service (v0.1)

Multi-agent conversation with 4 peer agents:
- Primary (Quillo) frames
- Claude gives perspective
- Grok gives contrasting perspective
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


# Model IDs for multi-agent chat
CLAUDE_MODEL = "anthropic/claude-3.5-sonnet"
GROK_MODEL = "x-ai/grok-2-1212"  # Grok 2
GEMINI_MODEL = settings.openrouter_gemini_model
PRIMARY_MODEL = settings.openrouter_balanced_model


def _get_agent_prompt(agent_name: str, mode: str = "raw") -> str:
    """
    Get system prompt for an agent based on the prompt mode.

    Args:
        agent_name: Name of agent ("claude", "grok", "gemini", "primary_frame", "primary_synth")
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
            "grok": """You are Grok. Reply naturally in your own style.
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
    agents: Optional[list[str]] = None
) -> tuple[list[dict], str]:
    """
    Run a multi-agent chat conversation.

    Args:
        text: User's input text
        user_id: Optional user identifier
        agents: List of agent names (default: ["primary", "claude", "grok"])

    Returns:
        Tuple of (messages, provider)
        - messages: List of dicts with {role, agent, content}
        - provider: "openrouter" or "template"
    """
    agents = agents or ["primary", "claude", "grok"]
    logger.info(f"Multi-agent chat: user_id={user_id}, agents={agents}")

    # Check if OpenRouter is available
    if not settings.openrouter_api_key:
        logger.info("OpenRouter key missing, using template responses")
        return _generate_template_transcript(text), "template"

    # Use OpenRouter to generate real conversation
    try:
        messages = await _generate_openrouter_transcript(text)
        return messages, "openrouter"
    except Exception as e:
        logger.error(f"OpenRouter multi-agent chat failed: {e}")
        # Fallback to template
        return _generate_template_transcript(text), "template"


def _generate_template_transcript(text: str) -> list[dict]:
    """
    Generate a deterministic template transcript (offline mode).

    Args:
        text: User's input text

    Returns:
        List of message dicts
    """
    # Extract a short excerpt from user text for personalization
    excerpt = text[:50] + "..." if len(text) > 50 else text

    return [
        {
            "role": "assistant",
            "agent": "quillo",
            "content": f"Got it. Let me bring in a few perspectives on this. We'll hear from Claude, Grok, and Gemini."
        },
        {
            "role": "assistant",
            "agent": "claude",
            "content": f"Looking at your question about \"{excerpt}\", I'd consider the long-term implications first. The key is balancing immediate needs with sustainable outcomes. Whatever path you choose, documentation and clear communication will be critical."
        },
        {
            "role": "assistant",
            "agent": "grok",
            "content": f"Hold up—before you get too comfortable with that, ask yourself: what if the opposite is true? Sometimes the 'thoughtful' path is just procrastination with better PR. What's the risk of moving fast and adjusting later versus overthinking and missing the window?"
        },
        {
            "role": "assistant",
            "agent": "gemini",
            "content": f"Here's a structured view: break this into phases. First, validate your core assumption. Second, test with a small pilot. Third, scale what works. This approach gives you Claude's thoughtfulness without Grok's risk of paralysis."
        },
        {
            "role": "assistant",
            "agent": "quillo",
            "content": f"All three perspectives add value. My recommendation: use Gemini's phased approach as your framework, with Claude's long-term lens and Grok's urgency check at each phase. Quick question: what's the smallest pilot you could run to validate this?"
        }
    ]


async def _generate_openrouter_transcript(text: str) -> list[dict]:
    """
    Generate real multi-agent conversation using OpenRouter.

    Calls OpenRouter 4 times for peer agents + synthesis:
    1. Claude perspective
    2. Grok perspective
    3. Gemini perspective
    4. Primary synthesis

    Args:
        text: User's input text

    Returns:
        List of message dicts
    """
    messages = []
    prompt_mode = settings.multi_agent_prompt_mode

    # Message 1: Primary frames
    primary_frame = _generate_short_frame(text)
    messages.append({
        "role": "assistant",
        "agent": "quillo",
        "content": primary_frame
    })

    # Message 2: Claude perspective
    claude_content = await _call_openrouter(
        model=CLAUDE_MODEL,
        system_prompt=_get_agent_prompt("claude", mode=prompt_mode),
        user_message=text
    )
    messages.append({
        "role": "assistant",
        "agent": "claude",
        "content": claude_content
    })

    # Message 3: Grok perspective
    grok_content = await _call_openrouter(
        model=GROK_MODEL,
        system_prompt=_get_agent_prompt("grok", mode=prompt_mode),
        user_message=text
    )
    messages.append({
        "role": "assistant",
        "agent": "grok",
        "content": grok_content
    })

    # Message 4: Gemini perspective
    gemini_content = await _call_openrouter(
        model=GEMINI_MODEL,
        system_prompt=_get_agent_prompt("gemini", mode=prompt_mode),
        user_message=text
    )
    messages.append({
        "role": "assistant",
        "agent": "gemini",
        "content": gemini_content
    })

    # Message 5: Primary synthesis
    # Give primary context of what all three peer agents said
    synth_prompt = f"""User asked: {text}

Claude's perspective: {claude_content}

Grok's perspective: {grok_content}

Gemini's perspective: {gemini_content}

Now synthesize these into a clear recommendation and end with one follow-up question."""

    primary_synth = await _call_openrouter(
        model=PRIMARY_MODEL,
        system_prompt=_get_agent_prompt("primary_synth", mode=prompt_mode),
        user_message=synth_prompt
    )
    messages.append({
        "role": "assistant",
        "agent": "quillo",
        "content": primary_synth
    })

    return messages


def _generate_short_frame(text: str) -> str:
    """Generate a short framing message for Primary."""
    # Keep it simple for v0.1
    return "Got it. Let me bring in a few perspectives on this. We'll hear from Claude, Grok, and Gemini."


async def _call_openrouter(
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 300
) -> str:
    """
    Call OpenRouter chat completion API.

    Args:
        model: Model ID (e.g., "anthropic/claude-3.5-sonnet")
        system_prompt: System prompt for the agent
        user_message: User's message
        max_tokens: Max tokens for response

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
