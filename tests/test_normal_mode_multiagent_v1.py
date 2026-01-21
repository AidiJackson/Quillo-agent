"""
Tests for Normal Mode Multi-Agent (v1)

Verifies:
- Normal mode returns raw peer replies WITHOUT synthesis
- Normal mode does NOT include structured output (Evidence/Interpretation/Recommendation)
- Normal mode bypasses trust contract checks
- Work mode still returns structured outputs with synthesis
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import httpx

from quillo_agent.main import create_app
from quillo_agent.config import settings
from quillo_agent.services.multi_agent_chat import CLAUDE_MODEL, CHALLENGER_MODEL, GEMINI_MODEL


# Test UI token
TEST_UI_TOKEN = "test-token-12345"

# Create test client
app = create_app()
client = TestClient(app)


# Structured output markers that should NOT appear in normal mode
WORK_MODE_MARKERS = [
    "**Evidence:**",
    "**Interpretation:**",
    "**Recommendation:**",
    "**Decision Framing:**",
    "**Key Disagreements:**",
    "**Best Move:**",
    "**Alternatives:**",
    "**Evidence Note:**",
    "TRUST CONTRACT",
]

# Synthesis markers that should NOT appear in normal mode
SYNTHESIS_MARKERS = [
    "Uorin — Synthesis",
    "synthesize",
    "recommendation",
    "Decision Framing",
]


def create_mock_response(model, content):
    """Create a mock response for OpenRouter"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return mock_resp


