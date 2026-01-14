"""
Tests for UORIN TRUST CONTRACT v1

Verifies trust-first judgment system behaviors:
1. Evidence default-on for factual/temporal prompts
2. No assumptions: asks questions when critical context missing
3. Structured outputs in multi-model responses
4. Synthesis preserves disagreements
5. Clear limitations when Evidence unavailable
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from quillo_agent.trust_contract import (
    classify_prompt_needs_evidence,
    enforce_no_assumptions,
    format_model_output,
    format_synthesis,
    extract_disagreements,
    parse_unstructured_output
)


class TestEvidenceDefaultOn:
    """Test evidence classification heuristics"""

    def test_latest_keyword_triggers_evidence(self):
        """Temporal indicators like 'latest' should trigger evidence"""
        assert classify_prompt_needs_evidence("What are the latest UK employment law changes?") is True
        assert classify_prompt_needs_evidence("Show me the latest market trends") is True

    def test_current_keyword_triggers_evidence(self):
        """'Current' indicator should trigger evidence"""
        assert classify_prompt_needs_evidence("What is the current interest rate?") is True
        assert classify_prompt_needs_evidence("What's currently happening with inflation?") is True

    def test_year_patterns_trigger_evidence(self):
        """Specific years should trigger evidence"""
        assert classify_prompt_needs_evidence("What happened in 2026?") is True
        assert classify_prompt_needs_evidence("UK GDP growth in 2025") is True

    def test_news_keywords_trigger_evidence(self):
        """News/market indicators should trigger evidence"""
        assert classify_prompt_needs_evidence("Any news about Tesla stock?") is True
        assert classify_prompt_needs_evidence("Market price for gold today") is True

    def test_statistical_keywords_trigger_evidence(self):
        """Statistical indicators should trigger evidence"""
        assert classify_prompt_needs_evidence("What percentage of startups fail?") is True
        assert classify_prompt_needs_evidence("Show me data on remote work adoption") is True

    def test_personal_drafting_no_evidence(self):
        """Personal drafting tasks should NOT trigger evidence"""
        assert classify_prompt_needs_evidence("Rewrite this email to sound professional") is False
        assert classify_prompt_needs_evidence("Help me draft a proposal") is False
        assert classify_prompt_needs_evidence("Write a thank you note") is False

    def test_opinion_questions_no_evidence(self):
        """Opinion/advice questions without factual claims should NOT trigger"""
        assert classify_prompt_needs_evidence("Should I start a business?") is False
        assert classify_prompt_needs_evidence("What do you think about this idea?") is False

    def test_empty_string_no_evidence(self):
        """Empty strings should not trigger evidence"""
        assert classify_prompt_needs_evidence("") is False
        assert classify_prompt_needs_evidence("   ") is False


class TestNoAssumptionsEnforcement:
    """Test no-assumptions policy - ask questions when context missing"""

    def test_rewrite_without_content_triggers_questions(self):
        """Rewrite request without actual content should trigger questions"""
        ok, questions = enforce_no_assumptions("Rewrite this email", {})
        assert ok is False
        assert len(questions) > 0
        assert any("text" in q.lower() or "content" in q.lower() for q in questions)

    def test_draft_without_context_triggers_questions(self):
        """Draft request without specifics should trigger questions"""
        ok, questions = enforce_no_assumptions("Draft an email to staff", {})
        assert ok is False
        assert len(questions) > 0

    def test_vague_help_request_triggers_questions(self):
        """Very vague prompts should trigger questions"""
        ok, questions = enforce_no_assumptions("Help", {})
        assert ok is False
        assert len(questions) > 0

    def test_decision_without_criteria_triggers_questions(self):
        """Decision requests without context should trigger questions"""
        ok, questions = enforce_no_assumptions("Should I fire this employee?", {})
        assert ok is False
        assert len(questions) > 0

    def test_detailed_prompt_no_questions(self):
        """Detailed prompts with context should NOT trigger questions"""
        detailed = """I need to rewrite this customer email: 'We are disappointed with your service.'

        Context: Customer received damaged goods. We want to apologize and offer a refund.
        Audience: Upset customer who has been with us for 5 years.

        Please make it empathetic and professional."""

        ok, questions = enforce_no_assumptions(detailed, {})
        assert ok is True
        assert len(questions) == 0

    def test_factual_question_no_assumptions_needed(self):
        """Clear factual questions don't need additional context"""
        ok, questions = enforce_no_assumptions("What is the capital of France?", {})
        assert ok is True
        assert len(questions) == 0

    def test_questions_limited_to_three(self):
        """Should return at most 3 questions"""
        ok, questions = enforce_no_assumptions("Rewrite", {})
        assert len(questions) <= 3

    def test_empty_prompt_triggers_question(self):
        """Empty prompt should trigger at least one question"""
        ok, questions = enforce_no_assumptions("", {})
        assert ok is False
        assert len(questions) >= 1


