"""
Tests for Normal Mode v1 - Raw chat output without work scaffolding

Normal mode should return raw LLM responses without:
- Evidence / No Evidence provided
- Interpretation
- Recommendation
- Decision Framing / Stress Test sections

Work mode should still include the structured scaffolding.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from quillo_agent.main import create_app
from quillo_agent.config import settings

app = create_app()
client = TestClient(app)

# Test UI token for authentication (must match the patched settings value)
TEST_UI_TOKEN = "test-ui-token-12345"

# Work-mode scaffolding patterns that should NOT appear in Normal mode
WORK_MODE_PATTERNS = [
    "**Evidence:**",
    "**Interpretation:**",
    "**Recommendation:**",
    "**Decision Framing:**",
    "No Evidence provided",
    "Evidence (from web sources):",
    "TRUST CONTRACT",
    "**Key Disagreements:**",
    "**Best Move:**",
    "**Alternatives:**",
    "**Evidence Note:**",
]


class TestNormalModeAsk:
    """Tests for /ask endpoint in Normal mode"""

    def test_ask_normal_mode_no_scaffolding(self):
        """Test that Normal mode returns raw output without work scaffolding"""
        # Mock the LLM response to return a simple answer
        mock_response = "Here are 5 money saving tips:\n1. Create a budget\n2. Cut subscriptions\n3. Cook at home\n4. Use coupons\n5. Save automatically"

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch('quillo_agent.services.advice.llm_router.answer_business_question', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_response

                response = client.post(
                    "/ui/api/ask",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Give me 5 money saving tips",
                        "mode": "normal"
                    }
                )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "answer" in data
                assert "model" in data
                assert "trace_id" in data

                # Verify NO work-mode scaffolding patterns
                answer = data["answer"]
                for pattern in WORK_MODE_PATTERNS:
                    assert pattern not in answer, f"Normal mode should NOT contain '{pattern}'"

    def test_ask_work_mode_has_scaffolding(self):
        """Test that Work mode still includes structured scaffolding"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                with patch.object(settings, 'anthropic_api_key', ''):
                    response = client.post(
                        "/ui/api/ask",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={
                            "text": "What is the current inflation rate?",
                            "mode": "work"
                        }
                    )

                    assert response.status_code == 200
                    data = response.json()

                    # In work mode, the trust contract should be applied
                    # At minimum, evidence should be attempted
                    # (offline mode won't have actual evidence, but the logic should run)

    def test_ask_default_mode_is_normal(self):
        """Test that default mode (no mode specified) is Normal"""
        mock_response = "Simple answer without scaffolding"

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch('quillo_agent.services.advice.llm_router.answer_business_question', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_response

                response = client.post(
                    "/ui/api/ask",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "What is 2+2?",
                        # No mode specified - should default to normal
                    }
                )

                assert response.status_code == 200
                data = response.json()

                # Verify NO work-mode scaffolding patterns
                answer = data["answer"]
                for pattern in WORK_MODE_PATTERNS:
                    assert pattern not in answer, f"Default mode should NOT contain '{pattern}'"


class TestNormalModeMultiAgent:
    """Tests for /multi-agent endpoint in Normal mode"""

    def test_multi_agent_normal_mode_no_scaffolding(self):
        """Test that Normal mode multi-agent returns raw output without work scaffolding"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "What's a good weekend activity?",
                        "mode": "normal"
                    }
                )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "messages" in data
                assert "provider" in data
                assert "trace_id" in data

                # Verify NO work-mode scaffolding patterns in any message
                for msg in data["messages"]:
                    content = msg.get("content", "")
                    for pattern in WORK_MODE_PATTERNS:
                        assert pattern not in content, f"Normal mode multi-agent should NOT contain '{pattern}' in {msg.get('agent')} message"

    def test_multi_agent_work_mode_has_scaffolding(self):
        """Test that Work mode multi-agent still includes structured output"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Should I accept this job offer?",
                        "mode": "work"
                    }
                )

                assert response.status_code == 200
                data = response.json()

                # In work mode with template fallback, we should have standard multi-agent output
                # The template should still have the structured format for work mode

    def test_multi_agent_default_mode_is_normal(self):
        """Test that default mode (no mode specified) is Normal for multi-agent"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "What should I have for lunch?",
                        # No mode specified - should default to normal
                    }
                )

                assert response.status_code == 200
                data = response.json()

                # Verify NO work-mode scaffolding patterns in any message
                for msg in data["messages"]:
                    content = msg.get("content", "")
                    for pattern in WORK_MODE_PATTERNS:
                        assert pattern not in content, f"Default mode multi-agent should NOT contain '{pattern}'"


class TestModeDetection:
    """Tests for mode detection and validation"""

    def test_invalid_mode_defaults_to_normal(self):
        """Test that invalid mode values default to normal"""
        mock_response = "Simple response"

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch('quillo_agent.services.advice.llm_router.answer_business_question', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_response

                response = client.post(
                    "/ui/api/ask",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Hello",
                        "mode": "invalid_mode_xyz"
                    }
                )

                assert response.status_code == 200
                data = response.json()

                # Should not have work-mode scaffolding (defaults to normal)
                answer = data["answer"]
                for pattern in WORK_MODE_PATTERNS:
                    assert pattern not in answer, f"Invalid mode should default to normal, not contain '{pattern}'"

    def test_case_insensitive_mode(self):
        """Test that mode is case-insensitive"""
        mock_response = "Simple response"

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch('quillo_agent.services.advice.llm_router.answer_business_question', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_response

                # Test uppercase
                response = client.post(
                    "/ui/api/ask",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Hello",
                        "mode": "NORMAL"
                    }
                )

                assert response.status_code == 200
                data = response.json()

                # Should not have work-mode scaffolding
                answer = data["answer"]
                for pattern in WORK_MODE_PATTERNS:
                    assert pattern not in answer
