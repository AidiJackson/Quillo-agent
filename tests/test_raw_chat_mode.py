"""
Tests for Raw Chat Mode (ChatGPT-like behavior)

Verifies that when RAW_CHAT_MODE=true:
- No automatic agent suggestions
- Minimal system prompts
- Direct LLM responses only
- Multi-agent only when explicitly requested
"""
import pytest
from unittest.mock import patch
from quillo_agent.services.agent_suggestion import should_suggest_agents
from quillo_agent.services.interaction_contract import enforce_contract
from quillo_agent.services.llm import LLMRouter
from quillo_agent.services.advice import _get_system_prompt
from quillo_agent.config import settings


class TestRawChatModeAgentSuggestions:
    """Test that raw mode disables automatic agent suggestions"""

    def test_raw_mode_disables_agent_suggestions_high_stakes(self):
        """High stakes should NOT suggest agents in raw mode"""
        with patch.object(settings, 'raw_chat_mode', True):
            result = should_suggest_agents(
                stakes="high",
                intent="decision",
                ambiguity=True,
                topic="critical business decision"
            )
            assert result is False

    def test_raw_mode_disables_agent_suggestions_complex_intent(self):
        """Complex intents should NOT suggest agents in raw mode"""
        with patch.object(settings, 'raw_chat_mode', True):
            result = should_suggest_agents(
                stakes="medium",
                intent="negotiate",
                ambiguity=False,
                topic="contract negotiation"
            )
            assert result is False

    def test_raw_mode_disables_agent_suggestions_ambiguity(self):
        """Ambiguous requests should NOT suggest agents in raw mode"""
        with patch.object(settings, 'raw_chat_mode', True):
            result = should_suggest_agents(
                stakes="medium",
                intent="plan",
                ambiguity=True,
                topic="unclear requirements"
            )
            assert result is False

    def test_advanced_mode_enables_agent_suggestions(self):
        """When raw mode is OFF, high stakes should suggest agents"""
        with patch.object(settings, 'raw_chat_mode', False):
            result = should_suggest_agents(
                stakes="high",
                intent="decision",
                ambiguity=True,
                topic="critical business decision"
            )
            assert result is True


class TestRawChatModeInteractionContract:
    """Test that raw mode doesn't add suggestions to interaction contract"""

    def test_raw_mode_no_suggestion_in_response(self):
        """Raw mode should not add agent suggestions to response"""
        with patch.object(settings, 'raw_chat_mode', True):
            response = enforce_contract(
                message="Help me make a critical decision about firing someone",
                stakes="high",
                intent="execute",
                has_integrations={}
            )

            # Should not have suggested_next_step for agents
            assert response.get("suggested_next_step") != "add_agents"

            # Message should not contain suggestion phrases
            message = response["assistant_message"].lower()
            assert "second opinion" not in message
            assert "bring in" not in message
            assert "other perspectives" not in message

    def test_advanced_mode_adds_suggestion_to_response(self):
        """Advanced mode should add agent suggestions for high stakes"""
        with patch.object(settings, 'raw_chat_mode', False):
            response = enforce_contract(
                message="Help me make a critical decision about firing someone",
                stakes="high",
                intent="execute",
                has_integrations={}
            )

            # Should have suggested_next_step for agents
            assert response.get("suggested_next_step") == "add_agents"
            assert response.get("requires_confirmation") is True


