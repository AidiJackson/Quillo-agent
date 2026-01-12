"""
Tests for Judgment Profile v1 (read-only storage, user-controlled)
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient
from quillo_agent.main import create_app
from quillo_agent.config import settings

app = create_app()
client = TestClient(app)

# Test UI token
TEST_UI_TOKEN = "test-ui-token-12345"


# ============================================================================
# UNIT TESTS: Service Layer Validation
# ============================================================================

def test_validate_profile_rejects_unknown_keys():
    """Test that validation rejects profiles with unknown keys"""
    from quillo_agent.services.judgment_profile.service import validate_profile, JudgmentProfileValidationError

    invalid_profile = {
        "risk_posture": {
            "value": "conservative",
            "source": "explicit",
            "confirmed_at": "2026-01-12T00:00:00Z"
        },
        "unknown_field": {  # This should be rejected
            "value": "test",
            "source": "explicit",
            "confirmed_at": "2026-01-12T00:00:00Z"
        }
    }

    with pytest.raises(JudgmentProfileValidationError) as exc_info:
        validate_profile(invalid_profile)

    assert "unknown_field" in str(exc_info.value).lower()


def test_validate_profile_rejects_missing_source():
    """Test that validation rejects fields missing 'source'"""
    from quillo_agent.services.judgment_profile.service import validate_profile, JudgmentProfileValidationError

    invalid_profile = {
        "risk_posture": {
            "value": "conservative",
            # Missing 'source' field
            "confirmed_at": "2026-01-12T00:00:00Z"
        }
    }

    with pytest.raises(JudgmentProfileValidationError) as exc_info:
        validate_profile(invalid_profile)

    assert "source" in str(exc_info.value).lower()


def test_validate_profile_rejects_missing_confirmed_at():
    """Test that validation rejects fields missing 'confirmed_at'"""
    from quillo_agent.services.judgment_profile.service import validate_profile, JudgmentProfileValidationError

    invalid_profile = {
        "risk_posture": {
            "value": "conservative",
            "source": "explicit",
            # Missing 'confirmed_at' field
        }
    }

    with pytest.raises(JudgmentProfileValidationError) as exc_info:
        validate_profile(invalid_profile)

    assert "confirmed_at" in str(exc_info.value).lower()


def test_validate_profile_rejects_non_explicit_source():
    """Test that validation rejects source != 'explicit'"""
    from quillo_agent.services.judgment_profile.service import validate_profile, JudgmentProfileValidationError

    invalid_profile = {
        "risk_posture": {
            "value": "conservative",
            "source": "inferred",  # Should be 'explicit'
            "confirmed_at": "2026-01-12T00:00:00Z"
        }
    }

    with pytest.raises(JudgmentProfileValidationError) as exc_info:
        validate_profile(invalid_profile)

    assert "explicit" in str(exc_info.value).lower()


def test_validate_profile_rejects_invalid_enum_values():
    """Test that validation rejects invalid enum values"""
    from quillo_agent.services.judgment_profile.service import validate_profile, JudgmentProfileValidationError

    invalid_profile = {
        "risk_posture": {
            "value": "invalid_value",  # Should be conservative|moderate|aggressive
            "source": "explicit",
            "confirmed_at": "2026-01-12T00:00:00Z"
        }
    }

    with pytest.raises(JudgmentProfileValidationError) as exc_info:
        validate_profile(invalid_profile)

    assert "invalid_value" in str(exc_info.value).lower()


def test_validate_profile_accepts_valid_profile():
    """Test that validation accepts a valid profile"""
    from quillo_agent.services.judgment_profile.service import validate_profile

    valid_profile = {
        "risk_posture": {
            "value": "conservative",
            "source": "explicit",
            "confirmed_at": "2026-01-12T00:00:00Z"
        },
        "default_tone": {
            "value": "formal",
            "source": "explicit",
            "confirmed_at": "2026-01-12T00:00:00Z"
        }
    }

    # Should not raise
    validate_profile(valid_profile)


# ============================================================================
# API TESTS: GET /profile/judgment
# ============================================================================

def test_get_profile_none_returns_null():
    """Test that GET returns null profile for new user"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.get(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-new-user"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "judgment_profile_v1"
        assert data["profile"] is None
        assert data["updated_at"] is None


