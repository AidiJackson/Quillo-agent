"""
Tests for Quillo Interaction Contract v1

Verifies behavioral compliance:
- Low stakes: no confirmation required
- Medium stakes: confirmation required
- High stakes: confirmation required
- Missing integration: returns cannot_do_yet with alternatives
- No chain-of-thought leakage
"""
import pytest
from quillo_agent.services.interaction_contract import (
    enforce_contract,
    validate_no_leakage,
    ActionIntent,
    Stakes,
    FORBIDDEN_PHRASES
)


class TestStakesBasedConfirmation:
    """Test stakes-aware confirmation behavior."""

    def test_low_stakes_no_confirmation(self):
        """Low stakes requests should not require confirmation."""
        result = enforce_contract(
            message="What's the best way to structure an email?",
            stakes="low",
            intent="chat_only",
            has_integrations={}
        )

        assert result["mode"] == "answer"
        assert result["requires_confirmation"] is False
        assert result["assistant_message"] is not None
        assert len(result["questions"]) == 0

    def test_medium_stakes_requires_confirmation(self):
        """Medium stakes requests should require confirmation."""
        result = enforce_contract(
            message="Draft a professional email to the client about the delay",
            stakes="medium",
            intent="execute",
            has_integrations={"email": True}
        )

        assert result["mode"] == "confirm_required"
        assert result["requires_confirmation"] is True
        assert "Want me to proceed?" in result["assistant_message"]

    def test_high_stakes_requires_confirmation(self):
        """High stakes requests should require confirmation."""
        result = enforce_contract(
            message="Draft a termination letter for the underperforming employee",
            stakes="high",
            intent="execute",
            has_integrations={}
        )

        assert result["mode"] == "confirm_required"
        assert result["requires_confirmation"] is True
        assert "Want me to proceed?" in result["assistant_message"]


class TestMissingIntegrations:
    """Test missing integration handling."""

    def test_email_integration_missing(self):
        """Should return cannot_do_yet for missing email integration."""
        result = enforce_contract(
            message="Check my inbox for urgent emails",
            stakes="medium",
            intent="external_integration",
            has_integrations={"email": False}
        )

        assert result["mode"] == "cannot_do_yet"
        assert result["requires_confirmation"] is False
        assert "can't pull your inbox yet" in result["assistant_message"]
        assert result["suggested_next_step"] is not None
        assert "paste" in result["suggested_next_step"].lower()

    def test_calendar_integration_missing(self):
        """Should return cannot_do_yet for missing calendar integration."""
        result = enforce_contract(
            message="Show me my calendar for this week",
            stakes="low",
            intent="external_integration",
            has_integrations={"calendar": False}
        )

        assert result["mode"] == "cannot_do_yet"
        assert "can't access your calendar yet" in result["assistant_message"]
        assert result["suggested_next_step"] is not None

    def test_crm_integration_missing(self):
        """Should return cannot_do_yet for missing CRM integration."""
        result = enforce_contract(
            message="Pull up my client contacts",
            stakes="low",
            intent="external_integration",
            has_integrations={"crm": False}
        )

        assert result["mode"] == "cannot_do_yet"
        assert "can't access your CRM yet" in result["assistant_message"]
        assert result["suggested_next_step"] is not None


class TestClarificationQuestions:
    """Test clarifying question behavior."""

    def test_vague_request_requires_clarification(self):
        """Very short, vague requests should trigger clarification."""
        result = enforce_contract(
            message="Do it",
            stakes="low",
            intent="execute",
            has_integrations={}
        )

        assert result["mode"] == "clarify"
        assert len(result["questions"]) > 0
        assert "specifically" in result["assistant_message"].lower()

    def test_missing_recipient_requires_clarification(self):
        """Send requests without recipient should trigger clarification."""
        result = enforce_contract(
            message="Send the proposal document",
            stakes="medium",
            intent="execute",
            has_integrations={}
        )

        assert result["mode"] == "clarify"
        assert len(result["questions"]) > 0
        assert any("who" in q.lower() for q in result["questions"])

    def test_overly_broad_scope_requires_clarification(self):
        """Requests with 'all' or 'every' should trigger clarification."""
        result = enforce_contract(
            message="Send emails to all my clients",
            stakes="high",
            intent="external_integration",
            has_integrations={"email": True}
        )

        assert result["mode"] == "clarify"
        assert len(result["questions"]) > 0


class TestNoChainOfThoughtLeakage:
    """Test that forbidden phrases don't appear in responses."""

    def test_low_stakes_no_leakage(self):
        """Low stakes responses should not leak internal reasoning."""
        result = enforce_contract(
            message="Help me write a quick thank you note",
            stakes="low",
            intent="execute",
            has_integrations={}
        )

        message = result["assistant_message"].lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in message, f"Forbidden phrase '{phrase}' found in: {result['assistant_message']}"

    def test_medium_stakes_no_leakage(self):
        """Medium stakes responses should not leak internal reasoning."""
        result = enforce_contract(
            message="Draft a professional response to client feedback",
            stakes="medium",
            intent="execute",
            has_integrations={}
        )

        message = result["assistant_message"].lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in message, f"Forbidden phrase '{phrase}' found in: {result['assistant_message']}"

    def test_high_stakes_no_leakage(self):
        """High stakes responses should not leak internal reasoning."""
        result = enforce_contract(
            message="Negotiate the contract terms with legal",
            stakes="high",
            intent="plan",
            has_integrations={}
        )

        message = result["assistant_message"].lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in message, f"Forbidden phrase '{phrase}' found in: {result['assistant_message']}"

    def test_cannot_do_yet_no_leakage(self):
        """Cannot do yet responses should not leak internal reasoning."""
        result = enforce_contract(
            message="Check my inbox",
            stakes="low",
            intent="external_integration",
            has_integrations={"email": False}
        )

        message = result["assistant_message"].lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in message, f"Forbidden phrase '{phrase}' found in: {result['assistant_message']}"

    def test_validate_no_leakage_function(self):
        """Test the validate_no_leakage helper function."""
        # Clean text should pass
        assert validate_no_leakage("Got it. I'll help you with that.") is True

        # Text with forbidden phrases should raise ValueError
        with pytest.raises(ValueError, match="Contract violation"):
            validate_no_leakage("Let me think about this internally...")

        with pytest.raises(ValueError, match="Contract violation"):
            validate_no_leakage("Here's my chain-of-thought analysis...")


