"""
Tests for Tasks Module v1 - Task Intent endpoints
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


def test_create_task_intent_success():
    """Test creating a task intent succeeds with valid token"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Review quarterly financials and prepare summary",
                "origin_chat_id": "chat-123",
                "user_key": "user-456"
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "status" in data
        assert "intent_text" in data
        assert "origin_chat_id" in data
        assert "user_key" in data

        # Verify values
        assert data["intent_text"] == "Review quarterly financials and prepare summary"
        assert data["origin_chat_id"] == "chat-123"
        assert data["user_key"] == "user-456"
        assert data["status"] == "approved"  # Default status


def test_create_task_intent_minimal():
    """Test creating a task intent with only required field (intent_text)"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Send follow-up emails to prospects"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["intent_text"] == "Send follow-up emails to prospects"
        assert data["origin_chat_id"] is None
        assert data["user_key"] is None
        assert data["status"] == "approved"


def test_create_task_intent_empty_text_validation():
    """Test that empty intent_text is rejected"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": ""
            }
        )
        # Should fail validation with 400 Bad Request
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()


def test_create_task_intent_missing_text_validation():
    """Test that missing intent_text is rejected"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "origin_chat_id": "chat-123"
            }
        )
        # Should fail Pydantic validation
        assert response.status_code == 422


def test_list_task_intents_returns_created():
    """Test that list endpoint returns created task intents"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create a task intent
        create_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Test task for listing",
                "user_key": "list-test-user"
            }
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        # List task intents for this user
        list_response = client.get(
            "/ui/api/tasks/intents?user_key=list-test-user",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert list_response.status_code == 200
        data = list_response.json()

        # Verify it's a list
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify our created intent is in the list
        intent_ids = [item["id"] for item in data]
        assert created_id in intent_ids

        # Verify the matching item has correct data
        matching_item = next(item for item in data if item["id"] == created_id)
        assert matching_item["intent_text"] == "Test task for listing"
        assert matching_item["user_key"] == "list-test-user"


def test_list_task_intents_global():
    """Test that list without user_key returns global recent intents"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create a task intent
        create_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Global test task"
            }
        )
        assert create_response.status_code == 200

        # List all recent intents (no user_key filter)
        list_response = client.get(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert list_response.status_code == 200
        data = list_response.json()

        # Verify it's a list
        assert isinstance(data, list)
        # Should have at least the one we just created
        assert len(data) > 0


def test_list_task_intents_respects_limit():
    """Test that limit parameter is respected"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # List with limit=1
        response = client.get(
            "/ui/api/tasks/intents?limit=1",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert response.status_code == 200
        data = response.json()

        # Should return at most 1 item
        assert len(data) <= 1


def test_create_task_intent_requires_auth():
    """Test that create endpoint requires authentication"""
    with patch.object(settings, 'app_env', 'prod'):
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            response = client.post(
                "/ui/api/tasks/intents",
                json={
                    "intent_text": "Test task"
                }
            )
            # Should fail without token
            assert response.status_code == 401


def test_list_task_intents_requires_auth():
    """Test that list endpoint requires authentication"""
    with patch.object(settings, 'app_env', 'prod'):
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            response = client.get("/ui/api/tasks/intents")
            # Should fail without token
            assert response.status_code == 401


def test_task_intent_status_defaults_to_approved():
    """Test that newly created task intents have status=approved by default"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Status test task"
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify status is approved
        assert data["status"] == "approved"
