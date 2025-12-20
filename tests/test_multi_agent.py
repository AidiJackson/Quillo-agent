"""
Tests for Multi-Agent Chat endpoint (v0.1)

Verifies:
- Auth protection (UI token required)
- Offline mode returns template transcript
- Online mode with OpenRouter mocking
- No chain-of-thought leakage
- Gemini as 4th peer agent
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import httpx

from quillo_agent.main import create_app
from quillo_agent.config import settings


# Test UI token
TEST_UI_TOKEN = "test-token-12345"

# Create test client
app = create_app()
client = TestClient(app)


# Forbidden phrases that leak internal implementation
FORBIDDEN_PHRASES = [
    "chain-of-thought",
    "i'm thinking",
    "internal",
    "tool execution",
    "llm",
    "system prompt",
    "here's my reasoning",
]


class TestMultiAgentAuth:
    """Test authentication and authorization."""

    def test_multi_agent_without_token_fails(self):
        """Test that /ui/api/multi-agent requires UI token"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            response = client.post(
                "/ui/api/multi-agent",
                json={"text": "Test question", "user_id": "test-user"}
            )
            assert response.status_code in [401, 403]

    def test_multi_agent_with_invalid_token_fails(self):
        """Test that invalid UI token is rejected"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            response = client.post(
                "/ui/api/multi-agent",
                headers={"X-UI-Token": "wrong-token"},
                json={"text": "Test question", "user_id": "test-user"}
            )
            assert response.status_code == 403

    def test_multi_agent_with_valid_token_succeeds(self):
        """Test that valid UI token allows access"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question", "user_id": "test-user"}
                )
                assert response.status_code == 200


class TestMultiAgentOfflineMode:
    """Test offline mode (no OpenRouter key)."""

    def test_offline_returns_template_transcript(self):
        """Test that offline mode returns template transcript"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Can I get a second opinion on this micro-SaaS acquisition deal?",
                        "user_id": "test-user"
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Check response structure
                assert "messages" in data
                assert "provider" in data
                assert "trace_id" in data

                # Should use template provider
                assert data["provider"] == "template"

                # Should have 5 messages (Primary/Claude/Grok/Gemini/Primary)
                assert len(data["messages"]) == 5

                # Check message structure
                for msg in data["messages"]:
                    assert "role" in msg
                    assert "agent" in msg
                    assert "content" in msg
                    assert msg["role"] == "assistant"

                # Check agents
                agents = [msg["agent"] for msg in data["messages"]]
                assert agents == ["quillo", "claude", "grok", "gemini", "quillo"]

                # Check content is not empty
                for msg in data["messages"]:
                    assert len(msg["content"]) > 10

    def test_offline_no_chain_of_thought_leakage(self):
        """Test that offline responses don't leak internal reasoning"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question", "user_id": "test-user"}
                )
                assert response.status_code == 200
                data = response.json()

                # Check all messages for forbidden phrases
                for msg in data["messages"]:
                    content_lower = msg["content"].lower()
                    for phrase in FORBIDDEN_PHRASES:
                        assert phrase not in content_lower, \
                            f"Forbidden phrase '{phrase}' found in: {msg['content']}"


