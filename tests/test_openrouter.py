"""
Tests for OpenRouter LLM integration
"""
import pytest
import json
from unittest.mock import patch, AsyncMock
import httpx
import anyio
from quillo_agent.services.llm import LLMRouter
from quillo_agent.config import settings


# Configure pytest-anyio to use only asyncio backend
pytestmark = pytest.mark.anyio(backends=['asyncio'])


@pytest.fixture
def mock_openrouter_key():
    """Mock OpenRouter API key for testing"""
    with patch.object(settings, 'openrouter_api_key', 'test-openrouter-key'):
        with patch.object(settings, 'openrouter_base_url', 'https://openrouter.ai/api/v1'):
            yield


@pytest.fixture
def mock_no_api_keys():
    """Mock no API keys configured"""
    with patch.object(settings, 'openrouter_api_key', ''):
        with patch.object(settings, 'anthropic_api_key', ''):
            yield


async def test_openrouter_key_missing_fallback_none(mock_no_api_keys):
    """Test that when OPENROUTER_API_KEY is missing, classify_fallback returns None"""
    router = LLMRouter()
    result = await router.classify_fallback("Test message")
    assert result is None


async def test_openrouter_classify_valid_json(mock_openrouter_key):
    """Test that valid JSON from OpenRouter is parsed correctly"""
    router = LLMRouter()

    # Mock response with valid JSON
    valid_response = {
        "intent": "response",
        "slots": {"outcome": "Defuse"},
        "reasons": ["User wants to respond to email", "Defuse keyword detected"],
        "confidence": 0.95
    }

    # Create a mock request
    mock_request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")

    mock_response = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {"message": {"content": json.dumps(valid_response)}}
            ]
        },
        request=mock_request
    )

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock, return_value=mock_response):
        result = await router.classify_fallback("Handle this email and defuse conflict")

        assert result is not None
        assert result["intent"] == "response"
        assert result["slots"]["outcome"] == "Defuse"
        assert result["confidence"] == 0.95
        assert isinstance(result["reasons"], list)


async def test_openrouter_classify_invalid_json_handled_gracefully(mock_openrouter_key):
    """Test that invalid JSON from OpenRouter is handled gracefully without crash"""
    router = LLMRouter()

    # Mock response with invalid JSON (plain text instead of JSON)
    mock_response = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {"message": {"content": "This is plain text, not JSON"}}
            ]
        }
    )

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock, return_value=mock_response):
        result = await router.classify_fallback("Test message")

        # Should return None instead of crashing
        assert result is None


async def test_openrouter_classify_missing_required_fields(mock_openrouter_key):
    """Test that JSON missing required fields is handled gracefully"""
    router = LLMRouter()

    # Mock response with JSON missing required fields
    invalid_response = {
        "slots": {"outcome": "Defuse"},
        # Missing "intent" and "confidence"
    }

    mock_response = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {"message": {"content": json.dumps(invalid_response)}}
            ]
        }
    )

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock, return_value=mock_response):
        result = await router.classify_fallback("Test message")

        # Should return None for invalid structure
        assert result is None


async def test_openrouter_http_error_handled(mock_openrouter_key):
    """Test that HTTP errors from OpenRouter are handled gracefully"""
    router = LLMRouter()

    # Mock 500 error response
    mock_response = httpx.Response(
        status_code=500,
        text="Internal Server Error"
    )
    mock_response._request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")

    async def raise_for_status():
        raise httpx.HTTPStatusError("Server error", request=mock_response.request, response=mock_response)

    mock_response.raise_for_status = raise_for_status

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock, return_value=mock_response):
        result = await router.classify_fallback("Test message")

        # Should return None instead of crashing
        assert result is None


async def test_openrouter_timeout_handled(mock_openrouter_key):
    """Test that timeout errors are handled gracefully"""
    router = LLMRouter()

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock, side_effect=httpx.TimeoutException("Request timeout")):
        result = await router.classify_fallback("Test message")

        # Should return None instead of crashing
        assert result is None


async def test_openrouter_model_routing_fast(mock_openrouter_key):
    """Test that fast model is selected for fast routing tier"""
    with patch.object(settings, 'model_routing', 'fast'):
        with patch.object(settings, 'openrouter_fast_model', 'anthropic/claude-3-haiku'):
            router = LLMRouter()
            model = router._get_openrouter_model()
            assert model == 'anthropic/claude-3-haiku'


