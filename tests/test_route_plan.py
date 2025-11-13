"""
Test route and plan endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_route_response_intent():
    """Test POST /route with response intent and defuse slot"""
    payload = {
        "text": "Handle this client email and defuse conflict",
        "user_id": "test-user-123"
    }

    response = client.post("/route", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "intent" in data
    assert data["intent"] == "response"
    assert "reasons" in data
    assert isinstance(data["reasons"], list)
    assert len(data["reasons"]) > 0

    # Check for extracted slot
    assert "slots" in data
    if data["slots"]:
        assert "outcome" in data["slots"]
        assert data["slots"]["outcome"] == "Defuse"


def test_route_rewrite_intent():
    """Test POST /route with rewrite intent"""
    payload = {
        "text": "Rewrite this email to be more professional",
        "user_id": "test-user-123"
    }

    response = client.post("/route", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["intent"] == "rewrite"


def test_plan_generation():
    """Test POST /plan returns non-empty steps"""
    payload = {
        "intent": "response",
        "user_id": "test-user-123",
        "slots": {"outcome": "Defuse"},
        "text": "Handle this client email and defuse conflict"
    }

    response = client.post("/plan", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "steps" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0

    # Check step structure
    first_step = data["steps"][0]
    assert "tool" in first_step
    assert "rationale" in first_step
    assert isinstance(first_step["tool"], str)
    assert isinstance(first_step["rationale"], str)

    # Check trace_id
    assert "trace_id" in data
    assert isinstance(data["trace_id"], str)
    assert len(data["trace_id"]) > 0


def test_plan_with_defuse_slot():
    """Test POST /plan with Defuse slot includes conflict resolver"""
    payload = {
        "intent": "response",
        "user_id": "test-user-123",
        "slots": {"outcome": "Defuse"}
    }

    response = client.post("/plan", json=payload)
    assert response.status_code == 200

    data = response.json()
    steps = data["steps"]

    # Should include conflict_resolver when outcome is Defuse
    tool_names = [step["tool"] for step in steps]
    assert "conflict_resolver" in tool_names


def test_route_missing_text():
    """Test POST /route with missing text returns 422"""
    payload = {"user_id": "test-user-123"}

    response = client.post("/route", json=payload)
    assert response.status_code == 422  # Validation error
