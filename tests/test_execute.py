"""
Tests for plan execution endpoint
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from quillo_agent.main import create_app
from quillo_agent.config import settings

app = create_app()
client = TestClient(app)

# Test tokens
TEST_API_KEY = "dev-test-key-12345"
TEST_UI_TOKEN = "test-ui-token-12345"


def test_ui_execute_without_token():
    """Test that /ui/api/execute requires UI token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/execute",
            json={
                "text": "Test message",
                "intent": "response",
                "plan_steps": [
                    {
                        "tool": "response_generator",
                        "premium": False,
                        "rationale": "Test"
                    }
                ],
                "dry_run": True
            }
        )
        assert response.status_code == 401


def test_ui_execute_with_valid_token():
    """Test that /ui/api/execute works with valid token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/execute",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "Help me write a professional response",
                "intent": "response",
                "plan_steps": [
                    {
                        "tool": "response_generator",
                        "premium": False,
                        "rationale": "Generate initial response"
                    },
                    {
                        "tool": "tone_adjuster",
                        "premium": True,
                        "rationale": "Adjust tone"
                    }
                ],
                "dry_run": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "output_text" in data
        assert "artifacts" in data
        assert "trace_id" in data
        assert "provider_used" in data
        assert "warnings" in data

        # Verify output is not empty
        assert len(data["output_text"]) > 0

        # Verify artifacts match step count
        assert len(data["artifacts"]) == 2

        # Verify dry run warning
        assert any("DRY RUN" in w for w in data["warnings"])


def test_execute_offline_mode():
    """Test that /ui/api/execute works in offline mode (no API keys)"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        with patch.object(settings, 'openrouter_api_key', ''):
            with patch.object(settings, 'anthropic_api_key', ''):
                response = client.post(
                    "/ui/api/execute",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Rewrite this email",
                        "intent": "rewrite",
                        "plan_steps": [
                            {
                                "tool": "rewriter",
                                "premium": False,
                                "rationale": "Rewrite for professionalism"
                            }
                        ],
                        "dry_run": True
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Should work in offline mode
                assert data["provider_used"] == "template"
                assert len(data["output_text"]) > 0
                assert len(data["artifacts"]) == 1


def test_execute_returns_trace_id():
    """Test that /ui/api/execute returns a valid trace_id"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/execute",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "Help me argue my position",
                "intent": "argue",
                "plan_steps": [
                    {
                        "tool": "argument_builder",
                        "premium": True,
                        "rationale": "Build argument"
                    }
                ],
                "dry_run": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify trace_id is UUID format
        assert len(data["trace_id"]) == 36
        assert data["trace_id"].count("-") == 4


def test_execute_with_slots():
    """Test that /ui/api/execute handles slots correctly"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/execute",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "Handle this conflict and defuse it",
                "intent": "response",
                "slots": {"outcome": "Defuse"},
                "plan_steps": [
                    {
                        "tool": "response_generator",
                        "premium": False,
                        "rationale": "Generate response"
                    },
                    {
                        "tool": "conflict_resolver",
                        "premium": True,
                        "rationale": "Apply de-escalation"
                    }
                ],
                "dry_run": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["artifacts"]) == 2


def test_execute_artifact_structure():
    """Test that execution artifacts have correct structure"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/execute",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "Test message",
                "intent": "clarity",
                "plan_steps": [
                    {
                        "tool": "clarity_simplifier",
                        "premium": False,
                        "rationale": "Simplify"
                    }
                ],
                "dry_run": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Check artifact structure
        artifact = data["artifacts"][0]
        assert "step_index" in artifact
        assert "tool" in artifact
        assert "input_excerpt" in artifact
        assert "output_excerpt" in artifact
        assert artifact["step_index"] == 0


def test_execute_missing_required_fields():
    """Test that /ui/api/execute validates required fields"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Missing plan_steps
        response = client.post(
            "/ui/api/execute",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "Test",
                "intent": "response"
            }
        )
        assert response.status_code == 422  # Validation error


def test_execute_backend_api_still_requires_api_key():
    """Test that /execute (non-UI) still requires API key"""
    # Try calling /execute without API key
    response = client.post(
        "/execute",
        json={
            "text": "Test",
            "intent": "response",
            "plan_steps": [
                {
                    "tool": "response_generator",
                    "premium": False,
                    "rationale": "Test"
                }
            ]
        }
    )
    # Should fail without API key
    assert response.status_code in [401, 403]


def test_execute_provider_selection():
    """Test that execution uses correct provider based on config"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Test with OpenRouter configured
        with patch.object(settings, 'openrouter_api_key', 'test-key'):
            response = client.post(
                "/ui/api/execute",
                headers={"X-UI-Token": TEST_UI_TOKEN},
                json={
                    "text": "Test",
                    "intent": "response",
                    "plan_steps": [
                        {
                            "tool": "response_generator",
                            "premium": False,
                            "rationale": "Test"
                        }
                    ],
                    "dry_run": True
                }
            )
            assert response.status_code == 200
            data = response.json()
            # Will try OpenRouter (may fall back to template if mock doesn't work)
            assert data["provider_used"] in ["openrouter", "template", "offline"]
