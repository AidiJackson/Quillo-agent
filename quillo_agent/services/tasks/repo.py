"""
Task Intent repository layer
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from .models import TaskIntent, TaskIntentStatus


class TaskIntentRepository:
    """Repository for TaskIntent database operations"""

    @staticmethod
    def create(
        db: Session,
        intent_text: str,
        origin_chat_id: Optional[str] = None,
        user_key: Optional[str] = None,
        scope_will_do: Optional[List[str]] = None,
        scope_wont_do: Optional[List[str]] = None,
        scope_done_when: Optional[str] = None
    ) -> TaskIntent:
        """
        Create a new task intent.

        Args:
            db: Database session
            intent_text: The task intent text (required)
            origin_chat_id: Optional chat/conversation ID where this originated
            user_key: Optional user identifier (session-based or client-provided)
            scope_will_do: What the task will do (max 5 bullets)
            scope_wont_do: What the task won't do (max 5 bullets)
            scope_done_when: When the task is considered done

        Returns:
            Created TaskIntent instance
        """
        task_intent = TaskIntent(
            intent_text=intent_text,
            origin_chat_id=origin_chat_id,
            user_key=user_key,
            status=TaskIntentStatus.APPROVED,  # v1: all start as approved
            scope_will_do=scope_will_do,
            scope_wont_do=scope_wont_do,
            scope_done_when=scope_done_when
        )
        db.add(task_intent)
        db.commit()
        db.refresh(task_intent)
        return task_intent

    @staticmethod
    def get_by_id(db: Session, intent_id: str) -> Optional[TaskIntent]:
        """
        Get a task intent by ID.

        Args:
            db: Database session
            intent_id: Task intent ID

        Returns:
            TaskIntent if found, None otherwise
        """
        return db.query(TaskIntent).filter(TaskIntent.id == intent_id).first()

    @staticmethod
    def list_by_user_key(
        db: Session,
        user_key: str,
        limit: int = 20
    ) -> List[TaskIntent]:
        """
        List task intents for a user (most recent first).

        Args:
            db: Database session
            user_key: User identifier
            limit: Max results to return

        Returns:
            List of TaskIntent instances
        """
        return (
            db.query(TaskIntent)
            .filter(TaskIntent.user_key == user_key)
            .order_by(TaskIntent.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_recent(db: Session, limit: int = 20) -> List[TaskIntent]:
        """
        List recent task intents globally (most recent first).

        For dev convenience - allows viewing all recent intents without user_key.

        Args:
            db: Database session
            limit: Max results to return

        Returns:
            List of TaskIntent instances
        """
        return (
            db.query(TaskIntent)
            .order_by(TaskIntent.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_status(
        db: Session,
        intent_id: str,
        status: TaskIntentStatus
    ) -> Optional[TaskIntent]:
        """
        Update task intent status.

        Args:
            db: Database session
            intent_id: Task intent ID
            status: New status

        Returns:
            Updated TaskIntent if found, None otherwise
        """
        task_intent = db.query(TaskIntent).filter(TaskIntent.id == intent_id).first()
        if task_intent:
            task_intent.status = status
            task_intent.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(task_intent)
        return task_intent
