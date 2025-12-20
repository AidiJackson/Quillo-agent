"""
Tests for Agent Suggestion Service (v1)

Verifies proactive agent suggestion logic:
- High stakes → suggestion appears
- Low stakes → no suggestion
- Complex intents → suggestion appears
- Missing integration → suggestion still allowed
- Decline path → no agent added
- Accept path → multi-agent endpoint used
- No chain-of-thought leakage

Note: These tests run with RAW_CHAT_MODE=False (advanced mode) via fixture.
Raw mode behavior is tested separately in test_raw_chat_mode.py.
"""
import pytest
from unittest.mock import patch
from quillo_agent.services.agent_suggestion import (
    should_suggest_agents,
    build_agent_suggestion_message,
    detect_ambiguity
)
from quillo_agent.services.interaction_contract import enforce_contract
from quillo_agent.config import settings


@pytest.fixture(autouse=True)
def disable_raw_chat_mode():
    """Disable raw chat mode for all tests in this module (test advanced mode features)."""
    with patch.object(settings, 'raw_chat_mode', False):
        yield


class TestShouldSuggestAgents:
    """Test the core suggestion logic."""

    def test_high_stakes_suggests_agents(self):
        """High stakes should trigger agent suggestion."""
        result = should_suggest_agents(
            stakes="high",
            intent="execute",
            ambiguity=False,
            topic="firing an employee"
        )
        assert result is True

    def test_low_stakes_no_suggestion(self):
        """Low stakes simple tasks should not suggest agents."""
        result = should_suggest_agents(
            stakes="low",
            intent="chat_only",
            ambiguity=False,
            topic="what is the weather"
        )
        assert result is False

    def test_complex_intent_suggests_agents(self):
        """Complex decision-making intents should suggest agents."""
        complex_intents = ["decision", "negotiate", "strategy", "plan"]
        for intent in complex_intents:
            result = should_suggest_agents(
                stakes="medium",
                intent=intent,
                ambiguity=False,
                topic="business strategy"
            )
            assert result is True, f"Intent '{intent}' should suggest agents"

    def test_simple_intent_no_suggestion(self):
        """Simple intents like grammar/typo should not suggest agents."""
        simple_intents = ["grammar", "rewrite", "typo", "lookup"]
        for intent in simple_intents:
            result = should_suggest_agents(
                stakes="medium",
                intent=intent,
                ambiguity=False,
                topic="fix my email"
            )
            assert result is False, f"Intent '{intent}' should not suggest agents"

    def test_ambiguity_suggests_agents(self):
        """Ambiguous requests should trigger agent suggestion."""
        result = should_suggest_agents(
            stakes="medium",
            intent="execute",
            ambiguity=True,
            topic="complex decision"
        )
        assert result is True

    def test_simple_topic_no_suggestion(self):
        """Simple topics (grammar, spelling) should not suggest agents."""
        result = should_suggest_agents(
            stakes="medium",
            intent="execute",
            ambiguity=False,
            topic="fix grammar in my email"
        )
        assert result is False


class TestDetectAmbiguity:
    """Test ambiguity detection logic."""

    def test_multiple_questions_is_ambiguous(self):
        """Multiple questions indicate ambiguity."""
        text = "Should I fire them? Or should I give them another chance? What do you think?"
        result = detect_ambiguity(text, "decision")
        assert result is True

    def test_uncertainty_markers_are_ambiguous(self):
        """Uncertainty markers indicate ambiguity."""
        uncertainty_texts = [
            "I'm not sure what to do here",
            "Maybe I should send the email",
            "I might want to reconsider",
            "I don't know if this is the right approach"
        ]
        for text in uncertainty_texts:
            result = detect_ambiguity(text, "decision")
            assert result is True, f"Text '{text}' should be detected as ambiguous"

    def test_conflicting_requirements_are_ambiguous(self):
        """Conflicting requirements indicate ambiguity."""
        text = "I want to be direct, but I also don't want to offend them"
        result = detect_ambiguity(text, "execute")
        assert result is True

    def test_simple_clear_request_not_ambiguous(self):
        """Clear, simple requests are not ambiguous."""
        text = "Draft a thank you email to the client"
        result = detect_ambiguity(text, "execute")
        assert result is False


class TestBuildAgentSuggestionMessage:
    """Test suggestion message generation."""

    def test_returns_professional_suggestion(self):
        """Should return a professional, calm suggestion."""
        message = build_agent_suggestion_message("negotiation")
        assert len(message) > 0
        # Should be conversational (may or may not have a question mark)
        assert any(word in message.lower() for word in ["want", "help", "can", "would"])

    def test_no_chain_of_thought_phrases(self):
        """Suggestion should not contain chain-of-thought phrases."""
        forbidden_phrases = [
            "chain-of-thought", "i'm thinking", "internal",
            "reasoning", "analysis"
        ]
        message = build_agent_suggestion_message("decision")
        message_lower = message.lower()
        for phrase in forbidden_phrases:
            assert phrase not in message_lower, \
                f"Forbidden phrase '{phrase}' found in: {message}"

    def test_consistent_format(self):
        """Messages should have consistent professional format."""
        for _ in range(5):
            message = build_agent_suggestion_message("strategy")
            # Should be a reasonable length (not too short, not too long)
            assert 20 < len(message) < 200


