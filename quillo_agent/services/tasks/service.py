"""
Task Intent service layer
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from loguru import logger

from .models import TaskIntent, TaskIntentStatus
from .repo import TaskIntentRepository
from ..user_prefs.service import UserPrefsService


def generate_scope(intent_text: str) -> Tuple[List[str], List[str], str]:
    """
    Generate deterministic task scope (will_do, wont_do, done_when).

    No LLM calls - uses keyword matching and templates only.

    Args:
        intent_text: The task intent text

    Returns:
        Tuple of (will_do, wont_do, done_when)
    """
    intent_lower = intent_text.lower()

    # Base will_do (always included)
    will_do = [
        "Draft outputs based strictly on the information you provided.",
        "Keep language professional and clear unless you specify otherwise.",
        "Flag missing info needed to produce a high-quality result.",
    ]

    # Keyword shaping (deterministic)
    if "email" in intent_lower or "reply" in intent_lower or "message" in intent_lower:
        will_do.append("Draft message replies for review.")

    if "summarize" in intent_lower or "thread" in intent_lower or "summary" in intent_lower:
        will_do.append("Summarize and extract action items for review.")

    if "argue" in intent_lower or "negotiate" in intent_lower or "case" in intent_lower:
        will_do.append("Prepare a structured case with options for review.")

    # Enforce max 5 bullets
    will_do = will_do[:5]

    # Base wont_do (always included - safety bullets)
    wont_do = [
        "Won't send messages or contact anyone on your behalf.",
        "Won't log into accounts, make purchases, or change external systems.",
        "Won't claim facts are verified unless you fetch Evidence separately.",
    ]

    # Enforce max 5 bullets
    wont_do = wont_do[:5]

    # Default done_when
    done_when = "Done when drafts are ready for your review in the app."

    return will_do, wont_do, done_when


class TaskIntentService:
    """Service layer for task intent operations"""

    @staticmethod
    def create_intent(
        db: Session,
        intent_text: str,
        origin_chat_id: Optional[str] = None,
        user_key: Optional[str] = None,
        scope_will_do: Optional[List[str]] = None,
        scope_wont_do: Optional[List[str]] = None,
        scope_done_when: Optional[str] = None,
        approval_mode: Optional[str] = None
    ) -> TaskIntent:
        """
        Create a new task intent.

        Args:
            db: Database session
            intent_text: The task intent text (required)
            origin_chat_id: Optional chat/conversation ID where this originated
            user_key: Optional user identifier
            scope_will_do: What the task will do (auto-generated if not provided)
            scope_wont_do: What the task won't do (auto-generated if not provided)
            scope_done_when: When the task is considered done (auto-generated if not provided)
            approval_mode: Optional override for approval mode (defaults to user prefs)

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

        # Auto-generate scope if not provided
        if scope_will_do is None or scope_wont_do is None or scope_done_when is None:
            logger.info("Generating task scope (deterministic)")
            generated_will_do, generated_wont_do, generated_done_when = generate_scope(intent_text.strip())
            scope_will_do = scope_will_do or generated_will_do
            scope_wont_do = scope_wont_do or generated_wont_do
            scope_done_when = scope_done_when or generated_done_when

        # Snapshot approval_mode from user prefs if not explicitly provided
        if approval_mode is None:
            # Determine user_key for prefs lookup (default to "global")
            prefs_user_key = user_key or "global"
            logger.info(f"Fetching user prefs for approval_mode snapshot: user_key={prefs_user_key}")
            user_prefs = UserPrefsService.get_prefs(db, prefs_user_key)
            approval_mode = user_prefs.approval_mode
            logger.info(f"Snapshotted approval_mode from prefs: {approval_mode}")

        task_intent = TaskIntentRepository.create(
            db=db,
            intent_text=intent_text.strip(),
            origin_chat_id=origin_chat_id,
            user_key=user_key,
            scope_will_do=scope_will_do,
            scope_wont_do=scope_wont_do,
            scope_done_when=scope_done_when,
            approval_mode=approval_mode
        )

        logger.info(f"Created task intent: id={task_intent.id}, status={task_intent.status}, approval_mode={task_intent.approval_mode}")
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
