"""
Task Intent service layer
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from loguru import logger

from .models import TaskIntent, TaskIntentStatus
from .repo import TaskIntentRepository


class TaskIntentService:
    """Service layer for task intent operations"""

    @staticmethod
    def create_intent(
        db: Session,
        intent_text: str,
        origin_chat_id: Optional[str] = None,
        user_key: Optional[str] = None
    ) -> TaskIntent:
        """
        Create a new task intent.

        Args:
            db: Database session
            intent_text: The task intent text (required)
            origin_chat_id: Optional chat/conversation ID where this originated
            user_key: Optional user identifier

        Returns:
            Created TaskIntent instance

        Raises:
            ValueError: If intent_text is empty
        """
        if not intent_text or not intent_text.strip():
            raise ValueError("intent_text is required and cannot be empty")

        logger.info(
            f"Creating task intent: user_key={user_key}, "
            f"origin_chat_id={origin_chat_id}, "
            f"text_len={len(intent_text)}"
        )

        task_intent = TaskIntentRepository.create(
            db=db,
            intent_text=intent_text.strip(),
            origin_chat_id=origin_chat_id,
            user_key=user_key
        )

        logger.info(f"Created task intent: id={task_intent.id}, status={task_intent.status}")
        return task_intent

    @staticmethod
    def list_intents(
        db: Session,
        user_key: Optional[str] = None,
        limit: int = 20
    ) -> List[TaskIntent]:
        """
        List task intents (most recent first).

        If user_key provided, filter by user.
        Otherwise, return recent intents globally (for dev convenience).

        Args:
            db: Database session
            user_key: Optional user identifier to filter by
            limit: Max results (default 20)

        Returns:
            List of TaskIntent instances
        """
        if user_key:
            logger.info(f"Listing task intents for user_key={user_key}, limit={limit}")
            intents = TaskIntentRepository.list_by_user_key(db, user_key, limit)
        else:
            logger.info(f"Listing recent task intents globally, limit={limit}")
            intents = TaskIntentRepository.list_recent(db, limit)

        logger.info(f"Found {len(intents)} task intents")
        return intents

    @staticmethod
    def get_intent(db: Session, intent_id: str) -> Optional[TaskIntent]:
        """
        Get a task intent by ID.

        Args:
            db: Database session
            intent_id: Task intent ID

        Returns:
            TaskIntent if found, None otherwise
        """
        return TaskIntentRepository.get_by_id(db, intent_id)

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
        logger.info(f"Updating task intent status: id={intent_id}, status={status}")
        task_intent = TaskIntentRepository.update_status(db, intent_id, status)
        if task_intent:
            logger.info(f"Updated task intent: id={task_intent.id}, status={task_intent.status}")
        else:
            logger.warning(f"Task intent not found: id={intent_id}")
        return task_intent
