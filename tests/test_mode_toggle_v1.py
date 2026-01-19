"""
Mode Toggle v1 Tests

Tests for Work vs Normal mode toggle functionality.
Verifies:
1. Backward compatibility (no mode => work mode)
2. Normal mode bypasses strict behaviors
3. Work mode retains strict behaviors
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from quillo_agent.mode import (
    normalize_mode,
    is_work_mode,
    is_normal_mode,
    UORIN_MODE_WORK,
    UORIN_MODE_NORMAL,
    DEFAULT_MODE,
    get_mode_description
)
from quillo_agent.config import settings

# Test UI token (must match what we patch into settings)
TEST_UI_TOKEN = "test-ui-token-mode-toggle"


class TestModeNormalization:
    """Tests for mode normalization function."""

    def test_normalize_mode_none_returns_work(self):
        """None should default to work mode."""
        assert normalize_mode(None) == UORIN_MODE_WORK

    def test_normalize_mode_empty_string_returns_work(self):
        """Empty string should default to work mode."""
        assert normalize_mode("") == UORIN_MODE_WORK

    def test_normalize_mode_work_lowercase(self):
        """'work' should normalize to work."""
        assert normalize_mode("work") == UORIN_MODE_WORK

    def test_normalize_mode_work_uppercase(self):
        """'WORK' should normalize to work (case-insensitive)."""
        assert normalize_mode("WORK") == UORIN_MODE_WORK

    def test_normalize_mode_work_mixed_case(self):
        """'Work' should normalize to work (case-insensitive)."""
        assert normalize_mode("Work") == UORIN_MODE_WORK

    def test_normalize_mode_normal_lowercase(self):
        """'normal' should normalize to normal."""
        assert normalize_mode("normal") == UORIN_MODE_NORMAL

    def test_normalize_mode_normal_uppercase(self):
        """'NORMAL' should normalize to normal (case-insensitive)."""
        assert normalize_mode("NORMAL") == UORIN_MODE_NORMAL

    def test_normalize_mode_invalid_returns_work(self):
        """Invalid mode should fail-safe to work."""
        assert normalize_mode("invalid") == UORIN_MODE_WORK
        assert normalize_mode("foo") == UORIN_MODE_WORK
        assert normalize_mode("bar") == UORIN_MODE_WORK

    def test_normalize_mode_with_whitespace(self):
        """Whitespace should be trimmed."""
        assert normalize_mode("  work  ") == UORIN_MODE_WORK
        assert normalize_mode("  normal  ") == UORIN_MODE_NORMAL


class TestModeHelpers:
    """Tests for mode helper functions."""

    def test_is_work_mode_true(self):
        """is_work_mode should return True for work mode."""
        assert is_work_mode("work") is True
        assert is_work_mode(None) is True  # Default
        assert is_work_mode("") is True  # Default

    def test_is_work_mode_false(self):
        """is_work_mode should return False for normal mode."""
        assert is_work_mode("normal") is False

    def test_is_normal_mode_true(self):
        """is_normal_mode should return True for normal mode."""
        assert is_normal_mode("normal") is True

    def test_is_normal_mode_false(self):
        """is_normal_mode should return False for work mode."""
        assert is_normal_mode("work") is False
        assert is_normal_mode(None) is False  # Default to work

    def test_default_mode_is_work(self):
        """DEFAULT_MODE should be work."""
        assert DEFAULT_MODE == UORIN_MODE_WORK

    def test_get_mode_description_work(self):
        """Work mode description should mention guardrails."""
        desc = get_mode_description("work")
        assert "Guardrails" in desc or "guardrails" in desc

    def test_get_mode_description_normal(self):
        """Normal mode description should mention free-form."""
        desc = get_mode_description("normal")
        assert "free" in desc.lower() or "Free" in desc


class TestAskEndpointModeToggle:
    """Tests for /ask endpoint mode toggle behavior."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from quillo_agent.main import create_app
        app = create_app()
        return TestClient(app)

    def test_default_mode_is_work_when_missing(self, client):
        """POST /ask without mode should default to work mode."""
        # Patch the advice service to avoid actual LLM calls
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch('quillo_agent.routers.ui_proxy.advice.answer_business_question') as mock_advice:
                mock_advice.return_value = ("Test response", "test-model")

                response = client.post(
                    "/ui/api/ask",
                    json={"text": "What is the latest news?", "user_id": "test"},
                    headers={"X-UI-Token": TEST_UI_TOKEN}
                )

                # Should succeed (work mode behavior)
                assert response.status_code == 200

    def test_normal_mode_does_not_block_on_vague_prompt(self, client):
        """Normal mode should not block on vague prompts."""
        # Patch the advice service
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch('quillo_agent.routers.ui_proxy.advice.answer_business_question') as mock_advice:
                mock_advice.return_value = ("Here's my help with that.", "test-model")

                response = client.post(
                    "/ui/api/ask",
                    json={
                        "text": "Rewrite this",  # Vague prompt that would trigger no-assumptions in work mode
                        "user_id": "test",
                        "mode": "normal"
                    },
                    headers={"X-UI-Token": TEST_UI_TOKEN}
                )

                assert response.status_code == 200
                data = response.json()

                # In normal mode, should NOT return trust-contract questions
                assert data["model"] != "trust-contract-v1"
                # Should have called the LLM (advice service)
                assert mock_advice.called

    def test_work_mode_blocks_on_vague_prompt(self, client):
        """Work mode should block on vague prompts with clarifying questions."""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            response = client.post(
                "/ui/api/ask",
                json={
                    "text": "Rewrite this",  # Vague prompt
                    "user_id": "test",
                    "mode": "work"
                },
                headers={"X-UI-Token": TEST_UI_TOKEN}
            )

            assert response.status_code == 200
            data = response.json()

            # In work mode, should return trust-contract clarifying questions
            assert data["model"] == "trust-contract-v1"
            assert "need" in data["answer"].lower() or "details" in data["answer"].lower()

    def test_normal_mode_does_not_auto_fetch_evidence(self, client):
        """Normal mode should not auto-fetch evidence."""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch('quillo_agent.routers.ui_proxy.advice.answer_business_question') as mock_advice:
                with patch('quillo_agent.routers.ui_proxy.retrieve_evidence') as mock_evidence:
                    mock_advice.return_value = ("Response about current news", "test-model")

                    response = client.post(
                        "/ui/api/ask",
                        json={
                            "text": "What are the latest market trends?",  # Would trigger evidence in work mode
                            "user_id": "test",
                            "mode": "normal"
                        },
                        headers={"X-UI-Token": TEST_UI_TOKEN}
                    )

                    assert response.status_code == 200
                    # Evidence should NOT be called in normal mode
                    assert not mock_evidence.called

    def test_work_mode_auto_fetches_evidence(self, client):
        """Work mode should auto-fetch evidence for temporal prompts."""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch('quillo_agent.routers.ui_proxy.advice.answer_business_question') as mock_advice:
                with patch('quillo_agent.routers.ui_proxy.retrieve_evidence') as mock_evidence:
                    from quillo_agent.schemas import EvidenceResponse, EvidenceFact, EvidenceSource

                    mock_advice.return_value = ("Response about current news", "test-model")
                    mock_evidence.return_value = EvidenceResponse(
                        ok=True,
                        retrieved_at="2026-01-18T00:00:00Z",
                        duration_ms=100,
                        facts=[EvidenceFact(text="Test fact", source_id="s1")],
                        sources=[EvidenceSource(
                            id="s1",
                            title="Test Source",
                            domain="test.com",
                            url="https://test.com",
                            retrieved_at="2026-01-18T00:00:00Z"
                        )]
                    )

                    response = client.post(
                        "/ui/api/ask",
                        json={
                            "text": "What are the latest market trends?",  # Temporal trigger
                            "user_id": "test",
                            "mode": "work"
                        },
                        headers={"X-UI-Token": TEST_UI_TOKEN}
                    )

                    assert response.status_code == 200
                    # Evidence should be called in work mode
                    assert mock_evidence.called


