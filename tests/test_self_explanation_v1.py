"""
Tests for UORIN Self-Explanation v1 (transparency cards + micro-disclosures)
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from quillo_agent.main import create_app
from quillo_agent.config import settings
from quillo_agent.self_explanation import (
    is_transparency_query,
    build_transparency_card,
    build_micro_disclosures,
    TRANSPARENCY_QUERY_PATTERNS
)

app = create_app()
client = TestClient(app)

# Test UI token
TEST_UI_TOKEN = "test-ui-token-12345"


# ============================================================================
# UNIT TESTS: Transparency Detection
# ============================================================================

def test_transparency_query_detection_positive():
    """Test that transparency query patterns are correctly detected"""
    test_cases = [
        "What do you remember about me?",
        "what are you using to answer this?",
        "Why are you saying that?",
        "Are you assuming I have a budget?",
        "Is this up to date?",
        "Did you store my preferences?",
        "What did you use for this answer?",
        "What context do you have?"
    ]

    for text in test_cases:
        assert is_transparency_query(text), f"Should detect: {text}"


def test_transparency_query_detection_negative():
    """Test that non-transparency queries are not detected"""
    test_cases = [
        "How do I write a good email?",
        "What's the best way to approach my boss?",
        "Can you help me draft a message?",
        "Should I fire this employee?",
        "Hello, how are you?"
    ]

    for text in test_cases:
        assert not is_transparency_query(text), f"Should NOT detect: {text}"


def test_transparency_query_case_insensitive():
    """Test that detection is case-insensitive"""
    assert is_transparency_query("WHAT DO YOU REMEMBER?")
    assert is_transparency_query("What Do You Remember?")
    assert is_transparency_query("what do you remember?")


def test_transparency_query_empty_input():
    """Test that empty/None input is handled gracefully"""
    assert not is_transparency_query("")
    assert not is_transparency_query(None)


# ============================================================================
# UNIT TESTS: Transparency Card Building
# ============================================================================

def test_build_transparency_card_all_false():
    """Test transparency card with all flags false"""
    state = {
        "using_conversation_context": False,
        "using_session_context": False,
        "using_profile": False,
        "using_evidence": False,
        "stress_test_mode": False,
        "facts_used": [],
        "not_assuming": ["I'm not filling missing details."],
        "needs_from_user": []
    }

    card = build_transparency_card(state)

    # Check structure
    assert "Transparency" in card
    assert "Using right now:" in card
    assert "Conversation context: ❌" in card
    assert "Session context (24h): ❌" in card
    assert "Judgment Profile: ❌" in card
    assert "Live Evidence: ❌" in card
    assert "Stress Test mode: ❌" in card
    assert "No external facts fetched." in card
    assert "I'm not filling missing details." in card
    assert "Nothing needed" in card
    assert "Control:" in card
    assert 'Say "clear context"' in card


def test_build_transparency_card_all_true():
    """Test transparency card with all flags true"""
    state = {
        "using_conversation_context": True,
        "using_session_context": True,
        "using_profile": True,
        "using_evidence": True,
        "stress_test_mode": True,
        "facts_used": [
            {"text": "Fact 1", "source": "example.com", "timestamp": "2026-01-12"},
            {"text": "Fact 2", "source": "test.org", "timestamp": ""}
        ],
        "not_assuming": ["Not assuming X", "Not assuming Y"],
        "needs_from_user": ["Clarify your budget", "Confirm timeline"]
    }

    card = build_transparency_card(state)

    # Check all flags are checkmarks
    assert "Conversation context: ✅" in card
    assert "Session context (24h): ✅" in card
    assert "Judgment Profile: ✅" in card
    assert "Live Evidence: ✅" in card
    assert "Stress Test mode: ✅" in card

    # Check facts
    assert "Fact 1 (source: example.com, 2026-01-12)" in card
    assert "Fact 2 (source: test.org)" in card

    # Check not_assuming
    assert "Not assuming X" in card
    assert "Not assuming Y" in card

    # Check needs
    assert "Clarify your budget" in card
    assert "Confirm timeline" in card


def test_transparency_card_no_prompt_leak():
    """Test that transparency card does not leak internal heuristics or prompt text"""
    state = {
        "using_conversation_context": False,
        "using_session_context": False,
        "using_profile": False,
        "using_evidence": False,
        "stress_test_mode": False,
        "facts_used": [],
        "not_assuming": [],
        "needs_from_user": []
    }

    card = build_transparency_card(state)

    # Check that no internal keywords leak
    forbidden_terms = [
        "system message",
        "prompt",
        "instruction",
        "LLM",
        "model",
        "heuristic",
        "pattern",
        "TRANSPARENCY_QUERY_PATTERNS"
    ]

    for term in forbidden_terms:
        assert term.lower() not in card.lower(), f"Card should not contain: {term}"


# ============================================================================
# UNIT TESTS: Micro-disclosures
# ============================================================================

def test_micro_disclosures_all_false():
    """Test that mode disclosure still appears when all other flags are false"""
    disclosures = build_micro_disclosures(
        using_evidence=False,
        stress_test_mode=False,
        using_conversation_context=False,
        using_profile=False
    )

    # Mode disclosure is always present (Mode Toggle v1)
    assert "Mode: Work" in disclosures
    assert "Evidence:" not in disclosures
    assert "Stress Test:" not in disclosures


def test_micro_disclosures_evidence_only():
    """Test evidence disclosure appears when evidence is used"""
    disclosures = build_micro_disclosures(
        using_evidence=True,
        stress_test_mode=False,
        using_conversation_context=False,
        using_profile=False
    )

    assert "Evidence: on (sources + timestamps below)" in disclosures
    assert "Mode: Work" in disclosures  # Mode always present (Mode Toggle v1)
    assert "Context:" not in disclosures
    assert "Profile:" not in disclosures


def test_micro_disclosures_stress_test_only():
    """Test stress test disclosure appears when stress test mode is active"""
    disclosures = build_micro_disclosures(
        using_evidence=False,
        stress_test_mode=True,
        using_conversation_context=False,
        using_profile=False
    )

    # Mode Toggle v1: Mode always shows, Stress Test is separate line
    assert "Mode: Work" in disclosures
    assert "Stress Test: active (consequential decision detected)" in disclosures
    assert "Evidence:" not in disclosures


def test_micro_disclosures_all_true():
    """Test that all disclosures appear in correct order when all flags are true"""
    disclosures = build_micro_disclosures(
        using_evidence=True,
        stress_test_mode=True,
        using_conversation_context=True,
        using_profile=True
    )

    lines = disclosures.strip().split("\n")

    # Check order (Mode Toggle v1: mode first, then evidence, stress test, context, profile)
    assert lines[0] == "Mode: Work (guardrails + evidence triggers + stress test)"
    assert lines[1] == "Evidence: on (sources + timestamps below)"
    assert lines[2] == "Stress Test: active (consequential decision detected)"
    assert lines[3] == "Context: using this conversation's history"
    assert lines[4] == "Profile: using your saved preferences (view/edit anytime)"

    # Check blank line separator
    assert disclosures.endswith("\n\n")


def test_micro_disclosures_formatting():
    """Test that disclosures are single-line and properly separated"""
    disclosures = build_micro_disclosures(
        using_evidence=True,
        stress_test_mode=True,
        using_conversation_context=False,
        using_profile=False
    )

    # Mode Toggle v1: Mode + Evidence + Stress Test = 3 lines + blank line separator
    assert disclosures.count("\n") == 4  # 3 disclosure lines + 1 blank line


# ============================================================================
# INTEGRATION TESTS: /ask endpoint
# ============================================================================

@patch('quillo_agent.routers.ui_proxy.advice.answer_business_question')
def test_ask_transparency_query_short_circuit(mock_answer):
    """Test that transparency query in /ask returns card without LLM call"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/ask",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "What do you remember about me?",
                "user_id": "test-user"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check that transparency card is returned
        assert "Transparency" in data["answer"]
        assert "Using right now:" in data["answer"]
        assert "self-explanation-v1" in data["model"]

        # Verify no LLM call was made
        mock_answer.assert_not_called()


