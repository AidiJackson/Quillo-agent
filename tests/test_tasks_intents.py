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


# Task Scope v1 Tests

def test_scope_auto_generated_when_not_provided():
    """Test that scope fields are auto-generated when not provided"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Review quarterly financials"
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify scope fields exist
        assert "scope_will_do" in data
        assert "scope_wont_do" in data
        assert "scope_done_when" in data

        # Verify they are not empty
        assert data["scope_will_do"] is not None
        assert data["scope_wont_do"] is not None
        assert data["scope_done_when"] is not None
        assert len(data["scope_will_do"]) > 0
        assert len(data["scope_wont_do"]) > 0
        assert len(data["scope_done_when"]) > 0


def test_scope_wont_do_contains_safety_bullets():
    """Test that scope_wont_do contains safety guardrails"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Analyze market trends"
            }
        )
        assert response.status_code == 200
        data = response.json()

        wont_do = data["scope_wont_do"]
        assert isinstance(wont_do, list)

        # Check for expected safety bullets
        wont_do_text = " ".join(wont_do).lower()
        assert "won't send messages" in wont_do_text or "won't contact" in wont_do_text
        assert "won't log into accounts" in wont_do_text or "won't make purchases" in wont_do_text


def test_scope_keyword_shaping_email():
    """Test that email-related keywords add specific scope bullets"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Draft email reply to client inquiry"
            }
        )
        assert response.status_code == 200
        data = response.json()

        will_do = data["scope_will_do"]
        assert isinstance(will_do, list)

        # Should contain message-related bullet
        will_do_text = " ".join(will_do).lower()
        assert "message" in will_do_text or "reply" in will_do_text or "draft" in will_do_text


def test_scope_keyword_shaping_summarize():
    """Test that summarize keywords add specific scope bullets"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Summarize email thread from team"
            }
        )
        assert response.status_code == 200
        data = response.json()

        will_do = data["scope_will_do"]
        assert isinstance(will_do, list)

        # Should contain summarize-related bullet
        will_do_text = " ".join(will_do).lower()
        assert "summarize" in will_do_text or "extract" in will_do_text or "action items" in will_do_text


def test_scope_keyword_shaping_negotiate():
    """Test that negotiate/argue keywords add specific scope bullets"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Prepare negotiation case for contract renewal"
            }
        )
        assert response.status_code == 200
        data = response.json()

        will_do = data["scope_will_do"]
        assert isinstance(will_do, list)

        # Should contain case/negotiation-related bullet
        will_do_text = " ".join(will_do).lower()
        assert "case" in will_do_text or "structured" in will_do_text or "options" in will_do_text


def test_scope_max_five_bullets_enforced():
    """Test that scope lists enforce max 5 bullets"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                # Intent with multiple keywords that could trigger many bullets
                "intent_text": "Draft email reply to summarize negotiation case for contract renewal"
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify max 5 bullets for will_do and wont_do
        assert len(data["scope_will_do"]) <= 5
        assert len(data["scope_wont_do"]) <= 5


