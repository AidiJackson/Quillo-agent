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
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import httpx

from quillo_agent.main import create_app
from quillo_agent.config import settings
from quillo_agent.services.multi_agent_chat import CLAUDE_MODEL, CHALLENGER_MODEL


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
                assert "fallback_reason" in data

                # Should use template provider with fallback reason
                assert data["provider"] == "template"
                assert data["fallback_reason"] == "openrouter_key_missing"

                # Should have 5 messages (Primary/Claude/DeepSeek/Gemini/Primary)
                assert len(data["messages"]) == 5

                # Check message structure
                for msg in data["messages"]:
                    assert "role" in msg
                    assert "agent" in msg
                    assert "content" in msg
                    assert msg["role"] == "assistant"

                # Check agents
                agents = [msg["agent"] for msg in data["messages"]]
                assert agents == ["quillo", "claude", "deepseek", "gemini", "quillo"]

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
            "deepseek": "DeepSeek's contrasting view here.",
            "gemini": "Gemini's structured analysis here.",
            "synth": "Here's my synthesis and recommendation. What's your risk tolerance?"
        }

        def create_mock_response(model):
            """Create a mock response for a given model"""
            mock_resp = MagicMock()
            mock_resp.status_code = 200

            if "claude" in model.lower():
                content = mock_responses["claude"]
            elif "deepseek" in model.lower():
                content = mock_responses["deepseek"]
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

                    # Should use openrouter provider with no fallback reason
                    assert data["provider"] == "openrouter"
                    assert data["fallback_reason"] is None

                    # Should have 5 messages
                    assert len(data["messages"]) == 5

                    # Check agents
                    agents = [msg["agent"] for msg in data["messages"]]
                    assert agents == ["quillo", "claude", "deepseek", "gemini", "quillo"]

    def test_online_all_peers_fail_partial_live(self):
        """Test that when all peer agents fail, we get partial-live with peers_unavailable=True"""
        async def mock_post_error(*args, **kwargs):
            """Mock httpx.AsyncClient.post that raises error for all OpenRouter calls"""
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

                    # NEW BEHAVIOR: Partial-live instead of full template fallback
                    # Quillo frame succeeds (deterministic), all peers fail
                    assert data["provider"] == "openrouter"
                    assert data["peers_unavailable"] == True
                    assert data["fallback_reason"] is None
                    assert len(data["messages"]) == 5

                    # All peer agents should be unavailable
                    for msg in data["messages"]:
                        if msg["agent"] in ["claude", "deepseek", "gemini"]:
                            assert msg["live"] == False
                            assert msg["unavailable_reason"] == "exception"  # HTTPError is caught by generic Exception handler


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
                assert "fallback_reason" in data

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

                # Should be: Primary -> Claude -> DeepSeek -> Gemini -> Primary
                agents = [msg["agent"] for msg in data["messages"]]
                assert agents[0] == "quillo"  # Primary frames
                assert agents[1] == "claude"  # Claude perspective
                assert agents[2] == "deepseek"    # DeepSeek contrasts
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


class TestMultiAgentPartialLive:
    """Test partial-live behavior where individual agents can fail independently."""

    def test_quillo_succeeds_all_peers_fail(self):
        """Test Quillo succeeds but all peers fail → openrouter with peers_unavailable=True"""
        call_count = [0]

        def create_mock_response(model, content):
            """Create a mock response"""
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": content}}]
            }
            return mock_resp

        async def mock_post(url, *args, **kwargs):
            call_count[0] += 1
            model = kwargs.get("json", {}).get("model", "")

            # All peer calls fail
            if "claude" in model.lower() or "deepseek" in model.lower() or "gemini" in model.lower():
                raise httpx.TimeoutException("Timeout")

            # Synthesis succeeds
            return create_mock_response(model, "Synthesis content")

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    response = client.post("/ui/api/multi-agent",
                                           headers={"X-UI-Token": TEST_UI_TOKEN},
                                           json={"text": "test", "user_id": "demo"})

                    assert response.status_code == 200
                    data = response.json()
                    assert data["provider"] == "openrouter"
                    assert data["peers_unavailable"] == True

                    # Check peer agents are unavailable
                    claude_msg = next(m for m in data["messages"] if m["agent"] == "claude")
                    assert claude_msg["live"] == False
                    assert claude_msg["unavailable_reason"] == "timeout"
                    assert "[Agent unavailable:" in claude_msg["content"]

    def test_quillo_and_one_peer_succeed(self):
        """Test Quillo + Claude succeed, DeepSeek/Gemini fail → openrouter, peers_unavailable=False"""
        call_count = [0]

        def create_mock_response(model, content):
            """Create a mock response"""
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": content}}]
            }
            return mock_resp

        async def mock_post(url, *args, **kwargs):
            call_count[0] += 1
            model = kwargs.get("json", {}).get("model", "")

            # Claude succeeds
            if "claude" in model.lower():
                return create_mock_response(model, "Claude response")

            # DeepSeek and Gemini fail
            if "deepseek" in model.lower() or "gemini" in model.lower():
                mock_resp = MagicMock()
                mock_resp.status_code = 429
                raise httpx.HTTPStatusError("Rate limited",
                                           request=MagicMock(),
                                           response=mock_resp)

            # Synthesis succeeds
            return create_mock_response(model, "Synthesis")

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    response = client.post("/ui/api/multi-agent",
                                           headers={"X-UI-Token": TEST_UI_TOKEN},
                                           json={"text": "test", "user_id": "demo"})

                    assert response.status_code == 200
                    data = response.json()
                    assert data["provider"] == "openrouter"
                    assert data["peers_unavailable"] == False

                    # Check Claude is live
                    claude_msg = next(m for m in data["messages"] if m["agent"] == "claude")
                    assert claude_msg["live"] == True
                    assert claude_msg["model_id"] == CLAUDE_MODEL

                    # Check DeepSeek is unavailable
                    deepseek_msg = next(m for m in data["messages"] if m["agent"] == "deepseek")
                    assert deepseek_msg["live"] == False
                    assert deepseek_msg["unavailable_reason"] == "rate_limited"

    def test_all_messages_have_new_metadata_fields(self):
        """Test that all messages have model_id, live, unavailable_reason fields"""

        def create_mock_response(model, content):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": content}}]
            }
            return mock_resp

        async def mock_post(url, *args, **kwargs):
            model = kwargs.get("json", {}).get("model", "")
            return create_mock_response(model, f"Response from {model}")

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    response = client.post("/ui/api/multi-agent",
                                           headers={"X-UI-Token": TEST_UI_TOKEN},
                                           json={"text": "test", "user_id": "demo"})

                    assert response.status_code == 200
                    data = response.json()

                    # All messages should have the new fields
                    for msg in data["messages"]:
                        assert "model_id" in msg
                        assert "live" in msg
                        assert "unavailable_reason" in msg
                        # First message (quillo frame) should have model_id=None
                        if msg["agent"] == "quillo" and data["messages"].index(msg) == 0:
                            assert msg["model_id"] is None
                        # Live messages should have unavailable_reason=None
                        if msg["live"]:
                            assert msg["unavailable_reason"] is None