@patch('quillo_agent.routers.ui_proxy.advice.answer_business_question')
@patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
def test_ask_micro_disclosure_no_evidence(mock_evidence, mock_answer):
    """Test that no disclosures appear when evidence is not used"""
    mock_answer.return_value = ("Here's my answer.", "gpt-4")
    mock_evidence.return_value = MagicMock(ok=False, facts=[])

    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/ask",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "Tell me about business strategy",
                "user_id": "test-user"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check that no disclosures appear
        assert "Evidence: on" not in data["answer"]
        assert "Mode: Stress Test" not in data["answer"]
        assert "Context: using" not in data["answer"]
        assert "Profile: using" not in data["answer"]


@patch('quillo_agent.routers.ui_proxy.advice.answer_business_question')
@patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
def test_ask_micro_disclosure_with_evidence(mock_evidence, mock_answer):
    """Test that evidence disclosure appears when evidence is successfully fetched"""
    # Mock evidence response
    mock_fact = MagicMock()
    mock_fact.text = "Test fact"
    mock_fact.source_id = "src1"

    mock_source = MagicMock()
    mock_source.id = "src1"
    mock_source.domain = "example.com"

    mock_evidence_response = MagicMock()
    mock_evidence_response.ok = True
    mock_evidence_response.facts = [mock_fact]
    mock_evidence_response.sources = [mock_source]

    mock_evidence.return_value = mock_evidence_response
    mock_answer.return_value = ("Here's my answer.", "gpt-4")

    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        with patch('quillo_agent.routers.ui_proxy.classify_prompt_needs_evidence', return_value=True):
            response = client.post(
                "/ui/api/ask",
                headers={"X-UI-Token": TEST_UI_TOKEN},
                json={
                    "text": "What's the latest news about AI?",
                    "user_id": "test-user"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Check that evidence disclosure appears at the top
            assert "Evidence: on (sources + timestamps below)" in data["answer"]
            # Evidence disclosure should be before the answer
            assert data["answer"].index("Evidence: on") < data["answer"].index("Here's my answer")


# ============================================================================
# INTEGRATION TESTS: /multi-agent endpoint
# ============================================================================

@patch('quillo_agent.routers.ui_proxy.run_multi_agent_chat')
def test_multi_agent_transparency_query_short_circuit(mock_run):
    """Test that transparency query in /multi-agent returns card without LLM call"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/multi-agent",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "What context are you using?",
                "user_id": "test-user",
                "agents": ["claude", "gemini"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check that transparency card is returned
        assert len(data["messages"]) == 1
        assert "Transparency" in data["messages"][0]["content"]
        assert data["messages"][0]["agent"] == "quillo"
        assert "self-explanation-v1" in data["provider"]

        # Verify no multi-agent call was made
        mock_run.assert_not_called()


@patch('quillo_agent.routers.ui_proxy.run_multi_agent_chat')
@patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
@patch('quillo_agent.routers.ui_proxy.enforce_no_assumptions')
def test_multi_agent_stress_test_disclosure(mock_no_assumptions, mock_evidence, mock_run):
    """Test that stress test disclosure appears for consequential prompts"""
    # Mock no assumptions check to let us proceed
    mock_no_assumptions.return_value = (True, [])

    # Mock evidence response
    mock_evidence_response = MagicMock()
    mock_evidence_response.ok = False
    mock_evidence_response.facts = []
    mock_evidence.return_value = mock_evidence_response

    # Mock multi-agent response with synthesis message
    mock_run.return_value = (
        [
            {
                "role": "assistant",
                "agent": "claude",
                "content": "Claude's perspective",
                "model_id": "claude-3",
                "live": True,
                "unavailable_reason": None
            },
            {
                "role": "assistant",
                "agent": "quillo",
                "content": "Here's the synthesis",
                "model_id": "gpt-4",
                "live": True,
                "unavailable_reason": None
            }
        ],
        "openrouter",
        None,
        False
    )

    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/multi-agent",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "Should I fire this underperforming employee?",
                "user_id": "test-user",
                "agents": ["claude", "gemini"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Find the synthesis message (from quillo)
        synthesis_msg = next((m for m in data["messages"] if m["agent"] == "quillo"), None)
        assert synthesis_msg is not None

        # Check that stress test disclosure appears (Mode Toggle v1 format)
        assert "Mode: Work" in synthesis_msg["content"]
        assert "Stress Test: active (consequential decision detected)" in synthesis_msg["content"]


@patch('quillo_agent.routers.ui_proxy.run_multi_agent_chat')
@patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
def test_multi_agent_no_disclosure_casual_prompt(mock_evidence, mock_run):
    """Test that stress test disclosure does NOT appear for casual prompts"""
    # Mock evidence response
    mock_evidence_response = MagicMock()
    mock_evidence_response.ok = False
    mock_evidence_response.facts = []
    mock_evidence.return_value = mock_evidence_response

    # Mock multi-agent response
    mock_run.return_value = (
        [
            {
                "role": "assistant",
                "agent": "quillo",
                "content": "Here's the answer",
                "model_id": "gpt-4",
                "live": True,
                "unavailable_reason": None
            }
        ],
        "openrouter",
        None,
        False
    )

    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/multi-agent",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "What's the weather like today?",
                "user_id": "test-user",
                "agents": ["claude", "gemini"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check that NO stress test disclosure appears
        synthesis_msg = next((m for m in data["messages"] if m["agent"] == "quillo"), None)
        assert synthesis_msg is not None
        assert "Mode: Stress Test" not in synthesis_msg["content"]


@patch('quillo_agent.routers.ui_proxy.run_multi_agent_chat')
@patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
def test_multi_agent_evidence_disclosure(mock_evidence, mock_run):
    """Test that evidence disclosure appears when evidence is successfully fetched"""
    # Mock evidence response
    mock_fact = MagicMock()
    mock_fact.text = "Test fact"
    mock_fact.source_id = "src1"

    mock_source = MagicMock()
    mock_source.id = "src1"
    mock_source.domain = "example.com"

    mock_evidence_response = MagicMock()
    mock_evidence_response.ok = True
    mock_evidence_response.facts = [mock_fact]
    mock_evidence_response.sources = [mock_source]

    mock_evidence.return_value = mock_evidence_response

    # Mock multi-agent response
    mock_run.return_value = (
        [
            {
                "role": "assistant",
                "agent": "quillo",
                "content": "Here's the synthesis",
                "model_id": "gpt-4",
                "live": True,
                "unavailable_reason": None
            }
        ],
        "openrouter",
        None,
        False
    )

    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        with patch('quillo_agent.routers.ui_proxy.classify_prompt_needs_evidence', return_value=True):
            response = client.post(
                "/ui/api/multi-agent",
                headers={"X-UI-Token": TEST_UI_TOKEN},
                json={
                    "text": "What's the latest news about AI?",
                    "user_id": "test-user",
                    "agents": ["claude", "gemini"]
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Check that evidence disclosure appears
            synthesis_msg = next((m for m in data["messages"] if m["agent"] == "quillo"), None)
            assert synthesis_msg is not None
            assert "Evidence: on (sources + timestamps below)" in synthesis_msg["content"]


# ============================================================================
# SECURITY TESTS
# ============================================================================

def test_profile_disclosure_only_when_used():
    """Test that profile disclosure does NOT appear unless profile is actually used"""
    # This test verifies that we don't falsely claim to use profile when we don't
    disclosures = build_micro_disclosures(
        using_evidence=False,
        stress_test_mode=False,
        using_conversation_context=False,
        using_profile=False  # Should be False until profile is actually used
    )

    assert "Profile:" not in disclosures