class TestConversationalTone:
    """Test conversational operator tone."""

    def test_chat_only_uses_operator_tone(self):
        """Chat-only requests should use warm operator phrases."""
        result = enforce_contract(
            message="What are the key points to include in a business proposal?",
            stakes="low",
            intent="chat_only",
            has_integrations={}
        )

        message = result["assistant_message"].lower()
        # Should use conversational starters like "got it", "here's what", etc.
        assert any(phrase in message for phrase in ["got it", "here's what", "here's"])

    def test_execute_uses_action_language(self):
        """Execute requests should use action-oriented language."""
        result = enforce_contract(
            message="Draft a response to the customer complaint",
            stakes="low",
            intent="execute",
            has_integrations={}
        )

        message = result["assistant_message"].lower()
        # Should use action phrases like "I'll", "On it"
        assert any(phrase in message for phrase in ["i'll", "on it"])

    def test_confirmation_prompt_present(self):
        """Medium/high stakes should have 'Want me to proceed?' prompt."""
        result = enforce_contract(
            message="Send the contract to the vendor",
            stakes="medium",
            intent="execute",
            has_integrations={}
        )

        assert "Want me to proceed?" in result["assistant_message"]


class TestActionIntentHandling:
    """Test different action intent scenarios."""

    def test_chat_only_intent(self):
        """Chat-only intent should provide answer without execution."""
        result = enforce_contract(
            message="How should I structure a cold email?",
            stakes="low",
            intent="chat_only",
            has_integrations={}
        )

        assert result["mode"] in ["answer", "clarify"]
        assert result["assistant_message"] is not None

    def test_plan_intent(self):
        """Plan intent should offer strategic guidance."""
        result = enforce_contract(
            message="What's the best strategy for reaching out to investors?",
            stakes="medium",
            intent="plan",
            has_integrations={}
        )

        assert result["mode"] in ["confirm_required", "answer"]
        assert "suggest" in result["assistant_message"].lower()

    def test_execute_intent(self):
        """Execute intent should prepare for action."""
        result = enforce_contract(
            message="Create a follow-up email to the prospect",
            stakes="low",
            intent="execute",
            has_integrations={}
        )

        assert result["mode"] in ["answer", "clarify"]
        assert "i'll" in result["assistant_message"].lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_integrations_dict(self):
        """Should handle empty integrations dict gracefully."""
        result = enforce_contract(
            message="Help me draft an email",
            stakes="low",
            intent="execute",
            has_integrations={}
        )

        assert result["mode"] in ["answer", "clarify"]
        assert result["assistant_message"] is not None

    def test_none_integrations(self):
        """Should handle None integrations gracefully."""
        result = enforce_contract(
            message="Help me draft an email",
            stakes="low",
            intent="execute",
            has_integrations=None
        )

        assert result["mode"] in ["answer", "clarify"]
        assert result["assistant_message"] is not None

    def test_all_integrations_available(self):
        """Should work normally when all integrations are available."""
        result = enforce_contract(
            message="Check my inbox and calendar",
            stakes="medium",
            intent="external_integration",
            has_integrations={"email": True, "calendar": True}
        )

        # Should not be cannot_do_yet since integrations are available
        assert result["mode"] in ["confirm_required", "answer", "clarify"]

    def test_very_long_message(self):
        """Should handle very long messages."""
        long_message = "Draft an email to the client " + "about the project status " * 50
        result = enforce_contract(
            message=long_message,
            stakes="medium",
            intent="execute",
            has_integrations={}
        )

        assert result["mode"] in ["confirm_required", "answer", "clarify"]
        assert result["assistant_message"] is not None


class TestResponseStructure:
    """Test that response structure is always correct."""

    def test_response_has_all_required_fields(self):
        """All responses should have required fields."""
        result = enforce_contract(
            message="Help me with this task",
            stakes="low",
            intent="chat_only",
            has_integrations={}
        )

        assert "mode" in result
        assert "assistant_message" in result
        assert "questions" in result
        assert "requires_confirmation" in result
        assert "suggested_next_step" in result

    def test_questions_is_list(self):
        """Questions field should always be a list."""
        result = enforce_contract(
            message="Help me with this task",
            stakes="low",
            intent="chat_only",
            has_integrations={}
        )

        assert isinstance(result["questions"], list)

    def test_requires_confirmation_is_bool(self):
        """requires_confirmation should always be a boolean."""
        result = enforce_contract(
            message="Help me with this task",
            stakes="low",
            intent="chat_only",
            has_integrations={}
        )

        assert isinstance(result["requires_confirmation"], bool)
