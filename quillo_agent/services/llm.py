"""
LLM service with safe fallbacks for classification and planning
"""
import httpx
import json
from typing import Optional, Dict, Any, List
from loguru import logger
from ..config import settings


class LLMRouter:
    """LLM-based routing and planning with graceful fallbacks"""

    def __init__(self):
        self.openrouter_key = settings.openrouter_api_key
        self.openrouter_base_url = settings.openrouter_base_url
        self.anthropic_key = settings.anthropic_api_key
        self.model_routing = settings.model_routing

    def _get_openrouter_model(self, tier: Optional[str] = None) -> str:
        """Get OpenRouter model based on routing tier"""
        routing_tier = tier or self.model_routing
        model_map = {
            "fast": settings.openrouter_fast_model,
            "balanced": settings.openrouter_balanced_model,
            "premium": settings.openrouter_premium_model,
        }
        return model_map.get(routing_tier, settings.openrouter_balanced_model)

    def _truncate_user_input(self, text: str, max_chars: int = 2000) -> str:
        """Truncate user input to prevent prompt injection and excessive tokens"""
        if len(text) > max_chars:
            logger.warning(f"Truncating user input from {len(text)} to {max_chars} chars")
            return text[:max_chars]
        return text

    async def classify_fallback(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Fallback LLM-based classification when rule-based confidence is low.

        Returns:
            Optional dict with intent, reasons, slots, confidence
            Returns None if no API keys are configured
        """
        if not self.openrouter_key and not self.anthropic_key:
            logger.warning("No LLM API keys configured; skipping LLM fallback")
            return None

        try:
            # Prefer OpenRouter if available
            if self.openrouter_key:
                return await self._classify_openrouter(text)
            elif self.anthropic_key:
                return await self._classify_anthropic(text)
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return None

    async def _classify_anthropic(self, text: str) -> Optional[Dict[str, Any]]:
        """Classify using Anthropic API"""
        # Truncate input for safety
        safe_text = self._truncate_user_input(text)

        prompt = f"""Classify this user request into one of: response, rewrite, argue, clarity.
Extract any outcome slots (Defuse, Negotiate, Escalate).

User request: {safe_text}

Respond in JSON format:
{{"intent": "...", "slots": {{}}, "reasons": ["..."], "confidence": 0.0-1.0}}"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 500,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                content = response.json()["content"][0]["text"]
                # Safe JSON parsing
                return json.loads(content)
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None

    async def _classify_openrouter(self, text: str) -> Optional[Dict[str, Any]]:
        """Classify using OpenRouter API with safe JSON parsing"""
        # Truncate input for safety
        safe_text = self._truncate_user_input(text)

        # System message to prevent prompt injection
        system_message = """You are a classification assistant. Your ONLY job is to classify user requests.
You MUST respond with valid JSON only. Do not include any other text, explanations, or markdown.
Classify the user request into one of: response, rewrite, argue, clarity.
Extract any outcome slots: Defuse, Negotiate, or Escalate."""

        user_message = f"""Classify this user request:

{safe_text}

Respond with ONLY this JSON format (no markdown, no other text):
{{"intent": "response|rewrite|argue|clarity", "slots": {{"outcome": "Defuse|Negotiate|Escalate"}}, "reasons": ["reason1", "reason2"], "confidence": 0.0-1.0}}"""

        try:
            model = self._get_openrouter_model("fast")  # Use fast model for classification
            result = await self._openrouter_chat(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                model=model,
                max_tokens=500,
                timeout=10.0
            )

            if not result:
                return None

            # Safe JSON parsing with fallback
            try:
                parsed = json.loads(result)
                # Validate required fields
                if "intent" in parsed and "confidence" in parsed:
                    return parsed
                else:
                    logger.warning("LLM response missing required fields; ignoring")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}. Raw response: {result[:200]}")
                return None

        except Exception as e:
            logger.error(f"OpenRouter classification error: {e}")
            return None

    async def plan_reasoning(
        self, intent: str, slots: Optional[Dict], text: Optional[str]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Enrich plan steps with LLM reasoning.

        Returns:
            Optional list of enriched steps with rationale
            Returns None if no API keys are configured
        """
        if not self.openrouter_key and not self.anthropic_key:
            logger.debug("No LLM API keys; skipping plan enrichment")
            return None

        # Truncate input for safety
        safe_text = self._truncate_user_input(text) if text else ""

        # System message to prevent prompt injection
        system_message = """You are a planning assistant. Your ONLY job is to generate execution plan steps.
You MUST respond with valid JSON only. Do not include any other text, explanations, or markdown."""

        user_message = f"""Generate a plan for this intent: {intent}

Slots: {json.dumps(slots or {{}})}
User text: {safe_text}

Respond with ONLY this JSON format (no markdown, no other text):
{{"steps": [{{"tool": "tool_name", "premium": true|false, "rationale": "why this step"}}]}}"""

        try:
            # Use premium model if MODEL_ROUTING=premium
            tier = "premium" if self.model_routing == "premium" else "balanced"

            if self.openrouter_key:
                model = self._get_openrouter_model(tier)
                result = await self._openrouter_chat(
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    model=model,
                    max_tokens=1000,
                    timeout=15.0
                )

                if result:
                    try:
                        parsed = json.loads(result)
                        return parsed.get("steps")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse plan JSON: {e}")
                        return None

            return None

        except Exception as e:
            logger.error(f"Plan reasoning failed: {e}")
            return None

    async def _openrouter_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int = 1000,
        timeout: float = 15.0
    ) -> Optional[str]:
        """
        Make a chat-completions request to OpenRouter.

        Args:
            messages: List of message dicts with role and content
            model: Model identifier (e.g., "anthropic/claude-3-haiku")
            max_tokens: Max tokens to generate
            timeout: Request timeout in seconds

        Returns:
            Optional string response content
            Returns None on error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://quillography.ai",  # Optional: for rankings
                        "X-Title": "Quillo Agent",  # Optional: for rankings
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                    },
                    timeout=timeout
                )
                response.raise_for_status()
                data = response.json()

                # Extract content from OpenRouter response
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    return content
                else:
                    logger.error(f"Unexpected OpenRouter response format: {data}")
                    return None

        except httpx.TimeoutException:
            logger.error(f"OpenRouter request timeout after {timeout}s")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            return None

    async def answer_business_question(
        self, text: str, profile_excerpt: str = ""
    ) -> Optional[str]:
        """
        Answer a business question using OpenRouter.

        Args:
            text: Business question
            profile_excerpt: Optional user profile context

        Returns:
            Optional string answer
            Returns None on error
        """
        if not self.openrouter_key:
            logger.debug("OpenRouter API key not configured")
            return None

        # Truncate inputs for safety
        safe_text = self._truncate_user_input(text)
        safe_profile = self._truncate_user_input(profile_excerpt, max_chars=300)

        # System message to prevent prompt injection
        system_message = """You are Quillopreneur, an expert business advisor specializing in entrepreneurship,
strategy, and growth. Provide actionable, practical advice based on proven business principles.
Be concise, specific, and helpful. Focus on the user's question."""

        # User message with optional profile context
        user_message = safe_text
        if safe_profile:
            user_message = f"User context: {safe_profile}\n\nQuestion: {safe_text}"

        try:
            model = self._get_openrouter_model()  # Use routing tier
            result = await self._openrouter_chat(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                model=model,
                max_tokens=1000,
                timeout=30.0
            )
            return result

        except Exception as e:
            logger.error(f"Business question answering failed: {e}")
            return None
