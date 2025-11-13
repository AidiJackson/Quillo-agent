"""
LLM service with safe fallbacks for classification and planning
"""
import httpx
from typing import Optional, Dict, Any, List
from loguru import logger
from ..config import settings


class LLMRouter:
    """LLM-based routing and planning with graceful fallbacks"""

    def __init__(self):
        self.openrouter_key = settings.openrouter_api_key
        self.anthropic_key = settings.anthropic_api_key
        self.model_routing = settings.model_routing

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
            if self.anthropic_key:
                return await self._classify_anthropic(text)
            elif self.openrouter_key:
                return await self._classify_openrouter(text)
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return None

    async def _classify_anthropic(self, text: str) -> Optional[Dict[str, Any]]:
        """Classify using Anthropic API"""
        prompt = f"""Classify this user request into one of: response, rewrite, argue, clarity.
Extract any outcome slots (Defuse, Negotiate, Escalate).

User request: {text}

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
                # Parse JSON from content
                import json
                return json.loads(content)
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None

    async def _classify_openrouter(self, text: str) -> Optional[Dict[str, Any]]:
        """Classify using OpenRouter API"""
        # Simplified OpenRouter implementation
        logger.warning("OpenRouter classification not fully implemented; returning None")
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

        # For MVP, we'll use deterministic planning
        # LLM enrichment can be added in future iterations
        return None
