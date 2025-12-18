"""
Tests for Judgment Explanation Layer

Validates stake assessment, explanation generation, and response tone.
"""
import pytest
from fastapi.testclient import TestClient
from quillo_agent.services.judgment import (
    assess_stakes,
    build_explanation,
    format_for_user
)
from quillo_agent.main import create_app


class TestStakeAssessment:
    """Test stake level assessment logic"""

    def test_high_stakes_conflict_keywords(self):
        """High stakes: multiple conflict-related keywords"""
        text = "I need to fire someone on my team who has been underperforming. This is urgent and I'm concerned about legal issues."
        stakes = assess_stakes(text)
        assert stakes == "high", "Should detect high stakes with conflict + legal + urgent keywords"

    def test_high_stakes_negotiation(self):
        """High stakes: negotiation and money keywords"""
        text = "I'm negotiating a salary increase and need to be very careful about how I approach this. The compensation discussion is critical."
        stakes = assess_stakes(text)
        assert stakes == "high", "Should detect high stakes with negotiation + money keywords"

    def test_high_stakes_long_emotional(self):
        """High stakes: long text with emotional content"""
        text = """
        I'm really upset about what happened in the meeting today. A team member
        publicly criticized my decision in front of the entire leadership team,
        and now I'm concerned about how this affects my credibility. I need to
        respond but I'm worried that if I come across as too defensive, it will
        make things worse. At the same time, if I don't address it, people might
        think I agree with the criticism. This is a complex situation and I need
        help crafting the right response that asserts my position without escalating
        the conflict further.
        """
        stakes = assess_stakes(text)
        assert stakes == "high", "Should detect high stakes for long emotional text"

    def test_medium_stakes_professional_email(self):
        """Medium stakes: professional business communication"""
        text = "I need to write an email to a client about a project delay. It's a professional situation and I want to maintain the relationship."
        stakes = assess_stakes(text)
        assert stakes == "medium", "Should detect medium stakes for professional business communication"

    def test_medium_stakes_team_feedback(self):
        """Medium stakes: team performance feedback"""
        text = "I need to give feedback to my team member about their presentation performance in the meeting."
        stakes = assess_stakes(text)
        assert stakes == "medium", "Should detect medium stakes for team feedback"

    def test_low_stakes_simple_rewrite(self):
        """Low stakes: simple rewrite request"""
        text = "Can you rewrite this paragraph to make it clearer?"
        stakes = assess_stakes(text)
        assert stakes == "low", "Should detect low stakes for simple rewrite"

    def test_low_stakes_question(self):
        """Low stakes: short informational question"""
        text = "What is the best way to structure a business proposal?"
        stakes = assess_stakes(text)
        assert stakes == "low", "Should detect low stakes for short question"

    def test_low_stakes_explanation_request(self):
        """Low stakes: explanation request"""
        text = "Please explain how the quarterly review process works"
        stakes = assess_stakes(text)
        assert stakes == "low", "Should detect low stakes for explanation request"


class TestExplanationBuilding:
    """Test explanation generation and formatting"""

    def test_low_stakes_no_why_it_matters(self):
        """Low stakes explanations should omit 'why_it_matters'"""
        explanation = build_explanation(
            context="a simple rewrite request",
            stakes="low",
            recommendation="rewrite the text for clarity"
        )
        assert explanation["why_it_matters"] is None, "Low stakes should not include 'why_it_matters'"
        assert "what_i_see" in explanation
        assert "recommendation" in explanation
        assert "requires_confirmation" in explanation

    def test_medium_stakes_includes_why_it_matters(self):
        """Medium stakes explanations should include 'why_it_matters'"""
        explanation = build_explanation(
            context="a professional email to a client",
            stakes="medium",
            recommendation="draft a clear, professional response"
        )
        assert explanation["why_it_matters"] is not None, "Medium stakes should include 'why_it_matters'"
        assert "professional" in explanation["why_it_matters"].lower() or "clear" in explanation["why_it_matters"].lower()

    def test_high_stakes_includes_why_it_matters(self):
        """High stakes explanations should include 'why_it_matters'"""
        explanation = build_explanation(
            context="a team conflict situation",
            stakes="high",
            recommendation="carefully draft a response"
        )
        assert explanation["why_it_matters"] is not None, "High stakes should include 'why_it_matters'"
        assert len(explanation["why_it_matters"]) > 0

    def test_low_stakes_no_confirmation(self):
        """Low stakes should not require confirmation by default"""
        explanation = build_explanation(
            context="a simple task",
            stakes="low",
            recommendation="handle this directly"
        )
        assert explanation["requires_confirmation"] is False, "Low stakes should not require confirmation"

    def test_high_stakes_requires_confirmation(self):
        """High stakes should require confirmation by default"""
        explanation = build_explanation(
            context="a critical decision",
            stakes="high",
            recommendation="proceed carefully"
        )
        assert explanation["requires_confirmation"] is True, "High stakes should require confirmation"

    def test_confirmation_override(self):
        """Should respect explicit confirmation override"""
        explanation = build_explanation(
            context="a task",
            stakes="low",
            recommendation="handle this",
            requires_confirmation=True
        )
        assert explanation["requires_confirmation"] is True, "Should respect explicit confirmation requirement"


