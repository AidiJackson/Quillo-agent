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


# Task Plan v2 Phase 1 Tests

def test_create_plan_success():
    """Test creating a task plan succeeds with valid token and task"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # First create a task intent
        task_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Draft email reply to customer inquiry about pricing"
            }
        )
        assert task_response.status_code == 200
        task_id = task_response.json()["id"]

        # Now create a plan for this task
        plan_response = client.post(
            f"/ui/api/tasks/{task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert plan_response.status_code == 200
        plan_data = plan_response.json()

        # Verify response structure
        assert "id" in plan_data
        assert "task_intent_id" in plan_data
        assert "created_at" in plan_data
        assert "updated_at" in plan_data
        assert "plan_steps" in plan_data
        assert "summary" in plan_data
        assert "status" in plan_data

        # Verify values
        assert plan_data["task_intent_id"] == task_id
        assert plan_data["status"] == "draft"
        assert isinstance(plan_data["plan_steps"], list)
        assert len(plan_data["plan_steps"]) > 0


def test_create_plan_deterministic_output():
    """Test that plan generation produces deterministic keyword-based output"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create a task with email keywords
        task_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Reply to customer email about refund request"
            }
        )
        task_id = task_response.json()["id"]

        # Create plan
        plan_response = client.post(
            f"/ui/api/tasks/{task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert plan_response.status_code == 200
        plan_data = plan_response.json()

        # Verify email-related keywords triggered appropriate steps
        steps = plan_data["plan_steps"]
        assert len(steps) > 0

        # Summary should be present for email tasks
        assert plan_data["summary"] is not None
        summary_lower = plan_data["summary"].lower()
        assert any(kw in summary_lower for kw in ["email", "reply", "response", "draft"])


def test_create_plan_replaces_existing_idempotently():
    """Test that creating a plan multiple times replaces the previous plan (idempotent)"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create a task
        task_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Prepare quarterly report"
            }
        )
        task_id = task_response.json()["id"]

        # Create first plan
        plan1_response = client.post(
            f"/ui/api/tasks/{task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert plan1_response.status_code == 200
        plan1_id = plan1_response.json()["id"]

        # Create second plan (should replace first)
        plan2_response = client.post(
            f"/ui/api/tasks/{task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert plan2_response.status_code == 200
        plan2_id = plan2_response.json()["id"]

        # Verify it's the same plan ID (replaced, not created new)
        assert plan2_id == plan1_id

        # Verify GET returns the updated plan
        get_response = client.get(
            f"/ui/api/tasks/{task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert get_response.status_code == 200
        assert get_response.json()["id"] == plan1_id


def test_get_plan_success():
    """Test getting a plan returns correct data"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create task and plan
        task_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Analyze competitor pricing"
            }
        )
        task_id = task_response.json()["id"]

        create_plan_response = client.post(
            f"/ui/api/tasks/{task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        created_plan_id = create_plan_response.json()["id"]

        # Now GET the plan
        get_response = client.get(
            f"/ui/api/tasks/{task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert get_response.status_code == 200
        plan_data = get_response.json()

        # Verify it matches the created plan
        assert plan_data["id"] == created_plan_id
        assert plan_data["task_intent_id"] == task_id
        assert plan_data["status"] == "draft"


def test_get_plan_404_when_none_exists():
    """Test that GET plan returns 404 when no plan exists for task"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create a task but don't create a plan
        task_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "No plan for this task"
            }
        )
        task_id = task_response.json()["id"]

        # Try to GET plan that doesn't exist
        get_response = client.get(
            f"/ui/api/tasks/{task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        assert get_response.status_code == 404
        assert "No plan found" in get_response.json()["detail"]


def test_plan_steps_contract_shape():
    """Test that plan_steps have correct contract structure"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create task and plan
        task_response = client.post(
            "/ui/api/tasks/intents",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "intent_text": "Summarize research findings"
            }
        )
        task_id = task_response.json()["id"]

        plan_response = client.post(
            f"/ui/api/tasks/{task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        plan_data = plan_response.json()

        # Verify plan_steps structure
        steps = plan_data["plan_steps"]
        assert isinstance(steps, list)
        assert len(steps) > 0

        # Each step should have step_num and description
        for step in steps:
            assert "step_num" in step
            assert "description" in step
            assert isinstance(step["step_num"], int)
            assert isinstance(step["description"], str)
            assert step["step_num"] > 0
            assert len(step["description"]) > 0


def test_create_plan_requires_auth():
    """Test that create plan endpoint requires authentication"""
    with patch.object(settings, 'app_env', 'prod'):
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            # Create a task first (with auth)
            task_response = client.post(
                "/ui/api/tasks/intents",
                headers={"X-UI-Token": TEST_UI_TOKEN},
                json={
                    "intent_text": "Test auth task"
                }
            )
            task_id = task_response.json()["id"]

            # Try to create plan without auth
            response = client.post(f"/ui/api/tasks/{task_id}/plan")
            assert response.status_code == 401


def test_get_plan_requires_auth():
    """Test that get plan endpoint requires authentication"""
    with patch.object(settings, 'app_env', 'prod'):
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            # Create task and plan first (with auth)
            task_response = client.post(
                "/ui/api/tasks/intents",
                headers={"X-UI-Token": TEST_UI_TOKEN},
                json={
                    "intent_text": "Test auth task"
                }
            )
            task_id = task_response.json()["id"]

            client.post(
                f"/ui/api/tasks/{task_id}/plan",
                headers={"X-UI-Token": TEST_UI_TOKEN}
            )

            # Try to GET plan without auth
            response = client.get(f"/ui/api/tasks/{task_id}/plan")
            assert response.status_code == 401


def test_create_plan_404_for_nonexistent_task():
    """Test that creating plan for non-existent task returns 404"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        fake_task_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/ui/api/tasks/{fake_task_id}/plan",
            headers={"X-UI-Token": TEST_UI_TOKEN}
        )
        # Should fail with 404 Not Found
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
