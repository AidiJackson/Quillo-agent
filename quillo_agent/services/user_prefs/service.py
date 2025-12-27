"""
User Preferences service layer
"""
from sqlalchemy.orm import Session
from loguru import logger

from .models import UserPrefs, ApprovalMode
from .repo import UserPrefsRepository


class UserPrefsService:
    """Service layer for user preferences operations"""

    @staticmethod
    def get_prefs(db: Session, user_key: str) -> UserPrefs:
        """
        Get user preferences, creating with defaults if not exists.

        Args:
            db: Database session
            user_key: User identifier

        Returns:
            UserPrefs instance
        """
        logger.info(f"Getting preferences for user_key={user_key}")
        prefs = UserPrefsRepository.get_or_create(db, user_key)
        logger.info(f"Retrieved preferences: approval_mode={prefs.approval_mode}")
        return prefs

    @staticmethod
    def update_approval_mode(
        db: Session,
        user_key: str,
        approval_mode: str
    ) -> UserPrefs:
        """
        Update user's approval mode.

        Args:
            db: Database session
            user_key: User identifier
            approval_mode: New approval mode value

        Returns:
            Updated UserPrefs instance

        Raises:
            ValueError: If approval_mode is invalid
        """
        # Validate approval mode
        try:
            ApprovalMode(approval_mode)
        except ValueError:
            valid_modes = [m.value for m in ApprovalMode]
            raise ValueError(
                f"Invalid approval_mode: {approval_mode}. "
                f"Must be one of: {', '.join(valid_modes)}"
            )

        logger.info(f"Updating approval_mode for user_key={user_key} to {approval_mode}")
        prefs = UserPrefsRepository.update_approval_mode(db, user_key, approval_mode)
        logger.info(f"Updated preferences: approval_mode={prefs.approval_mode}")
        return prefs
