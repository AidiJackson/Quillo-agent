"""
Tests for offline mode (no AI API keys configured)

Verifies that all endpoints work correctly without OPENROUTER_API_KEY or ANTHROPIC_API_KEY.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from quillo_agent.main import create_app
from quillo_agent.config import settings, is_offline_mode

app = create_app()
client = TestClient(app)


def test_is_offline_mode_true_when_no_keys():
    """Test is_offline_mode returns True when no API keys configured"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            assert is_offline_mode() is True


def test_is_offline_mode_false_when_openrouter_key():
    """Test is_offline_mode returns False when OpenRouter key is set"""
    with patch.object(settings, 'openrouter_api_key', 'test-key'):
        with patch.object(settings, 'anthropic_api_key', ''):
            assert is_offline_mode() is False


def test_is_offline_mode_false_when_anthropic_key():
    """Test is_offline_mode returns False when Anthropic key is set"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', 'test-key'):
            assert is_offline_mode() is False


def test_route_offline_mode_returns_200():
    """Test /ui/api/route works in offline mode without API keys"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            with patch.object(settings, 'app_env', 'dev'):
                with patch.object(settings, 'quillo_ui_token', ''):
                    response = client.post(
                        "/ui/api/route",
                        json={
                            "text": "Please rewrite this email professionally",
                            "user_id": "test-user"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "intent" in data
                    assert "reasons" in data
                    assert data["intent"] in ["response", "rewrite", "argue", "clarity", "unknown"]


def test_route_offline_deterministic_output():
    """Test /ui/api/route returns deterministic output in offline mode"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            with patch.object(settings, 'app_env', 'dev'):
                with patch.object(settings, 'quillo_ui_token', ''):
                    response1 = client.post(
                        "/ui/api/route",
                        json={
                            "text": "Rewrite this email",
                            "user_id": "test-user"
                        }
                    )
                    response2 = client.post(
                        "/ui/api/route",
                        json={
                            "text": "Rewrite this email",
                            "user_id": "test-user"
                        }
                    )
                    assert response1.status_code == 200
                    assert response2.status_code == 200
                    assert response1.json()["intent"] == response2.json()["intent"]


def test_plan_offline_mode_returns_200():
    """Test /ui/api/plan works in offline mode without API keys"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            with patch.object(settings, 'app_env', 'dev'):
                with patch.object(settings, 'quillo_ui_token', ''):
                    response = client.post(
                        "/ui/api/plan",
                        json={
                            "intent": "response",
                            "user_id": "test-user",
                            "slots": {"outcome": "Defuse"},
                            "text": "Handle this difficult client email"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "steps" in data
                    assert "trace_id" in data
                    assert isinstance(data["steps"], list)
                    assert len(data["steps"]) > 0


def test_plan_offline_deterministic_steps():
    """Test /ui/api/plan returns deterministic steps in offline mode"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            with patch.object(settings, 'app_env', 'dev'):
                with patch.object(settings, 'quillo_ui_token', ''):
                    response1 = client.post(
                        "/ui/api/plan",
                        json={
                            "intent": "rewrite",
                            "user_id": "test-user",
                            "text": "Rewrite this"
                        }
                    )
                    response2 = client.post(
                        "/ui/api/plan",
                        json={
                            "intent": "rewrite",
                            "user_id": "test-user",
                            "text": "Rewrite this"
                        }
                    )
                    assert response1.status_code == 200
                    assert response2.status_code == 200
                    steps1 = [s["tool"] for s in response1.json()["steps"]]
                    steps2 = [s["tool"] for s in response2.json()["steps"]]
                    assert steps1 == steps2


def test_execute_offline_mode_returns_200():
    """Test /ui/api/execute works in offline mode without API keys"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            with patch.object(settings, 'app_env', 'dev'):
                with patch.object(settings, 'quillo_ui_token', ''):
                    response = client.post(
                        "/ui/api/execute",
                        json={
                            "intent": "response",
                            "user_id": "test-user",
                            "text": "Draft a reply to this client",
                            "slots": {},
                            "plan_steps": [
                                {"tool": "response_generator", "premium": False, "rationale": "Generate response"}
                            ],
                            "dry_run": True
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "output_text" in data
                    assert "artifacts" in data
                    assert "trace_id" in data
                    assert "provider_used" in data


def test_execute_offline_provider_is_template():
    """Test /ui/api/execute returns provider='template' in offline mode"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            with patch.object(settings, 'app_env', 'dev'):
                with patch.object(settings, 'quillo_ui_token', ''):
                    response = client.post(
                        "/ui/api/execute",
                        json={
                            "intent": "response",
                            "user_id": "test-user",
                            "text": "Test execution",
                            "slots": {},
                            "plan_steps": [
                                {"tool": "response_generator", "premium": False, "rationale": "Test"}
                            ],
                            "dry_run": True
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["provider_used"] == "template"


def test_ask_offline_mode_returns_200():
    """Test /ui/api/ask works in offline mode without API keys"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            with patch.object(settings, 'app_env', 'dev'):
                with patch.object(settings, 'quillo_ui_token', ''):
                    response = client.post(
                        "/ui/api/ask",
                        json={
                            "text": "How do I start a business?",
                            "user_id": "test-user"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "answer" in data
                    assert "model" in data
                    assert "trace_id" in data
                    assert len(data["answer"]) > 0


def test_ask_offline_model_is_template():
    """Test /ui/api/ask returns model='template' in offline mode"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            with patch.object(settings, 'app_env', 'dev'):
                with patch.object(settings, 'quillo_ui_token', ''):
                    response = client.post(
                        "/ui/api/ask",
                        json={
                            "text": "What is a good marketing strategy?",
                            "user_id": "test-user"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["model"] == "template"


def test_health_works_in_offline_mode():
    """Test /ui/api/health works regardless of API key configuration"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            response = client.get("/ui/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
