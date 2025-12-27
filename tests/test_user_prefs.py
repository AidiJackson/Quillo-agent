"""
Tests for User Preferences Module v1 - /ui/api/prefs endpoints
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


def test_get_prefs_default_is_plan_then_auto():
    """Test that default approval_mode is plan_then_auto when prefs don't exist"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.get(
            "/ui/api/prefs?user_key=test-default-user",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "user_key" in data
        assert "approval_mode" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Verify default value
        assert data["user_key"] == "test-default-user"
        assert data["approval_mode"] == "plan_then_auto"


def test_post_prefs_updates_value():
    """Test that POST updates the approval_mode value and persists it"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create/update preferences
        response = client.post(
            "/ui/api/prefs?user_key=test-update-user",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={"approval_mode": "confirm_every_step"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify updated value
        assert data["user_key"] == "test-update-user"
        assert data["approval_mode"] == "confirm_every_step"

        # Verify persistence by getting again
        get_response = client.get(
            "/ui/api/prefs?user_key=test-update-user",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["approval_mode"] == "confirm_every_step"


def test_post_prefs_invalid_value_rejected():
    """Test that invalid approval_mode values are rejected with 422"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/prefs?user_key=test-invalid-user",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={"approval_mode": "invalid_mode"}
        )
        # Should fail validation with 422 Unprocessable Entity
        assert response.status_code == 422
        assert "invalid" in response.json()["detail"].lower()


def test_get_prefs_requires_auth():
    """Test that GET /prefs endpoint requires authentication"""
    with patch.object(settings, 'app_env', 'prod'):
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            response = client.get("/ui/api/prefs?user_key=test-auth-user")
            # Should fail without token
            assert response.status_code == 401


def test_post_prefs_requires_auth():
    """Test that POST /prefs endpoint requires authentication"""
    with patch.object(settings, 'app_env', 'prod'):
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            response = client.post(
                "/ui/api/prefs?user_key=test-auth-user",
                json={"approval_mode": "plan_then_auto"}
            )
            # Should fail without token
            assert response.status_code == 401


def test_prefs_all_valid_modes():
    """Test that all three approval modes are accepted"""
    valid_modes = ["confirm_every_step", "plan_then_auto", "auto_lowrisk_confirm_highrisk"]

    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        for mode in valid_modes:
            response = client.post(
                f"/ui/api/prefs?user_key=test-mode-{mode}",
                headers={"X-UI-Token": TEST_UI_TOKEN},
                json={"approval_mode": mode}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["approval_mode"] == mode


def test_prefs_defaults_to_global_user_key():
    """Test that user_key defaults to 'global' if not provided"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.get(
            "/ui/api/prefs",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_key"] == "global"
        assert data["approval_mode"] == "plan_then_auto"


def test_prefs_upsert_behavior():
    """Test that POST creates or updates preferences"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # First POST - creates
        response1 = client.post(
            "/ui/api/prefs?user_key=test-upsert-user",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={"approval_mode": "plan_then_auto"}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        created_at = data1["created_at"]

        # Second POST - updates
        response2 = client.post(
            "/ui/api/prefs?user_key=test-upsert-user",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={"approval_mode": "confirm_every_step"}
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # Verify same record (same created_at)
        assert data2["created_at"] == created_at
        # But different approval_mode
        assert data2["approval_mode"] == "confirm_every_step"