class TestNormalModeNoSynthesis:
    """Test that normal mode returns raw peer replies without synthesis."""

    def test_normal_mode_returns_4_messages_no_synthesis(self):
        """Test that normal mode returns only 4 messages (intro + 3 peers, no synthesis)"""
        mock_responses = {
            "claude": "Here's my natural response to your question.",
            "deepseek": "I have a different perspective on this matter.",
            "gemini": "Let me give you a structured view of this.",
        }

        async def mock_post(url, *args, **kwargs):
            model = kwargs.get("json", {}).get("model", "")
            if "claude" in model.lower():
                return create_mock_response(model, mock_responses["claude"])
            elif "deepseek" in model.lower():
                return create_mock_response(model, mock_responses["deepseek"])
            elif "gemini" in model.lower():
                return create_mock_response(model, mock_responses["gemini"])
            # Should not reach synthesis for normal mode
            pytest.fail(f"Unexpected model call in normal mode: {model}")

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    response = client.post(
                        "/ui/api/multi-agent",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={
                            "text": "Write a short, polite reply declining a meeting next week.",
                            "user_id": "test-user",
                            "mode": "normal"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()

                    # Should have 4 messages (intro + Claude + DeepSeek + Gemini)
                    assert len(data["messages"]) == 4, f"Expected 4 messages but got {len(data['messages'])}"

                    # Check message order
                    agents = [msg["agent"] for msg in data["messages"]]
                    assert agents == ["quillo", "claude", "deepseek", "gemini"]

                    # Verify NO synthesis message at the end
                    last_msg = data["messages"][-1]
                    assert last_msg["agent"] == "gemini", "Last message should be Gemini (no synthesis)"

    def test_normal_mode_no_structured_output_markers(self):
        """Test that normal mode responses do NOT contain Evidence/Interpretation/Recommendation markers"""
        # Use natural responses without structured markers
        mock_responses = {
            "claude": "I think you could politely say you have prior commitments that week. Keep it simple and friendly.",
            "deepseek": "Just be direct - say you can't make it and offer an alternative time if you want.",
            "gemini": "A good approach would be to thank them for the invite, briefly explain you're unavailable, and suggest rescheduling.",
        }

        async def mock_post(url, *args, **kwargs):
            model = kwargs.get("json", {}).get("model", "")
            if "claude" in model.lower():
                return create_mock_response(model, mock_responses["claude"])
            elif "deepseek" in model.lower():
                return create_mock_response(model, mock_responses["deepseek"])
            elif "gemini" in model.lower():
                return create_mock_response(model, mock_responses["gemini"])
            # Should not reach here
            return create_mock_response(model, "Unexpected call")

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    response = client.post(
                        "/ui/api/multi-agent",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={
                            "text": "How should I respond?",
                            "user_id": "test-user",
                            "mode": "normal"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()

                    # Check that NO message contains work mode markers
                    for msg in data["messages"]:
                        for marker in WORK_MODE_MARKERS:
                            assert marker not in msg["content"], \
                                f"Normal mode should not contain '{marker}' but found in {msg['agent']}: {msg['content'][:100]}"

    def test_normal_mode_includes_three_peers(self):
        """Test that normal mode includes Claude, DeepSeek, and Gemini"""
        mock_responses = {
            "claude": "Claude's response here.",
            "deepseek": "DeepSeek's response here.",
            "gemini": "Gemini's response here.",
        }

        async def mock_post(url, *args, **kwargs):
            model = kwargs.get("json", {}).get("model", "")
            if "claude" in model.lower():
                return create_mock_response(model, mock_responses["claude"])
            elif "deepseek" in model.lower():
                return create_mock_response(model, mock_responses["deepseek"])
            elif "gemini" in model.lower():
                return create_mock_response(model, mock_responses["gemini"])
            return create_mock_response(model, "Unknown")

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    response = client.post(
                        "/ui/api/multi-agent",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={
                            "text": "Test question",
                            "user_id": "test-user",
                            "mode": "normal"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()

                    # Check all three peer agents are present
                    agents = [msg["agent"] for msg in data["messages"]]
                    assert "claude" in agents, "Claude should be in normal mode response"
                    assert "deepseek" in agents, "DeepSeek should be in normal mode response"
                    assert "gemini" in agents, "Gemini should be in normal mode response"


class TestNormalModeOffline:
    """Test normal mode in offline (template) mode."""

    def test_normal_mode_offline_returns_4_messages(self):
        """Test that offline normal mode returns 4 messages without synthesis"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Test question",
                        "user_id": "test-user",
                        "mode": "normal"
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Should have 4 messages (intro + 3 peers, no synthesis)
                assert len(data["messages"]) == 4, f"Expected 4 messages in offline normal mode but got {len(data['messages'])}"
                assert data["provider"] == "template"

                agents = [msg["agent"] for msg in data["messages"]]
                assert agents == ["quillo", "claude", "deepseek", "gemini"]


class TestWorkModeUnchanged:
    """Test that work mode still has synthesis and structured outputs."""

    def test_work_mode_returns_5_messages_with_synthesis(self):
        """Test that work mode returns 5 messages including synthesis"""
        mock_responses = {
            "claude": "**Evidence:** No evidence provided.\n**Interpretation:** My analysis.\n**Recommendation:** Do this.",
            "deepseek": "**Evidence:** None.\n**Interpretation:** Different view.\n**Recommendation:** Consider that.",
            "gemini": "**Evidence:** N/A.\n**Interpretation:** Structured take.\n**Recommendation:** Try this.",
            "synth": "**Decision Framing:** Summary.\n**Key Disagreements:** None.\n**Best Move:** Go ahead.\n**Alternatives:** Option A, Option B.\n**Evidence Note:** No evidence used."
        }

        async def mock_post(url, *args, **kwargs):
            model = kwargs.get("json", {}).get("model", "")
            if "claude" in model.lower():
                return create_mock_response(model, mock_responses["claude"])
            elif "deepseek" in model.lower():
                return create_mock_response(model, mock_responses["deepseek"])
            elif "gemini" in model.lower():
                return create_mock_response(model, mock_responses["gemini"])
            else:
                return create_mock_response(model, mock_responses["synth"])

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    # Use a specific prompt that won't trigger no-assumptions check
                    response = client.post(
                        "/ui/api/multi-agent",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={
                            "text": "What are three benefits of daily exercise for mental health?",
                            "user_id": "test-user",
                            "mode": "work"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()

                    # Should have 5 messages (intro + 3 peers + synthesis)
                    assert len(data["messages"]) == 5, f"Expected 5 messages in work mode but got {len(data['messages'])}"

                    # Check message order
                    agents = [msg["agent"] for msg in data["messages"]]
                    assert agents == ["quillo", "claude", "deepseek", "gemini", "quillo"]

                    # Last message should be synthesis from quillo
                    last_msg = data["messages"][-1]
                    assert last_msg["agent"] == "quillo"

    def test_work_mode_offline_returns_5_messages(self):
        """Test that offline work mode returns 5 messages with synthesis"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Test question",
                        "user_id": "test-user",
                        "mode": "work"
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Should have 5 messages in work mode
                assert len(data["messages"]) == 5, f"Expected 5 messages in offline work mode but got {len(data['messages'])}"
                assert data["provider"] == "template"

                agents = [msg["agent"] for msg in data["messages"]]
                assert agents == ["quillo", "claude", "deepseek", "gemini", "quillo"]


class TestModeDefaultsToNormal:
    """Test that mode defaults to normal when not specified or invalid."""

    def test_missing_mode_defaults_to_normal(self):
        """Test that missing mode parameter defaults to normal (4 messages)"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Test question",
                        "user_id": "test-user"
                        # mode not specified
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Should default to normal mode (4 messages)
                assert len(data["messages"]) == 4

    def test_invalid_mode_defaults_to_normal(self):
        """Test that invalid mode value defaults to normal"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Test question",
                        "user_id": "test-user",
                        "mode": "invalid_mode"
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Should default to normal mode (4 messages)
                assert len(data["messages"]) == 4

    def test_mode_is_case_insensitive(self):
        """Test that mode parameter is case insensitive"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                # Test uppercase WORK
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Test question",
                        "user_id": "test-user",
                        "mode": "WORK"
                    }
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data["messages"]) == 5  # Work mode should have 5 messages

                # Test mixed case Normal
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Test question",
                        "user_id": "test-user",
                        "mode": "Normal"
                    }
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data["messages"]) == 4  # Normal mode should have 4 messages


class TestNormalModeBypassesTrustContract:
    """Test that normal mode bypasses trust contract checks."""

    def test_normal_mode_no_clarifying_questions(self):
        """Test that normal mode does NOT trigger 'need more context' blocking"""
        # This prompt would typically trigger trust contract questions in work mode
        ambiguous_prompt = "Help me with the thing"

        mock_responses = {
            "claude": "I'd be happy to help. What specifically would you like assistance with?",
            "deepseek": "Sure thing! Let me know what you need.",
            "gemini": "Of course! What would you like help with today?",
        }

        async def mock_post(url, *args, **kwargs):
            model = kwargs.get("json", {}).get("model", "")
            if "claude" in model.lower():
                return create_mock_response(model, mock_responses["claude"])
            elif "deepseek" in model.lower():
                return create_mock_response(model, mock_responses["deepseek"])
            elif "gemini" in model.lower():
                return create_mock_response(model, mock_responses["gemini"])
            return create_mock_response(model, "Unknown")

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    response = client.post(
                        "/ui/api/multi-agent",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={
                            "text": ambiguous_prompt,
                            "user_id": "test-user",
                            "mode": "normal"
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()

                    # Should get 4 messages (not blocked with questions)
                    assert len(data["messages"]) == 4

                    # Should NOT contain trust contract blocking message
                    first_msg = data["messages"][0]
                    assert "need a few details" not in first_msg["content"].lower()
                    assert "no guessing" not in first_msg["content"].lower()