# ============================================================================
# API TESTS: POST /profile/judgment
# ============================================================================

def test_post_profile_valid_upserts_and_returns():
    """Test that POST with valid profile creates/updates profile"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        valid_profile = {
            "profile": {
                "risk_posture": {
                    "value": "conservative",
                    "source": "explicit",
                    "confirmed_at": "2026-01-12T00:00:00Z"
                },
                "default_tone": {
                    "value": "formal",
                    "source": "explicit",
                    "confirmed_at": "2026-01-12T00:00:00Z"
                }
            }
        }

        response = client.post(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-post-user"},
            json=valid_profile
        )

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "judgment_profile_v1"
        assert data["profile"] == valid_profile["profile"]
        assert data["updated_at"] is not None

        # Verify we can retrieve it
        response2 = client.get(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-post-user"}
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["profile"] == valid_profile["profile"]


def test_post_profile_rejects_unknown_keys():
    """Test that POST rejects profiles with unknown keys"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        invalid_profile = {
            "profile": {
                "unknown_field": {
                    "value": "test",
                    "source": "explicit",
                    "confirmed_at": "2026-01-12T00:00:00Z"
                }
            }
        }

        response = client.post(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-invalid-keys"},
            json=invalid_profile
        )

        assert response.status_code == 400
        assert "unknown" in response.json()["detail"].lower()


def test_post_profile_rejects_missing_source():
    """Test that POST rejects fields missing 'source'"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        invalid_profile = {
            "profile": {
                "risk_posture": {
                    "value": "conservative",
                    # Missing 'source'
                    "confirmed_at": "2026-01-12T00:00:00Z"
                }
            }
        }

        response = client.post(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-missing-source"},
            json=invalid_profile
        )

        assert response.status_code == 400
        assert "source" in response.json()["detail"].lower()


def test_post_profile_rejects_missing_confirmed_at():
    """Test that POST rejects fields missing 'confirmed_at'"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        invalid_profile = {
            "profile": {
                "risk_posture": {
                    "value": "conservative",
                    "source": "explicit",
                    # Missing 'confirmed_at'
                }
            }
        }

        response = client.post(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-missing-confirmed-at"},
            json=invalid_profile
        )

        assert response.status_code == 400
        assert "confirmed_at" in response.json()["detail"].lower()


def test_post_profile_rejects_invalid_enum_values():
    """Test that POST rejects invalid enum values"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        invalid_profile = {
            "profile": {
                "risk_posture": {
                    "value": "invalid_value",
                    "source": "explicit",
                    "confirmed_at": "2026-01-12T00:00:00Z"
                }
            }
        }

        response = client.post(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-invalid-enum"},
            json=invalid_profile
        )

        assert response.status_code == 400
        assert "invalid_value" in response.json()["detail"].lower()


# ============================================================================
# API TESTS: DELETE /profile/judgment
# ============================================================================

def test_delete_profile_removes_profile():
    """Test that DELETE removes profile"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # First create a profile
        valid_profile = {
            "profile": {
                "risk_posture": {
                    "value": "conservative",
                    "source": "explicit",
                    "confirmed_at": "2026-01-12T00:00:00Z"
                }
            }
        }

        client.post(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-delete-user"},
            json=valid_profile
        )

        # Verify profile exists
        response_get = client.get(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-delete-user"}
        )
        assert response_get.json()["profile"] is not None

        # Delete profile
        response_delete = client.delete(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-delete-user"}
        )

        assert response_delete.status_code == 200
        assert response_delete.json()["deleted"] is True

        # Verify profile is gone
        response_get2 = client.get(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-delete-user"}
        )
        assert response_get2.json()["profile"] is None


