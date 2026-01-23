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
        """Test that offline mode returns template transcript (Work mode)"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Can I get a second opinion on this micro-SaaS acquisition deal?",
                        "user_id": "test-user",
                        "mode": "work"
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
        """Test that offline responses don't leak internal reasoning (Work mode)"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question", "user_id": "test-user", "mode": "work"}
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
                        json={"text": "Test question", "user_id": "test-user", "mode": "work"}
                    )
                    assert response.status_code == 200
                    data = response.json()

                    # Should use openrouter provider with no fallback reason
                    assert data["provider"] == "openrouter"
                    assert data["fallback_reason"] is None

                    # Should have 5 messages (Work mode)
                    assert len(data["messages"]) == 5

                    # Check agents (Work mode)
                    agents = [msg["agent"] for msg in data["messages"]]
                    assert agents == ["quillo", "claude", "deepseek", "gemini", "quillo"]

    def test_online_all_peers_fail_partial_live(self):
        """Test that when all peer agents fail, we get partial-live with peers_unavailable=True (Work mode)"""
        async def mock_post_error(*args, **kwargs):
            """Mock httpx.AsyncClient.post that raises error for all OpenRouter calls"""
            raise httpx.HTTPError("API error")

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post_error):
                    response = client.post(
                        "/ui/api/multi-agent",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={"text": "Test question", "user_id": "test-user", "mode": "work"}
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
        """Test that response has all required fields (Work mode)"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question", "user_id": "test-user", "mode": "work"}
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
                    json={"text": "Test question", "user_id": "test-user", "mode": "work"}
                )
                assert response.status_code == 200
                data = response.json()

                # Should be a valid UUID
                try:
                    uuid.UUID(data["trace_id"])
                except ValueError:
                    pytest.fail("trace_id is not a valid UUID")

    def test_messages_in_correct_order(self):
        """Test that messages are in correct order (Work mode)"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question", "user_id": "test-user", "mode": "work"}
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
        """Test that agents parameter is optional (Work mode)"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                # Without agents parameter, with explicit Work mode
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={"text": "Test question", "mode": "work"}
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data["messages"]) == 5


class TestMultiAgentDevBypass:
    """Test dev mode bypass behavior."""

    def test_dev_mode_no_token_configured_bypasses(self):
        """Test that dev mode with no token configured bypasses auth (Work mode)"""
        with patch.object(settings, 'app_env', 'dev'):
            with patch.object(settings, 'quillo_ui_token', ''):
                with patch.object(settings, 'openrouter_api_key', ''):
                    response = client.post(
                        "/ui/api/multi-agent",
                        json={"text": "Test question", "user_id": "test-user", "mode": "work"}
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["provider"] == "template"


class TestMultiAgentTruncation:
    """Test that responses are not truncated mid-sentence."""

    def test_responses_not_truncated_min_length(self):
        """Test that live agent responses meet minimum length expectations"""
        def create_mock_response(model, content):
            """Create a mock response"""
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": content}}]
            }
            return mock_resp

        # Create realistic-length responses (not truncated)
        mock_responses = {
            "claude": "Looking at your question, I'd consider the long-term implications first. The key is balancing immediate needs with sustainable outcomes. Whatever path you choose, documentation and clear communication will be critical. I'd recommend starting with a small proof-of-concept to validate the core assumptions before committing to a full implementation. This gives you flexibility to adjust based on early feedback.",
            "deepseek": "Hold up—before you get too comfortable with that, ask yourself: what if the opposite is true? Sometimes the 'thoughtful' path is just procrastination with better PR. What's the risk of moving fast and adjusting later versus overthinking and missing the window? I'd argue that speed and iteration often beats perfect planning, especially when the market is moving quickly.",
            "gemini": "Here's a structured view: break this into phases. First, validate your core assumption with user research. Second, test with a small pilot group to gather real feedback. Third, scale what works while maintaining quality. This approach gives you Claude's thoughtfulness without DeepSeek's risk of paralysis. Each phase should have clear success criteria and off-ramps.",
            "synth": "All three perspectives add value here. My recommendation: use Gemini's phased approach as your framework, with Claude's long-term lens and DeepSeek's urgency check at each phase. The key is balancing speed with validation - move quickly through small experiments rather than slowly through big plans. Quick question: what's the smallest pilot you could run this week to test your core hypothesis?"
        }

        async def mock_post(url, *args, **kwargs):
            """Mock httpx.AsyncClient.post"""
            model = kwargs.get("json", {}).get("model", "")

            if "claude" in model.lower():
                content = mock_responses["claude"]
            elif "deepseek" in model.lower():
                content = mock_responses["deepseek"]
            elif "gemini" in model.lower():
                content = mock_responses["gemini"]
            else:
                content = mock_responses["synth"]

            return create_mock_response(model, content)

        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', 'test-key'):
                with patch('httpx.AsyncClient.post', new=mock_post):
                    response = client.post(
                        "/ui/api/multi-agent",
                        headers={"X-UI-Token": TEST_UI_TOKEN},
                        json={"text": "Should I build a custom CRM or use an off-the-shelf solution?", "user_id": "test-user", "mode": "work"}
                    )
                    assert response.status_code == 200
                    data = response.json()

                    # Verify all live peer responses are substantive (not truncated)
                    for i, msg in enumerate(data["messages"]):
                        if msg["agent"] in ["claude", "deepseek", "gemini"] and msg.get("live", True):
                            # Peer agent responses should be at least 100 chars to be substantive
                            assert len(msg["content"]) >= 100, \
                                f"{msg['agent']} response too short ({len(msg['content'])} chars): {msg['content']}"

                            # Should end with proper punctuation (not truncated mid-sentence)
                            assert msg["content"].rstrip()[-1] in ['.', '!', '?'], \
                                f"{msg['agent']} response doesn't end with punctuation: {msg['content'][-50:]}"

                        # First quillo message is just a frame, skip it
                        # Last quillo message (synthesis) should also be substantive
                        if msg["agent"] == "quillo" and i > 0 and msg.get("live", True):
                            assert len(msg["content"]) >= 100, \
                                f"quillo synthesis response too short ({len(msg['content'])} chars): {msg['content']}"
                            assert msg["content"].rstrip()[-1] in ['.', '!', '?'], \
                                f"quillo synthesis response doesn't end with punctuation: {msg['content'][-50:]}"

    def test_max_tokens_increased_from_300(self):
        """Test that max_tokens default has been increased from 300 to prevent truncation"""
        from quillo_agent.services.multi_agent_chat import _call_openrouter_safe
        import inspect

        # Get the default value of max_tokens parameter
        sig = inspect.signature(_call_openrouter_safe)
        max_tokens_default = sig.parameters['max_tokens'].default

        # Should be at least 1000 (we use 1500)
        assert max_tokens_default >= 1000, \
            f"max_tokens default is {max_tokens_default}, should be >= 1000 to prevent truncation"


class TestMultiAgentPartialLive:
    """Test partial-live behavior where individual agents can fail independently."""

    def test_quillo_succeeds_all_peers_fail(self):
        """Test Quillo succeeds but all peers fail → openrouter with peers_unavailable=True (Work mode)"""
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
                                           json={"text": "test", "user_id": "demo", "mode": "work"})

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
        """Test Quillo + Claude succeed, DeepSeek/Gemini fail → openrouter, peers_unavailable=False (Work mode)"""
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
                                           json={"text": "test", "user_id": "demo", "mode": "work"})

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
        """Test that all messages have model_id, live, unavailable_reason fields (Work mode)"""

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
                                           json={"text": "test", "user_id": "demo", "mode": "work"})

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


class TestNormalModeParity:
    """Test Normal mode multi-agent feels native (no work scaffolding)."""

    # Work scaffolding markers that should NOT appear in Normal mode
    WORK_SCAFFOLDING_MARKERS = [
        "Evidence:",
        "Interpretation:",
        "Recommendation:",
        "TRUST CONTRACT",
        "no guessing",
        "Stress Test",
        "lens",
        "Top Risks",
        "Key Disagreements",
        "Best Move",
        "Alternatives",
        "Execution Tool",
    ]

    def test_normal_mode_returns_peers_only(self):
        """Test that Normal mode returns only peer messages (no intro, no synthesis)"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "What's a good price for a micro-SaaS?",
                        "user_id": "test-user",
                        "mode": "normal"
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Normal mode: 3 messages (Claude, DeepSeek, Gemini) - NO quillo
                assert len(data["messages"]) == 3

                # Check agents - should be peers only
                agents = [msg["agent"] for msg in data["messages"]]
                assert "quillo" not in agents, "Normal mode should not include Uorin/quillo messages"
                assert agents == ["claude", "deepseek", "gemini"]

    def test_normal_mode_no_work_scaffolding_markers(self):
        """Test that Normal mode responses don't contain work scaffolding markers"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Should I invest in Bitcoin?",
                        "user_id": "test-user",
                        "mode": "normal"
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Check all messages for work scaffolding markers
                for msg in data["messages"]:
                    content = msg["content"]
                    for marker in self.WORK_SCAFFOLDING_MARKERS:
                        assert marker not in content, \
                            f"Work scaffolding marker '{marker}' found in Normal mode response: {content[:100]}..."

    def test_work_mode_returns_full_structure(self):
        """Test that Work mode still returns intro + peers + synthesis"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                # Use a longer prompt to avoid triggering no-assumptions check
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "I'm considering whether to use React or Vue for my new e-commerce project. I need something that scales well and has good ecosystem support. My team is experienced in JavaScript but not specifically in either framework. We expect around 10,000 daily users initially.",
                        "user_id": "test-user",
                        "mode": "work"
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Work mode: 5 messages (quillo intro, claude, deepseek, gemini, quillo synthesis)
                assert len(data["messages"]) == 5

                # Check agents order
                agents = [msg["agent"] for msg in data["messages"]]
                assert agents == ["quillo", "claude", "deepseek", "gemini", "quillo"]

                # First message should be Quillo intro
                assert "perspectives" in data["messages"][0]["content"].lower()

                # Last message should be Quillo synthesis
                assert data["messages"][-1]["agent"] == "quillo"

    def test_mode_defaults_to_normal(self):
        """Test that mode defaults to 'normal' when not specified"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Test question",
                        "user_id": "test-user"
                        # mode not specified - should default to normal
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Should behave like Normal mode: 3 peer messages only
                assert len(data["messages"]) == 3
                agents = [msg["agent"] for msg in data["messages"]]
                assert "quillo" not in agents

    def test_mode_case_insensitive(self):
        """Test that mode is case-insensitive"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                # Test WORK (uppercase)
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
                assert len(data["messages"]) == 5  # Work mode structure

                # Test Normal (mixed case)
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
                assert len(data["messages"]) == 3  # Normal mode structure

    def test_normal_mode_skips_trust_contract_checks(self):
        """Test that Normal mode skips no-assumptions and evidence auto-fetch"""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch.object(settings, 'openrouter_api_key', ''):
                # This prompt would trigger no-assumptions in Work mode (short, vague)
                response = client.post(
                    "/ui/api/multi-agent",
                    headers={"X-UI-Token": TEST_UI_TOKEN},
                    json={
                        "text": "Help",
                        "user_id": "test-user",
                        "mode": "normal"
                    }
                )
                assert response.status_code == 200
                data = response.json()

                # Should NOT return a "I need details" clarifying question
                # Should return peer messages directly
                assert len(data["messages"]) == 3
                for msg in data["messages"]:
                    assert "I need a few details" not in msg["content"]
                    assert "no guessing" not in msg["content"]
