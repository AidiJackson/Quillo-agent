"""
Judgment Profile service layer with strict validation

CRITICAL RULES:
- ONLY explicit, user-confirmed fields allowed
- NO automatic inference or learning
- Reject unknown keys
- Require source="explicit" and confirmed_at for all fields
- Max payload size: 20KB
"""
import json
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from . import repo
from .models import JudgmentProfile


# Allowed top-level keys in judgment profile v1
ALLOWED_PROFILE_KEYS = {
    "risk_posture",
    "relationship_sensitivity",
    "decision_authority",
    "default_tone",
    "jurisdiction",
    "constraints"
}

# Allowed enum values for each field
ALLOWED_ENUMS = {
    "risk_posture": {"conservative", "moderate", "aggressive"},
    "relationship_sensitivity": {"low", "medium", "high"},
    "decision_authority": {"none", "limited", "full"},
    "default_tone": {"formal", "neutral", "casual"},
}

# Max payload size (20KB)
MAX_PAYLOAD_SIZE = 20 * 1024


class JudgmentProfileValidationError(ValueError):
    """Raised when judgment profile validation fails"""
    pass


def validate_profile(profile: Dict[str, Any]) -> None:
    """
    Validate judgment profile against v1 schema rules.

    CRITICAL VALIDATION RULES:
    1. Only allowed keys (reject unknown keys)
    2. Each field must have source="explicit"
    3. Each field must have confirmed_at (ISO8601 timestamp)
    4. Enum fields must have valid values
    5. Total payload must be under 20KB

    Args:
        profile: Profile dictionary to validate

    Raises:
        JudgmentProfileValidationError: If validation fails
    """
    if not isinstance(profile, dict):
        raise JudgmentProfileValidationError("Profile must be a dictionary")

    # Check for unknown keys
    profile_keys = set(profile.keys())
    unknown_keys = profile_keys - ALLOWED_PROFILE_KEYS
    if unknown_keys:
        raise JudgmentProfileValidationError(
            f"Unknown keys not allowed: {', '.join(unknown_keys)}. "
            f"Allowed keys: {', '.join(ALLOWED_PROFILE_KEYS)}"
        )

    # Validate each field
    for key, value in profile.items():
        if not isinstance(value, dict):
            raise JudgmentProfileValidationError(
                f"Field '{key}' must be a dictionary with 'source', 'value', and 'confirmed_at'"
            )

        # Check required subfields
        if "source" not in value:
            raise JudgmentProfileValidationError(
                f"Field '{key}' missing required 'source' field"
            )

        if "confirmed_at" not in value:
            raise JudgmentProfileValidationError(
                f"Field '{key}' missing required 'confirmed_at' field"
            )

        if "value" not in value:
            raise JudgmentProfileValidationError(
                f"Field '{key}' missing required 'value' field"
            )

        # Validate source is "explicit"
        if value["source"] != "explicit":
            raise JudgmentProfileValidationError(
                f"Field '{key}' must have source='explicit', got '{value['source']}'"
            )

        # Validate confirmed_at is ISO8601 timestamp
        try:
            datetime.fromisoformat(value["confirmed_at"].replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            raise JudgmentProfileValidationError(
                f"Field '{key}' has invalid confirmed_at timestamp: {value.get('confirmed_at')}"
            )

        # Validate enum values if applicable
        if key in ALLOWED_ENUMS:
            field_value = value["value"]
            allowed_values = ALLOWED_ENUMS[key]
            if field_value not in allowed_values:
                raise JudgmentProfileValidationError(
                    f"Field '{key}' has invalid value '{field_value}'. "
                    f"Allowed values: {', '.join(allowed_values)}"
                )

    # Check payload size
    profile_json = json.dumps(profile)
    if len(profile_json.encode('utf-8')) > MAX_PAYLOAD_SIZE:
        raise JudgmentProfileValidationError(
            f"Profile payload exceeds maximum size of {MAX_PAYLOAD_SIZE} bytes"
        )


def get_profile(db: Session, user_key: str) -> Optional[Dict[str, Any]]:
    """
    Get judgment profile for a user.

    Args:
        db: Database session
        user_key: User identifier

    Returns:
        Profile dictionary if exists, None otherwise
    """
    profile_record = repo.get_by_user_key(db, user_key)
    if not profile_record:
        return None

    try:
        profile_data = json.loads(profile_record.profile_json)
        return {
            "version": profile_record.version,
            "profile": profile_data,
            "updated_at": profile_record.updated_at.isoformat()
        }
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in profile for user_key={user_key}: {e}")
        return None


def upsert_profile(
    db: Session,
    user_key: str,
    profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create or update judgment profile for a user.

    Validates profile against strict v1 schema before saving.

    Args:
        db: Database session
        user_key: User identifier
        profile: Profile dictionary to save

    Returns:
        Saved profile data with metadata

    Raises:
        JudgmentProfileValidationError: If validation fails
    """
    # Validate profile
    validate_profile(profile)

    # Convert to JSON string
    profile_json = json.dumps(profile, separators=(',', ':'))

    # Save to database
    profile_record = repo.upsert_for_user(
        db=db,
        user_key=user_key,
        profile_json=profile_json,
        version="judgment_profile_v1"
    )

    return {
        "version": profile_record.version,
        "profile": profile,
        "updated_at": profile_record.updated_at.isoformat()
    }


def delete_profile(db: Session, user_key: str) -> bool:
    """
    Delete judgment profile for a user.

    Args:
        db: Database session
        user_key: User identifier

    Returns:
        True if profile was deleted, False if profile didn't exist
    """
    return repo.delete_for_user(db, user_key)


def profile_exists(db: Session, user_key: str) -> bool:
    """
    Check if judgment profile exists for a user.

    Fast existence check without loading the full profile.
    Used by self-explanation transparency system.

    Args:
        db: Database session
        user_key: User identifier

    Returns:
        True if profile exists, False otherwise
    """
    try:
        profile = repo.get_by_user_key(db, user_key)
        return profile is not None
    except Exception as e:
        logger.error(f"Error checking profile existence for user_key={user_key}: {e}")
        return False