def test_delete_nonexistent_profile_returns_false():
    """Test that DELETE returns false for nonexistent profile"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.delete(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-nonexistent"}
        )

        assert response.status_code == 200
        assert response.json()["deleted"] is False


# ============================================================================
# SECURITY TESTS: IDOR Prevention
# ============================================================================

def test_idor_prevention_profile_cannot_be_accessed_cross_user():
    """Test that users cannot access each other's profiles"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # User A creates a profile
        user_a_profile = {
            "profile": {
                "risk_posture": {
                    "value": "conservative",
                    "source": "explicit",
                    "confirmed_at": "2026-01-12T00:00:00Z"
                }
            }
        }

        client.post(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "user-a"},
            json=user_a_profile
        )

        # User B creates a different profile
        user_b_profile = {
            "profile": {
                "risk_posture": {
                    "value": "aggressive",
                    "source": "explicit",
                    "confirmed_at": "2026-01-12T00:00:00Z"
                }
            }
        }

        client.post(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "user-b"},
            json=user_b_profile
        )

        # Verify User A can only see their own profile
        response_a = client.get(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "user-a"}
        )
        assert response_a.json()["profile"]["risk_posture"]["value"] == "conservative"

        # Verify User B can only see their own profile
        response_b = client.get(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "user-b"}
        )
        assert response_b.json()["profile"]["risk_posture"]["value"] == "aggressive"

        # Verify profiles are properly isolated
        assert response_a.json()["profile"] != response_b.json()["profile"]


# ============================================================================
# INTEGRATION TESTS: Self-Explanation Transparency
# ============================================================================

@patch('quillo_agent.routers.ui_proxy.advice.answer_business_question')
def test_transparency_card_shows_judgment_profile_true_when_exists(mock_answer):
    """Test that transparency card shows profile checkmark when profile exists"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Create a profile for the user
        valid_profile = {
            "profile": {
                "risk_posture": {
                    "value": "conservative",
                    "source": "explicit",
                    "confirmed_at": "2026-01-12T00:00:00Z"
                }
            }
        }

        client.post(
            "/ui/api/profile/judgment",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            params={"user_key": "test-transparency-user"},
            json=valid_profile
        )

        # Ask a transparency question
        response = client.post(
            "/ui/api/ask",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "What do you remember about me?",
                "user_id": "test-transparency-user"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify transparency card is returned
        assert "Transparency" in data["answer"]
        assert "Judgment Profile: ✅" in data["answer"]

        # Verify no LLM call was made
        mock_answer.assert_not_called()


@patch('quillo_agent.routers.ui_proxy.advice.answer_business_question')
def test_transparency_card_shows_judgment_profile_false_when_absent(mock_answer):
    """Test that transparency card shows profile X when profile doesn't exist"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        # Ask a transparency question for user with no profile
        response = client.post(
            "/ui/api/ask",
            headers={"X-UI-Token": TEST_UI_TOKEN},
            json={
                "text": "What do you remember about me?",
                "user_id": "test-no-profile-user"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify transparency card is returned
        assert "Transparency" in data["answer"]
        assert "Judgment Profile: ❌" in data["answer"]

        # Verify no LLM call was made
        mock_answer.assert_not_called()


# ============================================================================
# AUTH TESTS
# ============================================================================

def test_get_profile_requires_auth():
    """Test that GET requires authentication"""
    response = client.get(
        "/ui/api/profile/judgment",
        params={"user_key": "test-user"}
    )

    # Should fail without token (in production mode)
    # In dev mode with no token configured, it bypasses auth
    # So we test with token configured
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.get(
            "/ui/api/profile/judgment",
            params={"user_key": "test-user"}
        )
        # Should fail without X-UI-Token header
        assert response.status_code in [401, 403]


def test_post_profile_requires_auth():
    """Test that POST requires authentication"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.post(
            "/ui/api/profile/judgment",
            params={"user_key": "test-user"},
            json={"profile": {}}
        )
        # Should fail without X-UI-Token header
        assert response.status_code in [401, 403]


def test_delete_profile_requires_auth():
    """Test that DELETE requires authentication"""
    with patch.object(settings, 'quillo_ui_token', TEST_UI_TOKEN):
        response = client.delete(
            "/ui/api/profile/judgment",
            params={"user_key": "test-user"}
        )
        # Should fail without X-UI-Token header
        assert response.status_code in [401, 403]
