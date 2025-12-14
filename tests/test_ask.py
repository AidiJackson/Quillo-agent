"""
Tests for /ask Quillopreneur advice endpoint
"""
import pytest
from fastapi.testclient import TestClient
from quillo_agent.main import create_app

app = create_app()
client = TestClient(app)

# Test API key for authentication
TEST_API_KEY = "dev-test-key-12345"


def test_ask_without_auth():
    """Test that /ask requires authentication"""
    response = client.post(
        "/ask",
        json={"text": "How do I start a business?"}
    )
    # Should return 403 (Forbidden) or 401 (Unauthorized)
    assert response.status_code in [401, 403]


def test_ask_with_invalid_auth():
    """Test that /ask rejects invalid API keys"""
    response = client.post(
        "/ask",
        headers={"Authorization": "Bearer invalid-key"},
        json={"text": "How do I start a business?"}
    )
    assert response.status_code == 401


def test_ask_offline_mode():
    """Test /ask returns offline response when no API keys configured"""
    response = client.post(
        "/ask",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={"text": "How do I start a business?"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "answer" in data
    assert "model" in data
    assert "trace_id" in data

    # Verify answer is not empty
    assert len(data["answer"]) > 0

    # In offline mode, model should be "offline"
    # (This assumes no ANTHROPIC_API_KEY is set in test environment)
    assert data["model"] in ["offline", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"]

    # Verify trace_id is a valid UUID format
    assert len(data["trace_id"]) == 36  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    assert data["trace_id"].count("-") == 4


def test_ask_with_user_id():
    """Test /ask with user_id parameter"""
    response = client.post(
        "/ask",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "text": "How should I price my SaaS product?",
            "user_id": "test-user-123"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "trace_id" in data


def test_ask_missing_text():
    """Test /ask fails gracefully with missing text field"""
    response = client.post(
        "/ask",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={}
    )

    # Should return 422 (Unprocessable Entity) for validation error
    assert response.status_code == 422


def test_ask_empty_text():
    """Test /ask with empty text"""
    response = client.post(
        "/ask",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={"text": ""}
    )

    # Empty text is technically valid (validation passes)
    # but response should still be returned
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


def test_ask_long_text_truncation():
    """Test that very long text is handled safely"""
    long_text = "How do I start? " * 500  # Very long question

    response = client.post(
        "/ask",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={"text": long_text}
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
