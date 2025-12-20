"""
Multi-Agent Chat Service (v0)

Minimal proof: 3 agents, one thread, real conversation.
- Primary (Quillo) frames
- Claude gives perspective
- Grok gives contrasting perspective
- Primary (Quillo) synthesizes

No tools execution. No streaming. Just conversation.
"""
import uuid
from typing import Optional
from loguru import logger
import httpx

from ..config import settings


# Model IDs for multi-agent chat
CLAUDE_MODEL = "anthropic/claude-3.5-sonnet"
GROK_MODEL = "x-ai/grok-2-1212"  # Grok 2
PRIMARY_MODEL = settings.openrouter_balanced_model


# System prompts for each agent (forbid chain-of-thought)
PRIMARY_FRAME_PROMPT = """You are Quillo, a helpful AI assistant for business communication.
Acknowledge the user's question briefly and frame what perspectives would be useful.
Be conversational and warm. No chain-of-thought. No "here's my reasoning". Just natural speech."""

CLAUDE_PROMPT = """You are Claude, an AI assistant focused on thoughtful, nuanced analysis.
Provide a helpful perspective on the user's question. Be insightful but concise.
No chain-of-thought. No "I'm thinking". Just share your perspective naturally."""

GROK_PROMPT = """You are Grok, an AI with a contrarian, challenger mindset.
Question assumptions. Offer a different angle or potential risks the user should consider.
Be direct and a bit provocative, but helpful. No chain-of-thought. Just speak plainly."""

PRIMARY_SYNTH_PROMPT = """You are Quillo, synthesizing the conversation.
You've seen perspectives from Claude and Grok. Now give a clear recommendation.
End with one thoughtful follow-up question to help the user think deeper.
No chain-of-thought. Be conversational and actionable."""


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
            "content": f"Got it. Let me bring in a couple perspectives on this. We'll hear from Claude on the thoughtful approach, then Grok will challenge some assumptions."
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
            "agent": "quillo",
            "content": f"Both perspectives have merit. My recommendation: start with Claude's long-term thinking to set your foundation, but use Grok's urgency test—if waiting costs you the opportunity, act faster. Quick question: what's your personal risk tolerance on this decision?"
        }
    ]


async def _generate_openrouter_transcript(text: str) -> list[dict]:
    """
    Generate real multi-agent conversation using OpenRouter.

    Calls OpenRouter 3 times:
    1. Claude perspective
    2. Grok perspective
    3. Primary synthesis

    Args:
        text: User's input text

    Returns:
        List of message dicts
    """
    messages = []

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
        system_prompt=CLAUDE_PROMPT,
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
        system_prompt=GROK_PROMPT,
        user_message=text
    )
    messages.append({
        "role": "assistant",
        "agent": "grok",
        "content": grok_content
    })

    # Message 4: Primary synthesis
    # Give primary context of what Claude and Grok said
    synth_prompt = f"""User asked: {text}

Claude's perspective: {claude_content}

Grok's perspective: {grok_content}

Now synthesize these into a clear recommendation and end with one follow-up question."""

    primary_synth = await _call_openrouter(
        model=PRIMARY_MODEL,
        system_prompt=PRIMARY_SYNTH_PROMPT,
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
    # Keep it simple for v0
    return "Got it. Let me bring in a couple perspectives on this. We'll hear from Claude, then Grok will challenge some assumptions."


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
