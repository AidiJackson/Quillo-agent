"""
Judgment Profile repository layer
"""
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from .models import JudgmentProfile


def get_by_user_key(db: Session, user_key: str) -> Optional[JudgmentProfile]:
    """
    Get judgment profile by user_key.

    Args:
        db: Database session
        user_key: User identifier

    Returns:
        JudgmentProfile if exists, None otherwise
    """
    try:
        return db.query(JudgmentProfile).filter(
            JudgmentProfile.user_key == user_key
        ).first()
    except Exception as e:
        logger.error(f"Error fetching judgment profile for user_key={user_key}: {e}")
        return None


def upsert_for_user(
    db: Session,
    user_key: str,
    profile_json: str,
    version: str = "judgment_profile_v1"
) -> JudgmentProfile:
    """
    Create or update judgment profile for a user.

    Args:
        db: Database session
        user_key: User identifier
        profile_json: JSON string of profile data
        version: Profile schema version

    Returns:
        Created or updated JudgmentProfile

    Raises:
        Exception: If database operation fails
    """
    existing = get_by_user_key(db, user_key)

    if existing:
        # Update existing profile
        existing.profile_json = profile_json
        existing.version = version
        logger.info(f"Updating judgment profile for user_key={user_key}")
    else:
        # Create new profile
        existing = JudgmentProfile(
            user_key=user_key,
            profile_json=profile_json,
            version=version
        )
        db.add(existing)
        logger.info(f"Creating new judgment profile for user_key={user_key}")

    db.commit()
    db.refresh(existing)
    return existing


def delete_for_user(db: Session, user_key: str) -> bool:
    """
    Delete judgment profile for a user.

    Args:
        db: Database session
        user_key: User identifier

    Returns:
        True if profile was deleted, False if profile didn't exist

    Raises:
        Exception: If database operation fails
    """
    existing = get_by_user_key(db, user_key)

    if not existing:
        logger.info(f"No judgment profile to delete for user_key={user_key}")
        return False

    db.delete(existing)
    db.commit()
    logger.info(f"Deleted judgment profile for user_key={user_key}")
    return True
