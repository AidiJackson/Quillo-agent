"""
Judgment Explanation Layer endpoint

Provides conversational explanations of intent and stakes before execution.
"""
from fastapi import APIRouter, Depends
from loguru import logger
from ..schemas import JudgmentRequest, JudgmentResponse
from ..services.judgment import assess_stakes, build_explanation, format_for_user
from ..auth import verify_api_key

router = APIRouter(prefix="/judgment", tags=["judgment"])


@router.post("", response_model=JudgmentResponse)
async def explain_judgment(
    request: JudgmentRequest,
    api_key: str = Depends(verify_api_key)
) -> JudgmentResponse:
    """
    Analyze user input and provide conversational explanation of stakes and recommendation.

    This endpoint sits before /plan and /execute, providing human-readable
    narration of what Quillo sees and recommends.

    Args:
        request: JudgmentRequest with text, user_id, intent, context
        api_key: Validated API key (from auth dependency)

    Returns:
        JudgmentResponse with stakes assessment and formatted explanation
    """
    logger.info(f"POST /judgment: user_id={request.user_id}, intent={request.intent}")

    # Assess stakes
    stakes = assess_stakes(request.text)
    logger.debug(f"Stakes assessed as: {stakes}")

    # Build context observation
    if request.intent:
        context = f"a request for {request.intent}"
    else:
        context = "your request"

    # Build recommendation based on stakes
    if stakes == "high":
        recommendation = (
            "carefully draft a response, testing multiple approaches to ensure "
            "we get the tone and message exactly right"
        )
    elif stakes == "medium":
        recommendation = (
            "create a professional response that addresses your needs while "
            "maintaining clarity and appropriate tone"
        )
    else:
        recommendation = "handle this request directly"

    # Build explanation
    explanation = build_explanation(
        context=context,
        stakes=stakes,
        recommendation=recommendation,
        intent=request.intent
    )

    # Format for user
    formatted_message = format_for_user(explanation)

    return JudgmentResponse(
        stakes=stakes,
        what_i_see=explanation["what_i_see"],
        why_it_matters=explanation.get("why_it_matters"),
        recommendation=explanation["recommendation"],
        requires_confirmation=explanation["requires_confirmation"],
        formatted_message=formatted_message
    )
