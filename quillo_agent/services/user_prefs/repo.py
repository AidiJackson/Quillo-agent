"""
User Preferences repository layer
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from .models import UserPrefs, ApprovalMode


class UserPrefsRepository:
    """Repository for UserPrefs database operations"""

    @staticmethod
    def get_or_create(
        db: Session,
        user_key: str
    ) -> UserPrefs:
        """
        Get user preferences, creating with defaults if not exists.

        Args:
            db: Database session
            user_key: User identifier

        Returns:
            UserPrefs instance
        """
        prefs = db.query(UserPrefs).filter(UserPrefs.user_key == user_key).first()
        if not prefs:
            prefs = UserPrefs(
                user_key=user_key,
                approval_mode=ApprovalMode.PLAN_THEN_AUTO.value
            )
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return prefs

    @staticmethod
    def update_approval_mode(
        db: Session,
        user_key: str,
        approval_mode: str
    ) -> UserPrefs:
        """
        Update user's approval mode, creating prefs if not exists.

        Args:
            db: Database session
            user_key: User identifier
            approval_mode: New approval mode value

        Returns:
            Updated UserPrefs instance
        """
        prefs = db.query(UserPrefs).filter(UserPrefs.user_key == user_key).first()
        if prefs:
            prefs.approval_mode = approval_mode
            prefs.updated_at = datetime.utcnow()
        else:
            prefs = UserPrefs(
                user_key=user_key,
                approval_mode=approval_mode
            )
            db.add(prefs)
        db.commit()
        db.refresh(prefs)
        return prefs
