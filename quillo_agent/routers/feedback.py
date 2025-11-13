"""
Feedback recording endpoint
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from loguru import logger
from ..db import get_db
from ..schemas import FeedbackIn, FeedbackOut
from ..services import memory as memory_service

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut)
async def record_feedback(
    request: FeedbackIn,
    db: Session = Depends(get_db)
) -> FeedbackOut:
    """
    Record feedback event and update user profile.

    Args:
        request: FeedbackIn with user_id, tool, outcome, signals
        db: Database session

    Returns:
        FeedbackOut confirmation
    """
    logger.info(
        f"POST /feedback: user_id={request.user_id}, "
        f"tool={request.tool}, outcome={request.outcome}"
    )
    memory_service.record_feedback(
        db,
        request.user_id,
        request.tool,
        request.outcome,
        request.signals
    )
    return FeedbackOut(ok=True)
