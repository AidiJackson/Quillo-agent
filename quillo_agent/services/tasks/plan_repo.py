"""
Task Plan Repository (v2 Phase 1)
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .models import TaskPlan, TaskPlanStatus


class TaskPlanRepository:
    """Repository for TaskPlan database operations"""

    @staticmethod
    def create_or_replace(
        db: Session,
        task_intent_id: str,
        plan_steps: List[Dict],
        summary: Optional[str] = None
    ) -> TaskPlan:
        """
        Create or replace a plan for a task intent.

        Args:
            db: Database session
            task_intent_id: FK to task_intents.id
            plan_steps: List of plan step dicts
            summary: Optional plan summary

        Returns:
            Created or updated TaskPlan instance
        """
        # Check if plan already exists
        existing = db.query(TaskPlan).filter(
            TaskPlan.task_intent_id == task_intent_id
        ).first()

        if existing:
            # Replace existing plan
            existing.plan_steps = plan_steps
            existing.summary = summary
            existing.status = TaskPlanStatus.DRAFT  # Reset to draft
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new plan
            plan = TaskPlan(
                task_intent_id=task_intent_id,
                plan_steps=plan_steps,
                summary=summary,
                status=TaskPlanStatus.DRAFT
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)
            return plan

    @staticmethod
    def get_by_task_id(db: Session, task_intent_id: str) -> Optional[TaskPlan]:
        """
        Get plan by task intent ID.

        Args:
            db: Database session
            task_intent_id: FK to task_intents.id

        Returns:
            TaskPlan if found, None otherwise
        """
        return db.query(TaskPlan).filter(
            TaskPlan.task_intent_id == task_intent_id
        ).first()

    @staticmethod
    def update_status(
        db: Session,
        plan_id: str,
        status: TaskPlanStatus
    ) -> Optional[TaskPlan]:
        """
        Update plan status.

        Args:
            db: Database session
            plan_id: Plan ID
            status: New status

        Returns:
            Updated TaskPlan if found, None otherwise
        """
        plan = db.query(TaskPlan).filter(TaskPlan.id == plan_id).first()
        if plan:
            plan.status = status
            db.commit()
            db.refresh(plan)
        return plan

    @staticmethod
    def approve_by_task_id(
        db: Session,
        task_intent_id: str
    ) -> Optional[TaskPlan]:
        """
        Approve a plan by task intent ID.

        Sets status=approved and approved_at=now.
        Idempotent: if already approved, returns unchanged.

        Args:
            db: Database session
            task_intent_id: FK to task_intents.id

        Returns:
            Approved TaskPlan if found, None otherwise
        """
        plan = db.query(TaskPlan).filter(
            TaskPlan.task_intent_id == task_intent_id
        ).first()

        if not plan:
            return None

        # Idempotent: if already approved, return as-is
        if plan.status == TaskPlanStatus.APPROVED:
            return plan

        # Set status and approved_at
        plan.status = TaskPlanStatus.APPROVED
        plan.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(plan)
        return plan