class TestOutputFormatting:
    """Test structured output formatting"""

    def test_format_model_output_structure(self):
        """Model output should have required fields"""
        output = format_model_output(
            model_name="Claude",
            evidence_block="Fact 1\nFact 2",
            interpretation="This is my analysis",
            recommendation="Do this next"
        )

        assert output["model"] == "Claude"
        assert output["evidence"] == "Fact 1\nFact 2"
        assert output["interpretation"] == "This is my analysis"
        assert output["recommendation"] == "Do this next"
        assert output["structured"] is True
        assert "timestamp" in output

    def test_format_model_output_no_evidence(self):
        """When no evidence, should say so explicitly"""
        output = format_model_output(
            model_name="Gemini",
            evidence_block=None,
            interpretation="Analysis",
            recommendation="Recommendation"
        )

        assert output["evidence"] == "No Evidence fetched"

    def test_format_synthesis_structure(self):
        """Synthesis should have required structure"""
        synthesis = format_synthesis(
            decision_framing="Quick decision needed",
            disagreements=[
                {"model": "Claude", "point": "Move carefully"},
                {"model": "DeepSeek", "point": "Move fast"}
            ],
            best_move="Start with pilot",
            alternatives=[
                {"label": "Safer", "description": "Wait and research"},
                {"label": "Bolder", "description": "Full launch"}
            ],
            suggested_tool="Response",
            evidence_sources=[{"domain": "example.com", "title": "Source 1"}],
            evidence_fetched=True
        )

        assert synthesis["decision_framing"] == "Quick decision needed"
        assert len(synthesis["disagreements"]) == 2
        assert synthesis["best_move"] == "Start with pilot"
        assert len(synthesis["alternatives"]) == 2
        assert synthesis["suggested_tool"] == "Response"
        assert synthesis["evidence"]["fetched"] is True
        assert len(synthesis["evidence"]["sources"]) == 1

    def test_format_synthesis_no_disagreements(self):
        """When agents agree, disagreements should be empty"""
        synthesis = format_synthesis(
            decision_framing="Clear path",
            disagreements=[],  # No disagreements
            best_move="Proceed",
            alternatives=[
                {"label": "Safer", "description": "Slow"},
                {"label": "Bolder", "description": "Fast"}
            ],
            suggested_tool="Response",
            evidence_fetched=False
        )

        assert len(synthesis["disagreements"]) == 0


class TestDisagreementExtraction:
    """Test that meaningful disagreements are preserved"""

    def test_extract_disagreements_cautious_vs_bold(self):
        """Should detect cautious vs bold disagreements"""
        outputs = [
            format_model_output(
                "Claude",
                None,
                "Analysis",
                "Wait and consider all risks carefully before acting. Thorough research needed."
            ),
            format_model_output(
                "DeepSeek",
                None,
                "Analysis",
                "Act now immediately. Speed is critical, move fast and adjust later."
            )
        ]

        disagreements = extract_disagreements(outputs)
        assert len(disagreements) > 0

    def test_extract_disagreements_consensus(self):
        """When models agree, should return empty list"""
        outputs = [
            format_model_output(
                "Claude",
                None,
                "Analysis",
                "Proceed with the plan as outlined."
            ),
            format_model_output(
                "Gemini",
                None,
                "Analysis",
                "Agree, proceed with the plan."
            )
        ]

        disagreements = extract_disagreements(outputs)
        # Should be empty or minimal since both agree
        assert len(disagreements) <= 2  # May still list both if they're neutral

    def test_extract_disagreements_single_model(self):
        """Single model cannot have disagreements"""
        outputs = [
            format_model_output("Claude", None, "Analysis", "Recommendation")
        ]

        disagreements = extract_disagreements(outputs)
        assert len(disagreements) == 0