def test_scope_custom_values_accepted():
    """Test that custom scope values can be provided instead of auto-generation"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        custom_will_do = ["Custom action 1", "Custom action 2"]
        custom_wont_do = ["Custom constraint 1"]
        custom_done_when = "Custom completion criteria"

        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Custom scope test",
                "scope_will_do": custom_will_do,
                "scope_wont_do": custom_wont_do,
                "scope_done_when": custom_done_when
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify custom values were used
        assert data["scope_will_do"] == custom_will_do
        assert data["scope_wont_do"] == custom_wont_do
        assert data["scope_done_when"] == custom_done_when


def test_scope_returned_in_list_endpoint():
    """Test that scope fields are returned in list endpoint"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create a task intent
        create_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Test scope in list",
                "user_key": "scope-list-test-user"
            }
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        # List task intents
        list_response = client.get(
            "/ui/api/tasks/intents?user_key=scope-list-test-user",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert list_response.status_code == 200
        data = list_response.json()

        # Find our created intent
        matching_item = next(item for item in data if item["id"] == created_id)

        # Verify scope fields are present
        assert "scope_will_do" in matching_item
        assert "scope_wont_do" in matching_item
        assert "scope_done_when" in matching_item
        assert matching_item["scope_will_do"] is not None
        assert len(matching_item["scope_will_do"]) > 0


# Approval Mode Snapshot v1 Tests

def test_approval_mode_defaults_to_plan_then_auto():
    """Test that approval_mode defaults to plan_then_auto when no prefs exist"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Test approval mode default",
                "user_key": "approval-default-test-user"
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify approval_mode is present and defaults to plan_then_auto
        assert "approval_mode" in data
        assert data["approval_mode"] == "plan_then_auto"


def test_approval_mode_snapshots_current_pref():
    """Test that approval_mode is snapshotted from current user prefs"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # First, set user prefs to confirm_every_step
        prefs_response = client.post(
            "/ui/api/prefs?user_key=approval-snapshot-test-user",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "approval_mode": "confirm_every_step"
            }
        )
        assert prefs_response.status_code == 200

        # Now create a task intent
        task_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Test approval mode snapshot",
                "user_key": "approval-snapshot-test-user"
            }
        )
        assert task_response.status_code == 200
        task_data = task_response.json()

        # Verify the task has the snapshotted approval_mode
        assert task_data["approval_mode"] == "confirm_every_step"


def test_approval_mode_snapshot_is_immutable():
    """Test that changing user prefs doesn't affect existing tasks"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Set initial prefs to plan_then_auto
        client.post(
            "/ui/api/prefs?user_key=approval-immutable-test-user",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "approval_mode": "plan_then_auto"
            }
        )

        # Create first task with plan_then_auto
        task1_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "First task",
                "user_key": "approval-immutable-test-user"
            }
        )
        assert task1_response.status_code == 200
        task1_id = task1_response.json()["id"]
        assert task1_response.json()["approval_mode"] == "plan_then_auto"

        # Update prefs to auto_lowrisk_confirm_highrisk
        client.post(
            "/ui/api/prefs?user_key=approval-immutable-test-user",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "approval_mode": "auto_lowrisk_confirm_highrisk"
            }
        )

        # Create second task with new pref value
        task2_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Second task",
                "user_key": "approval-immutable-test-user"
            }
        )
        assert task2_response.status_code == 200
        task2_id = task2_response.json()["id"]
        assert task2_response.json()["approval_mode"] == "auto_lowrisk_confirm_highrisk"

        # List tasks and verify first task still has original approval_mode
        list_response = client.get(
            "/ui/api/tasks/intents?user_key=approval-immutable-test-user",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert list_response.status_code == 200
        tasks = list_response.json()

        task1 = next(t for t in tasks if t["id"] == task1_id)
        task2 = next(t for t in tasks if t["id"] == task2_id)

        # Verify task1 still has plan_then_auto (unchanged)
        assert task1["approval_mode"] == "plan_then_auto"
        # Verify task2 has auto_lowrisk_confirm_highrisk (new pref)
        assert task2["approval_mode"] == "auto_lowrisk_confirm_highrisk"


def test_approval_mode_returned_in_list_endpoint():
    """Test that approval_mode is returned in list endpoint"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create a task intent
        create_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Test approval mode in list",
                "user_key": "approval-list-test-user"
            }
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        # List task intents
        list_response = client.get(
            "/ui/api/tasks/intents?user_key=approval-list-test-user",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert list_response.status_code == 200
        data = list_response.json()

        # Find our created intent
        matching_item = next(item for item in data if item["id"] == created_id)

        # Verify approval_mode field is present
        assert "approval_mode" in matching_item
        assert matching_item["approval_mode"] is not None
