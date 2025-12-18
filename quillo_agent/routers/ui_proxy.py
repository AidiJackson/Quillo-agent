"""
UI Proxy (BFF) router - Frontend-facing endpoints without API key exposure
"""
import hmac
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import settings

# Track if dev bypass warning has been logged (log once, not every request)
_dev_bypass_logged = False
from ..db import get_db
from ..schemas import (
    RouteRequest, RouteResponse,
    PlanRequest, PlanResponse,
    AskRequest, AskResponse,
    ProfileIn, ProfileOut,
    FeedbackIn, FeedbackOut,
    ExecuteRequest, ExecuteResponse,
    JudgmentRequest, JudgmentResponse
)
from ..services import quillo, advice, memory as memory_service
from ..services.execution import execution_service
from ..services.judgment import assess_stakes, build_explanation, format_for_user


# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/ui/api", tags=["ui-proxy"])


class AuthStatusResponse(BaseModel):
    """Auth status response (never exposes secrets)"""
    env: str
    ui_token_required: bool
    ui_token_configured: bool
    hint: str | None = None


def verify_ui_token(x_ui_token: str = Header(None, alias="X-UI-Token")) -> str:
    """
    Verify UI token for frontend requests.

    For MVP, uses a simple shared token from env.
    In production, this should be replaced with session-based auth.

    Dev mode behavior:
    - If QUILLO_UI_TOKEN is NOT set: bypass auth entirely (log warning once)
    - If QUILLO_UI_TOKEN IS set: require valid token

    Production behavior:
    - Always require QUILLO_UI_TOKEN to be configured
    - Always require valid X-UI-Token header
    - Use constant-time comparison to prevent timing attacks

    Args:
        x_ui_token: UI token from X-UI-Token header

    Returns:
        The validated token or "dev-bypass"

    Raises:
        HTTPException: If token is missing or invalid
    """
    global _dev_bypass_logged

    # Dev mode with no token configured = bypass (safe for local dev)
    if settings.app_env == "dev" and not settings.quillo_ui_token:
        if not _dev_bypass_logged:
            logger.warning("DEV MODE: UI token bypass active (QUILLO_UI_TOKEN not set)")
            _dev_bypass_logged = True
        return "dev-bypass"

    # From here, token is required (either prod, or dev with token configured)
    if not settings.quillo_ui_token:
        logger.error("QUILLO_UI_TOKEN not configured in production mode")
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: UI token not set"
        )

    if not x_ui_token:
        logger.warning("UI request rejected: missing X-UI-Token header")
        raise HTTPException(
            status_code=401,
            detail="UI token missing or invalid"
        )

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(x_ui_token, settings.quillo_ui_token):
        logger.warning("UI request rejected: invalid X-UI-Token")
        raise HTTPException(
            status_code=403,
            detail="UI token missing or invalid"
        )

    return x_ui_token


@router.get("/health")
async def ui_health_check():
    """
    Health check endpoint for UI (no auth required).

    Returns:
        Status object
    """
    return {"status": "ok", "service": "quillo-ui-proxy"}


@router.get("/auth/status", response_model=AuthStatusResponse)
async def ui_auth_status():
    """
    Auth status endpoint for UI diagnostics (no auth required, no secrets exposed).

    Returns status booleans so the frontend can display appropriate messaging
    about whether UI token auth is configured and required.

    This endpoint is intentionally unauthenticated so the frontend can always
    check auth status, even when misconfigured.

    Returns:
        AuthStatusResponse with env, ui_token_required, ui_token_configured, hint
    """
    is_dev = settings.app_env == "dev"
    token_configured = bool(settings.quillo_ui_token)
    token_required = not is_dev or token_configured

    hint = None
    if is_dev and not token_configured:
        hint = "Dev bypass active. Set QUILLO_UI_TOKEN and VITE_UI_TOKEN to enable auth."

    return AuthStatusResponse(
        env=settings.app_env,
        ui_token_required=token_required,
        ui_token_configured=token_configured,
        hint=hint
    )


@router.post("/judgment", response_model=JudgmentResponse)
@limiter.limit("30/minute")
async def ui_explain_judgment(
    request: Request,
    payload: JudgmentRequest,
    token: str = Depends(verify_ui_token)
) -> JudgmentResponse:
    """
    UI proxy for judgment explanation.

    Provides conversational explanation of what Quillo sees and recommends.
    Works offline - no LLM required, pure heuristic-based assessment.
    Rate limited to 30 requests per minute per IP.

    Args:
        request: FastAPI request (for rate limiting)
        payload: JudgmentRequest with text, user_id, intent, context
        token: Validated UI token

    Returns:
        JudgmentResponse with stakes assessment and formatted explanation
    """
    logger.info(f"UI POST /judgment: user_id={payload.user_id}, intent={payload.intent}")

    # Assess stakes
    stakes = assess_stakes(payload.text)
    logger.debug(f"Stakes assessed as: {stakes}")

    # Build context observation
    if payload.intent:
        context = f"a request for {payload.intent}"
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
        intent=payload.intent
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


@router.post("/route", response_model=RouteResponse)
@limiter.limit("30/minute")
async def ui_route_intent(
    request: Request,
    payload: RouteRequest,
    token: str = Depends(verify_ui_token)
) -> RouteResponse:
    """
    UI proxy for intent routing.

    Calls underlying service directly without requiring API key.
    Rate limited to 30 requests per minute per IP.

    Args:
        request: FastAPI request (for rate limiting)
        payload: RouteRequest with text, user_id, context
        token: Validated UI token

    Returns:
        RouteResponse with intent, reasons, and slots
    """
    logger.info(f"UI POST /route: user_id={payload.user_id}")
    response = await quillo.route(
        text=payload.text,
        user_id=payload.user_id
    )
    return response


