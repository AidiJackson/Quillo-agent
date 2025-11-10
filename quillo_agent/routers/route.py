"""
Intent routing endpoint
"""
from fastapi import APIRouter
from loguru import logger
from ..schemas import RouteRequest, RouteResponse
from ..services import quillo

router = APIRouter(prefix="/route", tags=["routing"])


@router.post("", response_model=RouteResponse)
async def route_intent(request: RouteRequest) -> RouteResponse:
    """
    Route user input to appropriate intent.

    Args:
        request: RouteRequest with text, user_id, context

    Returns:
        RouteResponse with intent, reasons, and slots
    """
    logger.info(f"POST /route: user_id={request.user_id}")
    response = await quillo.route(
        text=request.text,
        user_id=request.user_id
    )
    return response