class TestMultiAgentEndpointModeToggle:
    """Tests for /multi-agent endpoint mode toggle behavior."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from quillo_agent.main import create_app
        app = create_app()
        return TestClient(app)

    def test_normal_mode_disables_stress_test(self, client):
        """Normal mode should not activate stress test for consequential prompts."""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            with patch('quillo_agent.routers.ui_proxy.run_multi_agent_chat') as mock_multi:
                mock_multi.return_value = (
                    [
                        {"role": "assistant", "agent": "quillo", "content": "Test response", "live": True}
                    ],
                    "openrouter",
                    None,
                    False
                )

                response = client.post(
                    "/ui/api/multi-agent",
                    json={
                        "text": "Should I fire this employee?",  # High-stakes prompt
                        "user_id": "test",
                        "mode": "normal"
                    },
                    headers={"X-UI-Token": TEST_UI_TOKEN}
                )

                assert response.status_code == 200

                # Verify stress_test_mode was False in the call
                call_kwargs = mock_multi.call_args[1]
                assert call_kwargs.get("stress_test_mode") is False

    def test_work_mode_enables_stress_test(self, client):
        """Work mode should activate stress test for consequential prompts."""
        with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
            # Bypass no-assumptions to test stress test logic directly
            with patch('quillo_agent.routers.ui_proxy.enforce_no_assumptions') as mock_no_assumptions:
                mock_no_assumptions.return_value = (True, [])  # ok_to_proceed=True, no questions

                with patch('quillo_agent.routers.ui_proxy.run_multi_agent_chat') as mock_multi:
                    mock_multi.return_value = (
                        [
                            {"role": "assistant", "agent": "quillo", "content": "Test response", "live": True}
                        ],
                        "openrouter",
                        None,
                        False
                    )

                    # High-stakes prompt that triggers stress test
                    response = client.post(
                        "/ui/api/multi-agent",
                        json={
                            "text": "Should I fire John?",  # Triggers detect_consequence
                            "user_id": "test",
                            "mode": "work"
                        },
                        headers={"X-UI-Token": TEST_UI_TOKEN}
                    )

                    assert response.status_code == 200

                    # Verify mock was called (we're past no-assumptions)
                    assert mock_multi.called, "run_multi_agent_chat should have been called"

                    # Verify stress_test_mode was True in the call
                    call_kwargs = mock_multi.call_args[1]
                    assert call_kwargs.get("stress_test_mode") is True


class TestSelfExplanationModeDisclosure:
    """Tests for mode disclosure in self-explanation."""

    def test_micro_disclosures_include_work_mode(self):
        """Micro-disclosures should include work mode indicator."""
        from quillo_agent.self_explanation import build_micro_disclosures

        disclosures = build_micro_disclosures(mode="work")
        assert "Mode: Work" in disclosures
        assert "guardrails" in disclosures.lower()

    def test_micro_disclosures_include_normal_mode(self):
        """Micro-disclosures should include normal mode indicator."""
        from quillo_agent.self_explanation import build_micro_disclosures

        disclosures = build_micro_disclosures(mode="normal")
        assert "Mode: Normal" in disclosures
        assert "free" in disclosures.lower() or "no auto" in disclosures.lower()

    def test_micro_disclosures_default_to_work(self):
        """Micro-disclosures should default to work mode if not specified."""
        from quillo_agent.self_explanation import build_micro_disclosures

        disclosures = build_micro_disclosures()
        assert "Mode: Work" in disclosures