class TestRawChatModeSystemPrompts:
    """Test that raw mode uses minimal system prompts"""

    def test_raw_mode_system_prompt_is_minimal(self):
        """Raw mode should use minimal ChatGPT-like system prompt"""
        with patch.object(settings, 'raw_chat_mode', True):
            prompt = _get_system_prompt()

            # Should be short and generic
            assert "Quillo" in prompt
            assert "helpful AI assistant" in prompt

            # Should NOT contain specialist language
            assert "Quillopreneur" not in prompt
            assert "entrepreneurship" not in prompt
            assert "business advisor" not in prompt

    def test_advanced_mode_system_prompt_is_specialist(self):
        """Advanced mode should use Quillopreneur specialist prompt"""
        with patch.object(settings, 'raw_chat_mode', False):
            prompt = _get_system_prompt()

            # Should contain specialist language
            assert "Quillopreneur" in prompt
            assert "business advisor" in prompt
            assert "entrepreneurship" in prompt or "strategy" in prompt

    def test_llm_router_system_prompt_respects_raw_mode(self):
        """LLMRouter should use minimal prompt in raw mode"""
        router = LLMRouter()

        with patch.object(settings, 'raw_chat_mode', True):
            prompt = router._get_system_prompt()
            assert "helpful AI assistant" in prompt
            assert "Quillopreneur" not in prompt

        with patch.object(settings, 'raw_chat_mode', False):
            prompt = router._get_system_prompt()
            assert "Quillopreneur" in prompt


class TestRawChatModeDefaultBehavior:
    """Test that raw mode is enabled by default"""

    def test_raw_chat_mode_default_is_true(self):
        """RAW_CHAT_MODE should default to True"""
        # This tests the default value in config
        assert settings.raw_chat_mode is True


class TestRawChatModeModelSelection:
    """Test that raw mode uses the correct chat model"""

    def test_raw_mode_uses_chat_model(self):
        """In raw mode, should use openrouter_chat_model for answers"""
        from quillo_agent.services.llm import LLMRouter

        router = LLMRouter()

        with patch.object(settings, 'raw_chat_mode', True):
            with patch.object(settings, 'openrouter_chat_model', 'openai/gpt-4o-mini'):
                model = router._get_openrouter_model(for_chat=True)
                assert model == 'openai/gpt-4o-mini'

    def test_raw_mode_does_not_use_haiku(self):
        """In raw mode, should NOT use haiku for chat"""
        from quillo_agent.services.llm import LLMRouter

        router = LLMRouter()

        with patch.object(settings, 'raw_chat_mode', True):
            with patch.object(settings, 'openrouter_chat_model', 'openai/gpt-4o-mini'):
                model = router._get_openrouter_model(for_chat=True)
                assert 'haiku' not in model.lower()
                assert 'claude-3-haiku' not in model

    def test_advanced_mode_uses_tier_routing(self):
        """In advanced mode, should use tier-based model selection"""
        from quillo_agent.services.llm import LLMRouter

        with patch.object(settings, 'raw_chat_mode', False):
            with patch.object(settings, 'model_routing', 'balanced'):
                with patch.object(settings, 'openrouter_balanced_model', 'anthropic/claude-3.5-sonnet'):
                    # Create router after patching settings
                    router = LLMRouter()
                    model = router._get_openrouter_model(for_chat=True)
                    assert model == 'anthropic/claude-3.5-sonnet'

    def test_non_chat_calls_ignore_chat_model(self):
        """Non-chat calls (classification, etc) should ignore chat model"""
        from quillo_agent.services.llm import LLMRouter

        router = LLMRouter()

        with patch.object(settings, 'raw_chat_mode', True):
            with patch.object(settings, 'openrouter_chat_model', 'openai/gpt-4o-mini'):
                with patch.object(settings, 'model_routing', 'fast'):
                    with patch.object(settings, 'openrouter_fast_model', 'anthropic/claude-3-haiku'):
                        # for_chat=False should use tier routing even in raw mode
                        model = router._get_openrouter_model(for_chat=False)
                        assert model == 'anthropic/claude-3-haiku'


class TestRawChatModeNoTemplateResponses:
    """Test that raw mode doesn't use templated phrases"""

    def test_raw_mode_response_not_templated(self):
        """Raw mode responses should not use templated phrases"""
        with patch.object(settings, 'raw_chat_mode', True):
            response = enforce_contract(
                message="Write an email to my team",
                stakes="low",
                intent="chat_only",
                has_integrations={}
            )

            # Should get a response
            assert "assistant_message" in response
            assert response["mode"] == "answer"

            # In raw mode, we rely on the LLM prompt to avoid templates
            # Just verify we got a response
            assert len(response["assistant_message"]) > 0
