"""
Task Plan Service Layer (v2 Phase 1)
"""
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from .models import TaskPlan, TaskPlanStatus
from .plan_repo import TaskPlanRepository
from .plan_generator import generate_plan
from .service import TaskIntentService


class TaskPlanService:
    """Service layer for task plan operations"""

    @staticmethod
    def create_plan(
        db: Session,
        task_intent_id: str
    ) -> TaskPlan:
        """
        Create (or replace) a plan for a task intent.

        Args:
            db: Database session
            task_intent_id: ID of the task intent

        Returns:
            Created TaskPlan instance

        Raises:
            ValueError: If task intent doesn't exist
        """
        # Verify task intent exists
        task_intent = TaskIntentService.get_by_id(db, task_intent_id)
        if not task_intent:
            raise ValueError(f"Task intent {task_intent_id} not found")

        logger.info(f"Generating plan for task {task_intent_id}: {task_intent.intent_text[:50]}...")

        # Generate plan using deterministic generator
        plan_steps, summary = generate_plan(task_intent.intent_text)

        logger.info(f"Generated {len(plan_steps)} steps for task {task_intent_id}")

        # Create or replace plan in database
        plan = TaskPlanRepository.create_or_replace(
            db=db,
            task_intent_id=task_intent_id,
            plan_steps=plan_steps,
            summary=summary
        )

        logger.info(f"Created plan {plan.id} for task {task_intent_id}")
        return plan

    @staticmethod
    def get_plan(db: Session, task_intent_id: str) -> Optional[TaskPlan]:
        """
        Get plan for a task intent.

        Args:
            db: Database session
            task_intent_id: ID of the task intent

        Returns:
            TaskPlan if exists, None otherwise
        """
        return TaskPlanRepository.get_by_task_id(db, task_intent_id)

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
        return TaskPlanRepository.update_status(db, plan_id, status)

    @staticmethod
    def approve_plan(
        db: Session,
        task_intent_id: str,
        user_key: Optional[str] = None
    ) -> Optional[TaskPlan]:
        """
        Approve a plan for a task intent.

        Sets status=approved and approved_at=now.
        Idempotent: if already approved, returns unchanged.

        Args:
            db: Database session
            task_intent_id: ID of the task intent
            user_key: Optional user identifier (for future use)

        Returns:
            Approved TaskPlan if found, None otherwise

        Raises:
            ValueError: If task intent doesn't exist
        """
        # Verify task intent exists
        task_intent = TaskIntentService.get_by_id(db, task_intent_id)
        if not task_intent:
            raise ValueError(f"Task intent {task_intent_id} not found")

        logger.info(f"Approving plan for task {task_intent_id}")

        # Approve plan
        plan = TaskPlanRepository.approve_by_task_id(db, task_intent_id)

        if not plan:
            raise ValueError(f"No plan found for task {task_intent_id}")

        logger.info(f"Approved plan {plan.id} for task {task_intent_id}")
        return plan