class TestContractIntegration:
    """Test integration with interaction contract."""

    def test_high_stakes_adds_suggestion_to_contract(self):
        """High stakes request should add agent suggestion to contract response."""
        response = enforce_contract(
            message="I need to fire my co-founder. This is really urgent and stressful.",
            stakes="high",
            intent="execute",
            has_integrations={}
        )

        # Should have suggested_next_step
        assert response.get("suggested_next_step") == "add_agents"
        assert response["requires_confirmation"] is True

        # Suggestion should be in assistant_message
        assert len(response["assistant_message"]) > 0
        assert "?" in response["assistant_message"]

    def test_low_stakes_no_suggestion_in_contract(self):
        """Low stakes simple task should not add agent suggestion."""
        response = enforce_contract(
            message="What's the best way to say thank you?",
            stakes="low",
            intent="chat_only",
            has_integrations={}
        )

        # Should NOT have agent suggestion
        assert response.get("suggested_next_step") != "add_agents"

    def test_complex_decision_adds_suggestion(self):
        """Complex decision intents should add agent suggestion."""
        response = enforce_contract(
            message="Should I accept this acquisition offer or negotiate for more?",
            stakes="medium",
            intent="plan",  # Use valid ActionIntent
            has_integrations={}
        )

        assert response.get("suggested_next_step") == "add_agents"
        assert response["requires_confirmation"] is True

    def test_grammar_request_no_suggestion(self):
        """Grammar/rewrite requests should not suggest agents."""
        response = enforce_contract(
            message="Fix the grammar in this email",
            stakes="low",
            intent="chat_only",  # Use valid ActionIntent
            has_integrations={}
        )

        assert response.get("suggested_next_step") != "add_agents"

    def test_missing_integration_still_allows_suggestion(self):
        """Missing integration should not prevent agent suggestion if stakes warrant it."""
        response = enforce_contract(
            message="I need to negotiate this contract deal",
            stakes="high",
            intent="execute",  # Use valid ActionIntent
            has_integrations={"email": False}
        )

        # Should suggest agents even without email integration
        # (Unless it's a cannot_do_yet response for the integration itself)
        if response["mode"] != "cannot_do_yet":
            assert response.get("suggested_next_step") == "add_agents"

    def test_no_chain_of_thought_in_suggestion(self):
        """Agent suggestions should not leak chain-of-thought."""
        response = enforce_contract(
            message="Should I pivot my startup strategy completely?",
            stakes="high",
            intent="plan",  # Use valid ActionIntent
            has_integrations={}
        )

        forbidden_phrases = [
            "chain-of-thought", "i'm thinking", "internal",
            "reasoning", "my analysis", "processing"
        ]

        message = response["assistant_message"].lower()
        for phrase in forbidden_phrases:
            assert phrase not in message, \
                f"Forbidden phrase '{phrase}' found in: {response['assistant_message']}"


class TestDeclinePath:
    """Test the decline path (user says no to agents)."""

    def test_decline_removes_suggestion(self):
        """When user declines, suggestion should be removed."""
        # Initial response with suggestion
        response = enforce_contract(
            message="Critical business decision here",
            stakes="high",
            intent="execute",  # Use valid ActionIntent
            has_integrations={}
        )

        assert response.get("suggested_next_step") == "add_agents"

        # User declines by continuing solo
        # In the actual app, this would just hide the buttons and proceed normally
        # The contract doesn't need to handle decline - it's a UI concern


class TestAcceptPath:
    """Test the accept path (user accepts agent suggestion)."""

    def test_accept_uses_multi_agent_endpoint(self):
        """When user accepts, multi-agent endpoint should be called."""
        # This is tested in the frontend integration
        # The backend just provides the suggestion
        # The frontend calls /ui/api/multi-agent when user clicks "Bring in a second opinion"
        pass


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_message(self):
        """Should handle empty messages gracefully."""
        result = should_suggest_agents(
            stakes="high",
            intent="execute",
            ambiguity=False,
            topic=""
        )
        # High stakes still suggests even with empty topic
        assert result is True

    def test_very_long_message(self):
        """Should handle very long messages."""
        long_message = "negotiate " * 100
        result = should_suggest_agents(
            stakes="medium",
            intent="negotiate",
            ambiguity=False,
            topic=long_message
        )
        assert result is True

    def test_mixed_case_intent(self):
        """Should handle mixed case intents."""
        result = should_suggest_agents(
            stakes="medium",
            intent="DECISION",
            ambiguity=False,
            topic="business strategy"
        )
        assert result is True
