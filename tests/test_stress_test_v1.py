"""
Tests for STRESS TEST v1 - Automatic Consequence-Detected Mode

Verifies that STRESS TEST v1 activates automatically when consequence is detected:
1. Consequence detection triggers Stress Test mode
2. Casual chat does NOT trigger Stress Test mode
3. Lens assignments are applied correctly
4. Synthesis includes required structure
5. Evidence behavior is still respected
6. Free-form chat is preserved when Stress Test not active
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from quillo_agent.trust_contract import (
    detect_consequence,
    get_lens_for_agent,
    STRESS_TEST_LENSES,
    SYNTHESIS_EXECUTION_LENS,
    format_stress_test_synthesis,
    is_valid_execution_tool
)


class TestConsequenceDetection:
    """Test consequence/decision detection heuristics"""

    def test_should_i_triggers_consequence(self):
        """'Should I' questions should trigger Stress Test"""
        assert detect_consequence("Should I fire this employee?") is True
        assert detect_consequence("Should I send this email to the client?") is True
        assert detect_consequence("Should we launch the product now?") is True

    def test_decision_framing_triggers_consequence(self):
        """Decision framing should trigger Stress Test"""
        assert detect_consequence("What's the best move here?") is True
        assert detect_consequence("Is it worth investing in this?") is True
        assert detect_consequence("I need a second opinion on this decision") is True
        assert detect_consequence("What would you do in my situation?") is True

    def test_risk_framing_triggers_consequence(self):
        """Risk/consequence framing should trigger Stress Test"""
        assert detect_consequence("Is this too risky to proceed?") is True
        assert detect_consequence("What are the legal consequences?") is True
        assert detect_consequence("Could this damage our relationship with the client?") is True
        assert detect_consequence("What's the fallout if this goes wrong?") is True

    def test_irreversible_actions_trigger_consequence(self):
        """Irreversible actions should trigger Stress Test"""
        assert detect_consequence("Should I terminate the contract?") is True
        assert detect_consequence("Ready to publish this announcement") is True
        assert detect_consequence("Should I resign from my position?") is True
        assert detect_consequence("About to sue the vendor") is True

    def test_action_verbs_trigger_consequence(self):
        """Action-implying verbs should trigger Stress Test"""
        assert detect_consequence("Should I hire this candidate?") is True
        assert detect_consequence("Do I escalate this to management?") is True
        assert detect_consequence("Can I approve this budget request?") is True

    def test_casual_chat_no_consequence(self):
        """Casual conversation should NOT trigger Stress Test"""
        assert detect_consequence("What's the weather like?") is False
        assert detect_consequence("Tell me about machine learning") is False
        assert detect_consequence("How do I write a for loop in Python?") is False

    def test_factual_questions_no_consequence(self):
        """Factual questions should NOT trigger Stress Test"""
        assert detect_consequence("What is the capital of France?") is False
        assert detect_consequence("Explain quantum computing") is False
        assert detect_consequence("What are the latest market trends?") is False

    def test_drafting_tasks_no_consequence(self):
        """Drafting tasks without decision should NOT trigger"""
        assert detect_consequence("Help me write a blog post") is False
        assert detect_consequence("Rewrite this to be more professional") is False

    def test_empty_string_no_consequence(self):
        """Empty strings should not trigger"""
        assert detect_consequence("") is False
        assert detect_consequence("   ") is False


class TestLensAssignments:
    """Test lens assignment logic"""

    def test_get_lens_for_claude(self):
        """Claude should get Risk lens"""
        lens = get_lens_for_agent("claude")
        assert lens is not None
        assert lens["name"] == "Risk Lens"
        assert "risk" in lens["focus"].lower() or "failure" in lens["focus"].lower()

    def test_get_lens_for_deepseek(self):
        """DeepSeek should get Relationship lens"""
        lens = get_lens_for_agent("deepseek")
        assert lens is not None
        assert lens["name"] == "Relationship Lens"
        assert "emotional" in lens["focus"].lower() or "politically" in lens["focus"].lower()

    def test_get_lens_for_gemini(self):
        """Gemini should get Strategy lens"""
        lens = get_lens_for_agent("gemini")
        assert lens is not None
        assert lens["name"] == "Strategy Lens"
        assert "strategy" in lens["focus"].lower() or "leverage" in lens["focus"].lower()

    def test_get_lens_for_unknown_agent(self):
        """Unknown agents should get None"""
        lens = get_lens_for_agent("unknown")
        assert lens is None

    def test_synthesis_execution_lens_exists(self):
        """Synthesis should have Execution lens"""
        assert SYNTHESIS_EXECUTION_LENS is not None
        assert SYNTHESIS_EXECUTION_LENS["name"] == "Execution Lens"
        assert "clarity" in SYNTHESIS_EXECUTION_LENS["focus"].lower() or "reversibility" in SYNTHESIS_EXECUTION_LENS["focus"].lower()


class TestStressTestSynthesis:
    """Test Stress Test synthesis structure"""

    def test_format_stress_test_synthesis_structure(self):
        """Stress Test synthesis should have required fields"""
        synthesis = format_stress_test_synthesis(
            decision_being_tested="Should I fire the underperforming manager?",
            top_risks=["Legal liability risk", "Team morale impact", "Knowledge loss"],
            disagreements=[
                {"agent": "claude", "lens": "Risk", "point": "High legal risk"},
                {"agent": "deepseek", "lens": "Relationship", "point": "Will damage trust"}
            ],
            best_move="Document performance issues first, then have direct conversation",
            safer_alternative="Extend PIP by 30 days, offer coaching",
            bolder_alternative="Terminate immediately with severance package",
            execution_tool="Response",
            evidence_used=False
        )

        assert synthesis["mode"] == "stress_test"
        assert synthesis["decision_being_tested"] == "Should I fire the underperforming manager?"
        assert len(synthesis["top_risks"]) == 3
        assert len(synthesis["disagreements"]) == 2
        assert synthesis["best_move"] is not None
        assert "safer" in synthesis["alternatives"]
        assert "bolder" in synthesis["alternatives"]
        assert synthesis["execution_tool"] == "Response"
        assert synthesis["evidence"]["used"] is False

    def test_stress_test_synthesis_no_disagreements(self):
        """Stress Test synthesis can have empty disagreements (consensus)"""
        synthesis = format_stress_test_synthesis(
            decision_being_tested="Test decision",
            top_risks=["Risk 1"],
            disagreements=[],  # Consensus
            best_move="Proceed",
            safer_alternative="Wait",
            bolder_alternative="Act now",
            execution_tool="Clarity",
            evidence_used=True,
            evidence_sources=[{"domain": "example.com", "title": "Source"}]
        )

        assert len(synthesis["disagreements"]) == 0
        assert synthesis["evidence"]["used"] is True
        assert len(synthesis["evidence"]["sources"]) == 1


class TestExecutionToolValidation:
    """Test execution tool validation"""

    def test_valid_execution_tools(self):
        """Valid tools should pass validation"""
        assert is_valid_execution_tool("Response") is True
        assert is_valid_execution_tool("Rewrite") is True
        assert is_valid_execution_tool("Argue") is True
        assert is_valid_execution_tool("Clarity") is True

    def test_invalid_execution_tools(self):
        """Invalid tools should fail validation"""
        assert is_valid_execution_tool("Invalid") is False
        assert is_valid_execution_tool("response") is False  # Case-sensitive
        assert is_valid_execution_tool("") is False


class TestStressTestIntegration:
    """Integration tests for Stress Test v1"""

    @pytest.mark.anyio
    @patch("quillo_agent.routers.ui_proxy.run_multi_agent_chat")
    async def test_multi_agent_stress_test_activated(self, mock_multi_agent):
        """Test that Stress Test is activated for consequential prompts"""
        from quillo_agent.routers.ui_proxy import ui_multi_agent_chat
        from quillo_agent.schemas import MultiAgentRequest
        from fastapi import Request
        from unittest.mock import MagicMock

        # Mock multi-agent response
        mock_multi_agent.return_value = (
            [
                {"role": "assistant", "agent": "quillo", "content": "Frame", "model_id": None, "live": True, "unavailable_reason": None},
                {"role": "assistant", "agent": "claude", "content": "Risk analysis", "model_id": "claude", "live": True, "unavailable_reason": None}
            ],
            "openrouter",
            None,
            False
        )

        # Create mock request
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"

        payload = MultiAgentRequest(
            text="Should I fire this employee for poor performance? He's been with the company 3 years, has had 2 written warnings, and missed his last 3 deadlines. Our policy requires 3 warnings before termination.",
            user_id="test_user"
        )

        # Call endpoint
        response = await ui_multi_agent_chat(
            request=request,
            payload=payload,
            token="test-token"
        )

        # Verify multi-agent was called with stress_test_mode=True
        assert mock_multi_agent.called
        call_kwargs = mock_multi_agent.call_args[1]
        assert "stress_test_mode" in call_kwargs
        assert call_kwargs["stress_test_mode"] is True

    @pytest.mark.anyio
    @patch("quillo_agent.routers.ui_proxy.run_multi_agent_chat")
    async def test_multi_agent_normal_mode_casual_chat(self, mock_multi_agent):
        """Test that Stress Test is NOT activated for casual chat"""
        from quillo_agent.routers.ui_proxy import ui_multi_agent_chat
        from quillo_agent.schemas import MultiAgentRequest
        from fastapi import Request
        from unittest.mock import MagicMock

        # Mock multi-agent response
        mock_multi_agent.return_value = (
            [
                {"role": "assistant", "agent": "quillo", "content": "Answer", "model_id": None, "live": True, "unavailable_reason": None}
            ],
            "openrouter",
            None,
            False
        )

        # Create mock request
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"

        payload = MultiAgentRequest(
            text="Explain how neural networks work",
            user_id="test_user"
        )

        # Call endpoint
        response = await ui_multi_agent_chat(
            request=request,
            payload=payload,
            token="test-token"
        )

        # Verify multi-agent was called with stress_test_mode=False
        assert mock_multi_agent.called
        call_kwargs = mock_multi_agent.call_args[1]
        assert "stress_test_mode" in call_kwargs
        assert call_kwargs["stress_test_mode"] is False

    @pytest.mark.anyio
    @patch("quillo_agent.routers.ui_proxy.retrieve_evidence")
    @patch("quillo_agent.routers.ui_proxy.run_multi_agent_chat")
    async def test_stress_test_respects_evidence_default_on(self, mock_multi_agent, mock_evidence):
        """Test that Stress Test respects evidence default-on when factual claims present"""
        from quillo_agent.routers.ui_proxy import ui_multi_agent_chat
        from quillo_agent.schemas import MultiAgentRequest, EvidenceResponse, EvidenceFact, EvidenceSource
        from fastapi import Request
        from unittest.mock import MagicMock

        # Mock evidence response
        mock_evidence.return_value = EvidenceResponse(
            ok=True,
            retrieved_at="2026-01-11T00:00:00Z",
            duration_ms=100,
            facts=[EvidenceFact(text="Recent ruling", source_id="s1")],
            sources=[EvidenceSource(id="s1", title="Source", domain="example.com", url="http://example.com", retrieved_at="2026-01-11T00:00:00Z")]
        )

        # Mock multi-agent response
        mock_multi_agent.return_value = (
            [{"role": "assistant", "agent": "quillo", "content": "Analysis", "model_id": None, "live": True, "unavailable_reason": None}],
            "openrouter",
            None,
            False
        )

        # Create mock request
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"

        # Prompt with both consequence AND factual claim (should trigger both)
        payload = MultiAgentRequest(
            text="Should I sue my former employer based on the latest employment law changes in 2026? I was terminated without cause after 5 years, and my contract had a non-compete clause. The company is now competing with my new venture.",
            user_id="test_user"
        )

        # Call endpoint
        response = await ui_multi_agent_chat(
            request=request,
            payload=payload,
            token="test-token"
        )

        # Verify both evidence AND stress test were triggered
        assert mock_evidence.called  # Evidence fetch happened
        assert mock_multi_agent.called
        call_kwargs = mock_multi_agent.call_args[1]
        assert call_kwargs["stress_test_mode"] is True  # Stress Test activated
        assert call_kwargs["evidence_context"] is not None  # Evidence provided

    @pytest.mark.anyio
    @patch("quillo_agent.routers.ui_proxy.run_multi_agent_chat")
    async def test_stress_test_blocked_by_no_assumptions(self, mock_multi_agent):
        """Test that no-assumptions check blocks Stress Test when context missing"""
        from quillo_agent.routers.ui_proxy import ui_multi_agent_chat
        from quillo_agent.schemas import MultiAgentRequest
        from fastapi import Request
        from unittest.mock import MagicMock

        # Create mock request
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"

        # Consequential prompt but missing context
        payload = MultiAgentRequest(
            text="Should I fire him?",  # Missing context: who? why?
            user_id="test_user"
        )

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
