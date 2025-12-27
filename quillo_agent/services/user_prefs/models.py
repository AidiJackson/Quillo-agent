"""
User Preferences model (v1)
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import enum

from ...db import Base


class ApprovalMode(str, enum.Enum):
    """Task approval mode enum"""
    CONFIRM_EVERY_STEP = "confirm_every_step"
    PLAN_THEN_AUTO = "plan_then_auto"
    AUTO_LOWRISK_CONFIRM_HIGHRISK = "auto_lowrisk_confirm_highrisk"


class UserPrefs(Base):
    """
    User Preferences model (v1)

    Stores per-user preferences for task execution behavior.
    V1 only stores approval_mode.
    """
    __tablename__ = "user_prefs"

    user_key = Column(String, primary_key=True)  # Unique user identifier
    approval_mode = Column(String, default=ApprovalMode.PLAN_THEN_AUTO.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
