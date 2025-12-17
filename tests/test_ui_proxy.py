"""
Tests for UI Proxy (BFF) endpoints
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from quillo_agent.main import create_app
from quillo_agent.config import settings

app = create_app()
client = TestClient(app)

# Test UI token
TEST_UI_TOKEN = "test-ui-token-12345"


def test_ui_health_no_auth_required():
    """Test that /ui/api/health does not require authentication"""
    response = client.get("/ui/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "quillo-ui-proxy"


def test_ui_route_without_token_in_prod_mode():
    """Test that /ui/api/route requires X-UI-Token in prod mode"""
    with patch.object(settings, 'app_env', 'prod'):
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            response = client.post(
                "/ui/api/route",
                json={
                    "text": "Test message",
                    "user_id": "test-user"
                }
            )
            assert response.status_code == 401
            assert "X-UI-Token" in response.json()["detail"]


def test_ui_route_with_invalid_token():
    """Test that /ui/api/route rejects invalid X-UI-Token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/route",
            headers={"X-UI-Token": "invalid-token"},
            json={
                "text": "Test message",
                "user_id": "test-user"
            }
        )
        assert response.status_code == 403
        assert "Invalid" in response.json()["detail"]


def test_ui_route_with_valid_token():
    """Test that /ui/api/route works with valid X-UI-Token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/route",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "Rewrite this email professionally",
                "user_id": "test-user"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data
        assert "reasons" in data


def test_ui_route_dev_mode_bypass():
    """Test that /ui/api/route allows requests in dev mode without token"""
    with patch.object(settings, 'app_env', 'dev'):
        with patch.object(settings, 'quillo_ui_token', ''):  # No token configured
            response = client.post(
                "/ui/api/route",
                json={
                    "text": "Rewrite this email",
                    "user_id": "test-user"
                }
            )
            # Should work in dev mode even without token
            assert response.status_code == 200


def test_ui_plan_with_valid_token():
    """Test that /ui/api/plan works with valid X-UI-Token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent": "response",
                "user_id": "test-user",
                "slots": {"outcome": "Defuse"},
                "text": "Handle this email"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
        assert "trace_id" in data
        assert isinstance(data["steps"], list)


def test_ui_ask_with_valid_token():
    """Test that /ui/api/ask works with valid X-UI-Token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/ask",
            headers={"X-UI-Token": TEST_UI_TOKEN},
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


def test_ui_ask_without_token():
    """Test that /ui/api/ask requires authentication"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/ask",
            json={
                "text": "How do I start a business?"
            }
        )
        assert response.status_code == 401


def test_ui_memory_profile_get_with_token():
    """Test that /ui/api/memory/profile GET works with valid token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.get(
            "/ui/api/memory/profile?user_id=test-user",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert response.status_code == 200
        data = response.json()
        assert "profile_md" in data
        assert "updated_at" in data


def test_ui_memory_profile_post_with_token():
    """Test that /ui/api/memory/profile POST works with valid token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/memory/profile",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "user_id": "test-user",
                "profile_md": "# Updated Profile\n\nNew content here."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "profile_md" in data
        assert "Updated Profile" in data["profile_md"]


def test_ui_feedback_with_token():
    """Test that /ui/api/feedback works with valid token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/feedback",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "user_id": "test-user",
                "tool": "response_generator",
                "outcome": True,
                "signals": {"confidence": 0.95}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True


def test_ui_endpoints_without_api_key():
    """
    Test that UI proxy endpoints do NOT require QUILLO_API_KEY.
    This is the key security improvement - frontend never sends API keys.
    """
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Make sure we're not sending Authorization header, only X-UI-Token
        response = client.post(
            "/ui/api/route",
            headers={"X-UI-Token": TEST_UI_TOKEN},  # No Authorization header!
            json={
                "text": "Test message",
                "user_id": "test-user"
            }
        )
        # Should work without API key (uses UI token instead)
        assert response.status_code == 200


def test_original_api_still_requires_api_key():
    """
    Test that original /route endpoint still requires API key.
    The UI proxy doesn't replace backend API - both coexist.
    """
    # Try calling /route without API key (not /ui/api/route)
    response = client.post(
        "/route",
        json={
            "text": "Test message",
            "user_id": "test-user"
        }
    )
    # Should fail without API key
    assert response.status_code in [401, 403]
