"""
Task Intent model (v1) and Task Plan model (v2)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum, JSON, ForeignKey
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

    # Task Scope v1
    scope_will_do = Column(JSON, nullable=True)  # list[str]
    scope_wont_do = Column(JSON, nullable=True)  # list[str]
    scope_done_when = Column(Text, nullable=True)  # str

    # Approval mode snapshot (v1)
    approval_mode = Column(String, nullable=False, default="plan_then_auto")  # ApprovalMode enum value


class TaskPlanStatus(str, enum.Enum):
    """Task plan status enum"""
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class TaskPlan(Base):
    """
    Task Plan model (v2 Phase 1)

    Stores the execution plan for a task intent.
    V2 Phase 1: storage and display only, no execution.
    """
    __tablename__ = "task_plans"

    id = Column(String, primary_key=True, default=generate_uuid)
    task_intent_id = Column(String, ForeignKey("task_intents.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Plan content
    plan_steps = Column(JSON, nullable=False)  # list[dict] - each step has: step_num, description, tool_name?, args?
    summary = Column(Text, nullable=True)  # Brief summary of what the plan will do
    status = Column(Enum(TaskPlanStatus), default=TaskPlanStatus.DRAFT, nullable=False)