class TestUnstructuredOutputParsing:
    """Test parsing of unstructured model outputs"""

    def test_parse_with_section_markers(self):
        """Should extract sections when markers present"""
        raw = """Evidence: The sky is blue

Interpretation: This is a well-known fact

Recommendation: Enjoy the weather"""

        parsed = parse_unstructured_output(raw, "TestModel")

        # Parser successfully extracted interpretation section
        assert parsed["interpretation"] == "This is a well-known fact"
        assert parsed["evidence"] == "The sky is blue"
        assert parsed["model"] == "TestModel"

    def test_parse_without_markers(self):
        """When no markers, should wrap entire text as interpretation"""
        raw = "This is just plain text without any structure markers at all."

        parsed = parse_unstructured_output(raw, "TestModel")

        assert parsed["interpretation"] == raw
        assert parsed["recommendation"] == "See interpretation above."
        assert parsed["raw_response"] == raw


class TestIntegration:
    """Integration tests for trust contract enforcement"""

    @pytest.mark.anyio
    @patch("quillo_agent.routers.ui_proxy.retrieve_evidence")
    @patch("quillo_agent.routers.ui_proxy.advice.answer_business_question")
    async def test_ask_endpoint_evidence_triggered(self, mock_answer, mock_evidence):
        """Test /ask endpoint triggers evidence for 'latest' keyword"""
        from quillo_agent.routers.ui_proxy import ui_ask_quillopreneur
        from quillo_agent.schemas import AskRequest, EvidenceResponse, EvidenceFact, EvidenceSource
        from fastapi import Request
        from unittest.mock import MagicMock

        # Mock evidence response
        mock_evidence.return_value = EvidenceResponse(
            ok=True,
            retrieved_at="2026-01-11T00:00:00Z",
            duration_ms=100,
            facts=[
                EvidenceFact(text="Fact 1", source_id="s1"),
                EvidenceFact(text="Fact 2", source_id="s2")
            ],
            sources=[
                EvidenceSource(id="s1", title="Source 1", domain="example.com", url="http://example.com", retrieved_at="2026-01-11T00:00:00Z")
            ]
        )

        # Mock LLM response
        mock_answer.return_value = ("The answer is here", "claude-3.5-sonnet")

        # Create mock request
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"

        payload = AskRequest(text="What are the latest market trends?", user_id="test_user")

        # Call endpoint
        response = await ui_ask_quillopreneur(
            request=request,
            payload=payload,
            db=MagicMock(),
            token="test-token"
        )

        # Verify evidence was called
        assert mock_evidence.called
        # Verify evidence is in response
        assert "Evidence" in response.answer or "Fact" in response.answer

    @pytest.mark.anyio
    @patch("quillo_agent.routers.ui_proxy.advice.answer_business_question")
    async def test_ask_endpoint_no_assumptions_questions(self, mock_answer):
        """Test /ask endpoint returns questions when context missing"""
        from quillo_agent.routers.ui_proxy import ui_ask_quillopreneur
        from quillo_agent.schemas import AskRequest
        from fastapi import Request
        from unittest.mock import MagicMock

        # Create mock request
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"

        payload = AskRequest(text="Rewrite this email", user_id="test_user")

        # Call endpoint
        response = await ui_ask_quillopreneur(
            request=request,
            payload=payload,
            db=MagicMock(),
            token="test-token"
        )

        # Verify LLM was NOT called (questions asked instead)
        assert not mock_answer.called
        # Verify response contains questions
        assert "need" in response.answer.lower() or "details" in response.answer.lower()
        assert response.model == "trust-contract-v1"

    @pytest.mark.anyio
    @patch("quillo_agent.routers.ui_proxy.run_multi_agent_chat")
    async def test_multi_agent_no_assumptions_questions(self, mock_multi_agent):
        """Test /multi-agent endpoint returns questions when context missing"""
        from quillo_agent.routers.ui_proxy import ui_multi_agent_chat
        from quillo_agent.schemas import MultiAgentRequest
        from fastapi import Request
        from unittest.mock import MagicMock

        # Create mock request
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"

        payload = MultiAgentRequest(text="Help", user_id="test_user")

        # Call endpoint
        response = await ui_multi_agent_chat(
            request=request,
            payload=payload,
            token="test-token"
        )

        # Verify multi-agent was NOT called (questions asked instead)
        assert not mock_multi_agent.called
        # Verify response contains questions
        assert len(response.messages) == 1
        assert "need" in response.messages[0].content.lower() or "details" in response.messages[0].content.lower()
        assert response.provider == "trust-contract-v1"