async def test_openrouter_model_routing_balanced(mock_openrouter_key):
    """Test that balanced model is selected for balanced routing tier"""
    with patch.object(settings, 'model_routing', 'balanced'):
        with patch.object(settings, 'openrouter_balanced_model', 'anthropic/claude-3.5-sonnet'):
            router = LLMRouter()
            model = router._get_openrouter_model()
            assert model == 'anthropic/claude-3.5-sonnet'


async def test_openrouter_model_routing_premium(mock_openrouter_key):
    """Test that premium model is selected for premium routing tier"""
    with patch.object(settings, 'model_routing', 'premium'):
        with patch.object(settings, 'openrouter_premium_model', 'anthropic/claude-opus-4'):
            router = LLMRouter()
            model = router._get_openrouter_model()
            assert model == 'anthropic/claude-opus-4'


async def test_openrouter_input_truncation():
    """Test that long user input is truncated for safety"""
    router = LLMRouter()
    long_text = "A" * 5000
    truncated = router._truncate_user_input(long_text, max_chars=2000)

    assert len(truncated) == 2000
    assert truncated == "A" * 2000


async def test_openrouter_plan_reasoning_premium(mock_openrouter_key):
    """Test that plan reasoning uses premium model when MODEL_ROUTING=premium"""
    with patch.object(settings, 'model_routing', 'premium'):
        router = LLMRouter()

        # Mock valid plan response
        plan_response = {
            "steps": [
                {"tool": "response_generator", "premium": False, "rationale": "Generate response"},
                {"tool": "tone_adjuster", "premium": True, "rationale": "Adjust tone"}
            ]
        }

        mock_request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")

        mock_response = httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {"message": {"content": json.dumps(plan_response)}}
                ]
            },
            request=mock_request
        )

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock, return_value=mock_response):
            result = await router.plan_reasoning("response", {"outcome": "Defuse"}, "Test text")

            assert result is not None
            assert len(result) == 2
            assert result[0]["tool"] == "response_generator"
            assert result[1]["tool"] == "tone_adjuster"


async def test_openrouter_business_question(mock_openrouter_key):
    """Test business question answering via OpenRouter"""
    router = LLMRouter()

    mock_request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")

    mock_response = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {"message": {"content": "Consider value-based pricing for your SaaS product..."}}
            ]
        },
        request=mock_request
    )

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock, return_value=mock_response):
        result = await router.answer_business_question("How should I price my SaaS?", "")

        assert result is not None
        assert "value-based pricing" in result.lower()


async def test_openrouter_chat_request_headers(mock_openrouter_key):
    """Test that OpenRouter requests include correct headers"""
    router = LLMRouter()

    mock_response = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {"message": {"content": "test response"}}
            ]
        }
    )

    mock_post = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient.post', mock_post):
        await router._openrouter_chat(
            messages=[{"role": "user", "content": "test"}],
            model="anthropic/claude-3-haiku",
            max_tokens=100,
            timeout=10.0
        )

        # Check that the request was made with correct headers
        call_args = mock_post.call_args
        assert call_args is not None

        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer test-openrouter-key'
        assert headers['Content-Type'] == 'application/json'
        assert 'HTTP-Referer' in headers
        assert 'X-Title' in headers


async def test_openrouter_prefer_over_anthropic(mock_openrouter_key):
    """Test that OpenRouter is preferred when both keys are configured"""
    with patch.object(settings, 'anthropic_api_key', 'test-anthropic-key'):
        router = LLMRouter()

        # Mock OpenRouter response
        valid_response = {
            "intent": "response",
            "slots": {},
            "reasons": ["Test"],
            "confidence": 0.9
        }

        mock_request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")

        mock_response = httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {"message": {"content": json.dumps(valid_response)}}
                ]
            },
            request=mock_request
        )

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock, return_value=mock_response) as mock_post:
            result = await router.classify_fallback("Test")

            # Should use OpenRouter (not Anthropic)
            assert result is not None
            assert result["intent"] == "response"

            # Verify the endpoint called was OpenRouter
            call_args = mock_post.call_args
            url = call_args[0][0]
            assert "openrouter.ai" in url
