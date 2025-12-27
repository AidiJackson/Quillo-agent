"""
Task Intent model (v1)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

from ...db import Base


def generate_uuid():
    """Generate UUID as string"""
    return str(uuid.uuid4())


class TaskIntentStatus(str, enum.Enum):
    """Task intent status enum"""
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskIntent(Base):
    """
    Task Intent model (v1)

    Stores user task intents for future orchestration.
    V1 is minimal: just intent storage, no execution/workers.
    """
    __tablename__ = "task_intents"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    status = Column(Enum(TaskIntentStatus), default=TaskIntentStatus.APPROVED, nullable=False)
    intent_text = Column(Text, nullable=False)
    origin_chat_id = Column(String, nullable=True)
    user_key = Column(String, nullable=True)