@router.post("/plan", response_model=PlanResponse)
@limiter.limit("30/minute")
async def ui_generate_plan(
    request: Request,
    payload: PlanRequest,
    token: str = Depends(verify_ui_token)
) -> PlanResponse:
    """
    UI proxy for plan generation.

    Calls underlying service directly without requiring API key.
    Rate limited to 30 requests per minute per IP.

    Args:
        request: FastAPI request (for rate limiting)
        payload: PlanRequest with intent, slots, text, user_id
        token: Validated UI token

    Returns:
        PlanResponse with steps and trace_id
    """
    logger.info(f"UI POST /plan: intent={payload.intent}, user_id={payload.user_id}")
    response = await quillo.plan(
        intent=payload.intent,
        slots=payload.slots,
        text=payload.text,
        user_id=payload.user_id
    )
    return response


@router.post("/ask", response_model=AskResponse)
@limiter.limit("30/minute")
async def ui_ask_quillopreneur(
    request: Request,
    payload: AskRequest,
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> AskResponse:
    """
    UI proxy for Quillopreneur business advice.

    Calls underlying service directly without requiring API key.
    Rate limited to 30 requests per minute per IP.

    Args:
        request: FastAPI request (for rate limiting)
        payload: AskRequest with text and optional user_id
        db: Database session
        token: Validated UI token

    Returns:
        AskResponse with answer, model, and trace_id
    """
    import uuid
    logger.info(f"UI POST /ask: user_id={payload.user_id}")

    # Generate trace ID
    trace_id = str(uuid.uuid4())

    # Get business advice using the service layer
    answer, model = await advice.answer_business_question(
        text=payload.text,
        user_id=payload.user_id,
        db=db
    )

    return AskResponse(
        answer=answer,
        model=model,
        trace_id=trace_id
    )


@router.get("/memory/profile", response_model=ProfileOut)
async def ui_get_profile(
    user_id: str = Query(..., description="User identifier"),
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> ProfileOut:
    """
    UI proxy for getting user profile.

    Calls underlying service directly without requiring API key.

    Args:
        user_id: User identifier
        db: Database session
        token: Validated UI token

    Returns:
        ProfileOut with markdown content and timestamp
    """
    logger.info(f"UI GET /memory/profile: user_id={user_id}")
    profile_md = memory_service.get_or_init_profile(db, user_id)

    # Get updated_at timestamp
    from ..models import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    updated_at = profile.updated_at.isoformat() if profile else ""

    return ProfileOut(profile_md=profile_md, updated_at=updated_at)


@router.post("/memory/profile", response_model=ProfileOut)
async def ui_update_profile(
    payload: ProfileIn,
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> ProfileOut:
    """
    UI proxy for updating user profile.

    Calls underlying service directly without requiring API key.

    Args:
        payload: ProfileIn with user_id and profile_md
        db: Database session
        token: Validated UI token

    Returns:
        ProfileOut with updated content and timestamp
    """
    logger.info(f"UI POST /memory/profile: user_id={payload.user_id}")
    updated_at = memory_service.update_profile(
        db,
        payload.user_id,
        payload.profile_md
    )
    return ProfileOut(
        profile_md=payload.profile_md,
        updated_at=updated_at.isoformat()
    )


@router.post("/feedback", response_model=FeedbackOut)
async def ui_record_feedback(
    payload: FeedbackIn,
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> FeedbackOut:
    """
    UI proxy for recording feedback.

    Calls underlying service directly without requiring API key.

    Args:
        payload: FeedbackIn with user_id, tool, outcome, signals
        db: Database session
        token: Validated UI token

    Returns:
        FeedbackOut confirmation
    """
    logger.info(f"UI POST /feedback: user_id={payload.user_id}, tool={payload.tool}")
    memory_service.record_feedback(
        db,
        payload.user_id,
        payload.tool,
        payload.outcome,
        payload.signals
    )
    return FeedbackOut(ok=True)


@router.post("/execute", response_model=ExecuteResponse)
@limiter.limit("30/minute")
async def ui_execute_plan(
    request: Request,
    payload: ExecuteRequest,
    token: str = Depends(verify_ui_token)
) -> ExecuteResponse:
    """
    UI proxy for plan execution.

    Executes a plan by running each step with LLM-based tool simulation.
    Safe execution - no external actions performed.
    Rate limited to 30 requests per minute per IP.

    Args:
        request: FastAPI request (for rate limiting)
        payload: ExecuteRequest with intent, slots, plan_steps, etc.
        token: Validated UI token

    Returns:
        ExecuteResponse with output_text, artifacts, trace_id, provider, warnings
    """
    import uuid
    logger.info(f"UI POST /execute: intent={payload.intent}, user_id={payload.user_id}, dry_run={payload.dry_run}")

    # Generate trace ID
    trace_id = str(uuid.uuid4())

    # Execute the plan
    output_text, artifacts, provider_used, warnings = await execution_service.execute_plan(
        text=payload.text,
        intent=payload.intent,
        slots=payload.slots,
        plan_steps=payload.plan_steps,
        user_id=payload.user_id,
        dry_run=payload.dry_run
    )

    return ExecuteResponse(
        output_text=output_text,
        artifacts=artifacts,
        trace_id=trace_id,
        provider_used=provider_used,
        warnings=warnings
    )
