"""
Plan generation endpoint
"""
from fastapi import APIRouter
from loguru import logger
from ..schemas import PlanRequest, PlanResponse
from ..services import quillo

router = APIRouter(prefix="/plan", tags=["planning"])


@router.post("", response_model=PlanResponse)
async def generate_plan(request: PlanRequest) -> PlanResponse:
    """
    Generate execution plan for given intent.

    Args:
        request: PlanRequest with intent, slots, text, user_id

    Returns:
        PlanResponse with steps and trace_id
    """
    logger.info(f"POST /plan: intent={request.intent}, user_id={request.user_id}")
    response = await quillo.plan(
        intent=request.intent,
        slots=request.slots,
        text=request.text,
        user_id=request.user_id
    )
    return response