class TestResponseTone:
    """Test human-readable, conversational tone"""

    def test_no_chain_of_thought_leakage(self):
        """Explanations should not expose internal reasoning"""
        explanation = build_explanation(
            context="a business email",
            stakes="medium",
            recommendation="draft a professional response"
        )

        # Check for technical/internal terms that shouldn't appear
        forbidden_terms = [
            "classifier", "LLM", "model", "probability", "score",
            "algorithm", "heuristic", "confidence", "token"
        ]

        full_text = " ".join([
            explanation["what_i_see"],
            explanation.get("why_it_matters", ""),
            explanation["recommendation"]
        ]).lower()

        for term in forbidden_terms:
            assert term not in full_text, f"Should not expose internal term: {term}"

    def test_conversational_observation(self):
        """'What I'm seeing' should be conversational"""
        explanation = build_explanation(
            context="a request for help with a difficult email",
            stakes="medium",
            recommendation="draft the email"
        )
        assert "what i'm seeing" in explanation["what_i_see"].lower(), "Should use conversational phrasing"

    def test_recommendation_clarity(self):
        """Recommendations should be clear and actionable"""
        explanation = build_explanation(
            context="a team issue",
            stakes="high",
            recommendation="draft multiple versions of the response"
        )
        rec = explanation["recommendation"]
        assert len(rec) > 10, "Recommendation should be substantive"
        assert rec.strip()[-1] in [".", "?", "!"], "Recommendation should end with punctuation"


class TestFormatting:
    """Test user-facing message formatting"""

    def test_format_includes_all_parts(self):
        """Formatted message should include all relevant parts"""
        explanation = build_explanation(
            context="a professional email",
            stakes="medium",
            recommendation="draft a response"
        )
        formatted = format_for_user(explanation)

        assert explanation["what_i_see"] in formatted
        assert explanation["recommendation"] in formatted
        if explanation["why_it_matters"]:
            assert explanation["why_it_matters"] in formatted

    def test_format_includes_confirmation_prompt(self):
        """Formatted message should include confirmation prompt when required"""
        explanation = build_explanation(
            context="a critical decision",
            stakes="high",
            recommendation="proceed with caution"
        )
        formatted = format_for_user(explanation)

        assert "want me to proceed" in formatted.lower(), "Should include confirmation prompt"

    def test_format_no_confirmation_when_not_required(self):
        """Formatted message should not include confirmation prompt when not required"""
        explanation = build_explanation(
            context="a simple task",
            stakes="low",
            recommendation="handle this"
        )
        formatted = format_for_user(explanation)

        assert "want me to proceed" not in formatted.lower(), "Should not include confirmation prompt"


class TestRealWorldScenarios:
    """Test with realistic user inputs"""

    def test_team_firing_scenario(self):
        """Real scenario: firing a team member"""
        text = "I need to let go of a team member who hasn't been meeting expectations. This is going to be a difficult conversation."
        stakes = assess_stakes(text)
        assert stakes == "high"

        explanation = build_explanation(
            context="a difficult termination conversation",
            stakes=stakes,
            recommendation="prepare a respectful but clear termination script"
        )
        assert explanation["why_it_matters"] is not None
        assert explanation["requires_confirmation"] is True

    def test_client_update_scenario(self):
        """Real scenario: client project update"""
        text = "I need to send a project status update to our client"
        stakes = assess_stakes(text)
        assert stakes in ["low", "medium"]

        explanation = build_explanation(
            context="a client project update",
            stakes=stakes,
            recommendation="draft a clear status update"
        )
        # Should work for either stakes level
        assert "what_i_see" in explanation

    def test_simple_grammar_fix(self):
        """Real scenario: simple text fix"""
        text = "Fix the grammar in this sentence"
        stakes = assess_stakes(text)
        assert stakes == "low"

        explanation = build_explanation(
            context="a grammar correction request",
            stakes=stakes,
            recommendation="correct the grammar"
        )
        assert explanation["why_it_matters"] is None
        assert explanation["requires_confirmation"] is False


class TestJudgmentEndpoint:
    """Integration tests for the /judgment endpoint"""

    def setup_method(self):
        """Set up test client"""
        app = create_app()
        self.client = TestClient(app)
        self.test_api_key = "dev-test-key-12345"

    def test_judgment_endpoint_high_stakes(self):
        """Test /judgment endpoint with high stakes input"""
        response = self.client.post(
            "/judgment",
            json={
                "text": "I need to fire a team member. This is urgent and I'm concerned about how to handle it.",
                "user_id": "test_user"
            },
            headers={"Authorization": f"Bearer {self.test_api_key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stakes"] == "high"
        assert data["requires_confirmation"] is True
        assert data["why_it_matters"] is not None
        assert "what i'm seeing" in data["what_i_see"].lower()
        assert len(data["formatted_message"]) > 0

    def test_judgment_endpoint_low_stakes(self):
        """Test /judgment endpoint with low stakes input"""
        response = self.client.post(
            "/judgment",
            json={
                "text": "Can you rewrite this paragraph for clarity?",
                "user_id": "test_user"
            },
            headers={"Authorization": f"Bearer {self.test_api_key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stakes"] == "low"
        assert data["requires_confirmation"] is False
        assert data["why_it_matters"] is None

    def test_judgment_endpoint_with_intent(self):
        """Test /judgment endpoint with intent provided"""
        response = self.client.post(
            "/judgment",
            json={
                "text": "Help me respond to this angry client email",
                "user_id": "test_user",
                "intent": "response"
            },
            headers={"Authorization": f"Bearer {self.test_api_key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stakes"] in ["medium", "high"]
        assert "response" in data["what_i_see"].lower()