class TestMultiAgentOnlineMode:
    """Test online mode with OpenRouter."""

    def test_online_with_openrouter_mock(self):
        """Test that online mode calls OpenRouter correctly"""
        from unittest.mock import MagicMock

        # Mock OpenRouter responses
        mock_responses = {
            "claude": "Claude's perspective on this matter.",
            "grok": "Grok's contrasting view here.",
            "gemini": "Gemini's structured analysis here.",
            "synth": "Here's my synthesis and recommendation. What's your risk tolerance?"
        }

        def create_mock_response(model):
            """Create a mock response for a given model"""
            mock_resp = MagicMock()
            mock_resp.status_code = 200

            if "claude" in model.lower():
                content = mock_responses["claude"]
            elif "grok" in model.lower():
                content = mock_responses["grok"]
            elif "gemini" in model.lower():
                content = mock_responses["gemini"]
            else:
                content = mock_responses["synth"]

            mock_resp.json.return_value = {
                "choices": [{"message": {"content": content}}]
            }
            return mock_resp

        # Track which model is being called
        call_count = [0]

        async def mock_post(url, *args, **kwargs):
            """Mock httpx.AsyncClient.post"""
            payload = kwargs.get("json", {})
            model = payload.get("model", "")
            call_count[0] += 1
            return create_mock_response(model)

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    response = client.post(
                        "/ui/api/multi-agent",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={"text": "Test question", "user_id": "test-user"}
                    )
                    assert response.status_code == 200
                    data = response.json()

                    # Should use openrouter provider
                    assert data["provider"] == "openrouter"

                    # Should have 5 messages
                    assert len(data["messages"]) == 5

                    # Check agents
                    agents = [msg["agent"] for msg in data["messages"]]
                    assert agents == ["quillo", "claude", "grok", "gemini", "quillo"]

    def test_online_fallback_to_template_on_error(self):
        """Test that errors fall back to template mode"""
        async def mock_post_error(*args, **kwargs):
            """Mock httpx.AsyncClient.post that raises error"""
            raise httpx.HTTPError("API error")

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post_error):
                    response = client.post(
                        "/ui/api/multi-agent",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={"text": "Test question", "user_id": "test-user"}
                    )
                    assert response.status_code == 200
                    data = response.json()

                    # Should fall back to template
                    assert data["provider"] == "template"
                    assert len(data["messages"]) == 5


class TestMultiAgentResponseStructure:
    """Test response structure and content quality."""

    def test_response_has_all_required_fields(self):
        """Test that response has all required fields"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question", "user_id": "test-user"}
                )
                assert response.status_code == 200
                data = response.json()

                # Required top-level fields
                assert "messages" in data
                assert "provider" in data
                assert "trace_id" in data

                # Messages structure
                assert isinstance(data["messages"], list)
                assert len(data["messages"]) > 0

                # Each message has required fields
                for msg in data["messages"]:
                    assert "role" in msg
                    assert "agent" in msg
                    assert "content" in msg

    def test_trace_id_is_uuid(self):
        """Test that trace_id is a valid UUID"""
        import uuid

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question", "user_id": "test-user"}
                )
                assert response.status_code == 200
                data = response.json()

                # Should be a valid UUID
                try:
                    uuid.UUID(data["trace_id"])
                except ValueError:
                    pytest.fail("trace_id is not a valid UUID")

    def test_messages_in_correct_order(self):
        """Test that messages are in correct order"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question", "user_id": "test-user"}
                )
                assert response.status_code == 200
                data = response.json()

                # Should be: Primary -> Claude -> Grok -> Gemini -> Primary
                agents = [msg["agent"] for msg in data["messages"]]
                assert agents[0] == "quillo"  # Primary frames
                assert agents[1] == "claude"  # Claude perspective
                assert agents[2] == "grok"    # Grok contrasts
                assert agents[3] == "gemini"  # Gemini structured analysis
                assert agents[4] == "quillo"  # Primary synthesizes

    def test_optional_agents_parameter(self):
        """Test that agents parameter is optional"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                # Without agents parameter
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question"}
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data["messages"]) == 5


class TestMultiAgentDevBypass:
    """Test dev mode bypass behavior."""

    def test_dev_mode_no_token_configured_bypasses(self):
        """Test that dev mode with no token configured bypasses auth"""
        with patch.object(settings, 'app_env', 'dev'):
            with patch.object(settings, 'quillo_ui_token', ''):
                with patch.object(settings, 'openrouter_api_key', ''):
                    response = client.post(
                        "/ui/api/multi-agent",
                        json={"text": "Test question", "user_id": "test-user"}
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["provider"] == "template"
