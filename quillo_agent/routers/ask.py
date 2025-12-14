"""
Quillopreneur business advice endpoint
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from loguru import logger
from ..db import get_db
from ..schemas import AskRequest, AskResponse
from ..services import advice
from ..auth import verify_api_key

router = APIRouter(prefix="/ask", tags=["advice"])


@router.post("", response_model=AskResponse)
async def ask_quillopreneur(
    request: AskRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> AskResponse:
    """
    Get business advice from Quillopreneur specialist.

    Args:
        request: AskRequest with text and optional user_id
        db: Database session
        api_key: Verified API key (from auth dependency)

    Returns:
        AskResponse with answer, model, and trace_id
    """
    logger.info(f"POST /ask: user_id={request.user_id}")

    # Generate trace ID for debugging
    trace_id = str(uuid.uuid4())

    # Get business advice
    answer, model = await advice.answer_business_question(
        text=request.text,
        user_id=request.user_id,
        db=db
    )

    return AskResponse(
        answer=answer,
        model=model,
        trace_id=trace_id
    )
