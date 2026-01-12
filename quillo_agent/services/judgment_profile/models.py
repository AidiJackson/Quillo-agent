"""
Judgment Profile model (v1) - explicit, user-controlled constraints only
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, UniqueConstraint
from ...db import Base


class JudgmentProfile(Base):
    """
    Judgment Profile model (v1)

    Stores explicit, user-confirmed judgment preferences per user.
    NO automatic inference or learning - all fields must be explicitly set
    with source="explicit" and confirmed_at timestamp.

    V1 stores the entire profile as JSON text to allow flexible schema evolution.
    """
    __tablename__ = "judgment_profiles"

    # Use user_key as primary key for 1:1 relationship
    user_key = Column(String, primary_key=True)  # Unique user identifier

    # Store profile as JSON text (validated by service layer)
    profile_json = Column(Text, nullable=False)

    # Version tracking for schema evolution
    version = Column(String, default="judgment_profile_v1", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Ensure one profile per user (redundant with PK but explicit)
    __table_args__ = (
        UniqueConstraint('user_key', name='uq_judgment_profile_user_key'),
    )
