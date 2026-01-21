"""
UI Proxy (BFF) router - Frontend-facing endpoints without API key exposure
"""
import hmac
import os
from typing import Optional, List
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
    JudgmentRequest, JudgmentResponse,
    MultiAgentRequest, MultiAgentResponse, MultiAgentMessage,
    EvidenceRequest, EvidenceResponse,
    TaskIntentCreate, TaskIntentOut,
    TaskPlanOut,
    UserPrefsUpdate, UserPrefsOut,
    JudgmentProfileCreateUpdate, JudgmentProfileResponse, JudgmentProfileDeleteResponse
)
from ..services import quillo, advice, memory as memory_service
from ..services.execution import execution_service
from ..services.judgment import assess_stakes, build_explanation, format_for_user
from ..services.interaction_contract import enforce_contract, ActionIntent
from ..services.multi_agent_chat import run_multi_agent_chat
from ..services.evidence import retrieve_evidence
from ..services.tasks.service import TaskIntentService
from ..services.tasks.plan_service import TaskPlanService
from ..services.user_prefs.service import UserPrefsService
from ..services.judgment_profile import (
    get_profile as get_judgment_profile,
    upsert_profile as upsert_judgment_profile,
    delete_profile as delete_judgment_profile,
    profile_exists as judgment_profile_exists,
    JudgmentProfileValidationError
)
from ..trust_contract import (
    classify_prompt_needs_evidence,
    enforce_no_assumptions,
    format_model_output,
    format_synthesis,
    extract_disagreements,
    detect_consequence
)
from ..self_explanation import (
    is_transparency_query,
    build_transparency_card,
    build_micro_disclosures
)


# Rate limiter instance
limiter = Limiter(key_func=get_remote_address, enabled=(os.getenv("PYTEST_RUNNING") is None))

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


class ConfigResponse(BaseModel):
    """Configuration response for frontend"""
    raw_chat_mode: bool


@router.get("/config", response_model=ConfigResponse)
async def ui_config():
    """
    Configuration endpoint for UI (no auth required).

    Returns mode settings so the frontend can adapt behavior.
    This is unauthenticated so the frontend can check config at any time.

    Returns:
        ConfigResponse with raw_chat_mode setting
    """
    return ConfigResponse(
        raw_chat_mode=settings.raw_chat_mode
    )


class RawAuditResponse(BaseModel):
    """Raw mode audit response for QA verification (no secrets)"""
    raw_chat_mode: bool
    message_shape: str  # "user_only" | "system+user"
    profile_prepending_enabled: bool
    truncation_enabled: bool
    offline_template_style: str  # "neutral" | "advisor"


@router.get("/raw-audit", response_model=RawAuditResponse)
async def ui_raw_audit():
    """
    Raw mode audit endpoint for QA verification (no auth required, no secrets).

    Returns diagnostic information about RAW_CHAT_MODE behavior:
    - Whether raw mode is enabled
    - Message shape (user_only vs system+user)
    - Whether profile prepending is active
    - Whether truncation is active
    - Offline template style (neutral vs advisor)

    This endpoint is unauthenticated so it can be used for diagnostics.

    Returns:
        RawAuditResponse with raw mode configuration details
    """
    is_raw_mode = settings.raw_chat_mode

    return RawAuditResponse(
        raw_chat_mode=is_raw_mode,
        message_shape="user_only" if is_raw_mode else "system+user",
        profile_prepending_enabled=not is_raw_mode,
        truncation_enabled=not is_raw_mode,
        offline_template_style="neutral" if is_raw_mode else "advisor"
    )


class ModelStatusResponse(BaseModel):
    """Model status response (diagnostic, no secrets)"""
    raw_chat_model: str
    claude_agent_model: str
    challenger_agent_model: str
    gemini_agent_model: str
    primary_synthesis_model: str


@router.get("/model-status", response_model=ModelStatusResponse)
async def ui_model_status():
    """
    Model status diagnostic endpoint (no auth required, no secrets).

    Returns the configured OpenRouter model strings for each agent.
    Useful for debugging multi-agent reliability issues.

    This endpoint is unauthenticated so it can be used for diagnostics.

    Returns:
        ModelStatusResponse with all configured model strings
    """
    return ModelStatusResponse(
        raw_chat_model=settings.openrouter_chat_model,
        claude_agent_model=settings.openrouter_claude_agent_model,
        challenger_agent_model=settings.openrouter_challenger_agent_model,
        gemini_agent_model=settings.openrouter_gemini_agent_model,
        primary_synthesis_model=settings.openrouter_chat_model
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
    Now enforces Interaction Contract v1 for consistent conversational behavior.
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

    # Determine action intent based on text and context
    action_intent = _determine_action_intent(payload.text, payload.intent)
    logger.debug(f"Action intent determined as: {action_intent}")

    # Check integration availability (for MVP, none are available yet)
    has_integrations = {
        "email": False,
        "calendar": False,
        "crm": False
    }

    # Enforce interaction contract
    contract_response = enforce_contract(
        message=payload.text,
        stakes=stakes,
        intent=action_intent.value,
        has_integrations=has_integrations
    )
    logger.debug(f"Contract response mode: {contract_response['mode']}")

    # Build context observation (legacy behavior for backward compatibility)
    if payload.intent:
        context = f"a request for {payload.intent}"
    else:
        context = "your request"

    # Build recommendation based on stakes (legacy)
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

    # Build explanation (legacy)
    explanation = build_explanation(
        context=context,
        stakes=stakes,
        recommendation=recommendation,
        intent=payload.intent
    )

    # Format for user (legacy)
    formatted_message = format_for_user(explanation)

    # Return combined response (legacy fields + contract fields)
    return JudgmentResponse(
        stakes=stakes,
        what_i_see=explanation["what_i_see"],
        why_it_matters=explanation.get("why_it_matters"),
        recommendation=explanation["recommendation"],
        requires_confirmation=contract_response["requires_confirmation"],
        formatted_message=formatted_message,
        # Contract v1 fields
        mode=contract_response["mode"],
        assistant_message=contract_response["assistant_message"],
        questions=contract_response.get("questions"),
        suggested_next_step=contract_response.get("suggested_next_step")
    )


def _determine_action_intent(text: str, intent_hint: Optional[str] = None) -> ActionIntent:
    """
    Determine the action intent from user text.

    Args:
        text: User input text
        intent_hint: Optional intent hint from routing

    Returns:
        ActionIntent enum value
    """
    text_lower = text.lower()

    # Check for external integration requests
    external_keywords = [
        "inbox", "email", "emails", "calendar", "schedule", "crm"
    ]
    if any(keyword in text_lower for keyword in external_keywords):
        return ActionIntent.EXTERNAL_INTEGRATION

    # Check for execution intent
    execution_keywords = [
        "send", "create", "draft", "write", "make", "build",
        "schedule", "book", "delete", "update", "fix"
    ]
    if any(text_lower.startswith(keyword) for keyword in execution_keywords):
        return ActionIntent.EXECUTE

    # Check for planning intent
    planning_keywords = [
        "plan", "strategy", "approach", "how should i", "what's the best way"
    ]
    if any(keyword in text_lower for keyword in planning_keywords):
        return ActionIntent.PLAN

    # Default to chat only (questions, informational)
    return ActionIntent.CHAT_ONLY


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
    UI proxy for Quillopreneur business advice with TRUST CONTRACT v1 enforcement.

    TRUST CONTRACT BEHAVIORS:
    1. Evidence default-on: Auto-fetches evidence for factual/temporal prompts
    2. No assumptions: Asks clarifying questions if critical context is missing
    3. Evidence limitations: States clearly when evidence unavailable

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
    logger.info(f"UI POST /ask: user_id={payload.user_id}, trust_contract=v1")

    # Generate trace ID
    trace_id = str(uuid.uuid4())

    # SELF-EXPLANATION v1: Check for transparency query (short-circuit before any LLM calls)
    if is_transparency_query(payload.text):
        logger.info(f"[{trace_id}] Transparency query detected - returning transparency card")

        # Check judgment profile existence (safe DB read in transparency path)
        user_key_for_profile = payload.user_id if payload.user_id else "global"
        profile_present = False
        profile_check_failed = False
        try:
            profile_present = judgment_profile_exists(db, user_key_for_profile)
        except Exception as e:
            logger.warning(f"[{trace_id}] Profile existence check failed: {e}")
            profile_check_failed = True

        # Build state dict (for /ask, most flags are false since it's simpler than multi-agent)
        facts_used = []
        if profile_check_failed:
            facts_used.append({
                "text": "Profile availability could not be verified.",
                "source": "",
                "timestamp": ""
            })

        transparency_state = {
            "using_conversation_context": False,  # TODO: Enable when conversation storage implemented
            "using_session_context": False,  # Not yet implemented
            "using_profile": profile_present,  # True if judgment profile exists
            "using_evidence": False,  # Haven't fetched yet
            "stress_test_mode": False,  # /ask doesn't use stress test
            "facts_used": facts_used,
            "not_assuming": ["I'm not filling missing details without you confirming them."],
            "needs_from_user": []
        }

        transparency_card = build_transparency_card(transparency_state)

        return AskResponse(
            answer=transparency_card,
            model="self-explanation-v1",
            trace_id=trace_id
        )

    # TRUST CONTRACT STEP 1: Check for missing assumptions
    # Build context dict (for future: conversation history, attachments, etc.)
    context = {
        "has_previous_context": False,  # TODO: Check conversation storage
        "has_attachments": False
    }

    ok_to_proceed, questions = enforce_no_assumptions(payload.text, context)

    if not ok_to_proceed and questions:
        # Critical context missing - return questions without calling LLM
        logger.info(f"[{trace_id}] No-assumptions triggered: {len(questions)} questions")
        questions_text = "I need a few details before I can help (no guessing):\n\n"
        for i, question in enumerate(questions, 1):
            questions_text += f"{i}. {question}\n"

        return AskResponse(
            answer=questions_text.strip(),
            model="trust-contract-v1",
            trace_id=trace_id
        )

    # TRUST CONTRACT STEP 2: Check if evidence is needed
    needs_evidence = classify_prompt_needs_evidence(payload.text)
    evidence_block = None
    evidence_note = None

    if needs_evidence:
        logger.info(f"[{trace_id}] Evidence default-on triggered for prompt")
        try:
            evidence_response = await retrieve_evidence(payload.text)
            if evidence_response.ok and evidence_response.facts:
                # Build evidence block from facts
                evidence_lines = ["**Evidence (from web sources):**\n"]
                for fact in evidence_response.facts:
                    source = next((s for s in evidence_response.sources if s.id == fact.source_id), None)
                    source_label = f"{source.domain}" if source else "Unknown"
                    evidence_lines.append(f"- {fact.text} [{source_label}]")
                evidence_block = "\n".join(evidence_lines)
                logger.info(f"[{trace_id}] Evidence fetched: {len(evidence_response.facts)} facts from {len(evidence_response.sources)} sources")
            else:
                evidence_note = "⚠️ Evidence fetch attempted but no results found. Proceeding with limited factual certainty."
                logger.warning(f"[{trace_id}] Evidence fetch failed or empty")
        except Exception as e:
            evidence_note = "⚠️ Evidence temporarily unavailable. Response may have limited factual certainty."
            logger.error(f"[{trace_id}] Evidence fetch error: {e}")

    # Get business advice using the service layer
    # Note: Passing evidence_block to the answer_business_question is a future enhancement
    # For now, we prepend it to the response
    answer, model = await advice.answer_business_question(
        text=payload.text,
        user_id=payload.user_id,
        db=db
    )

    # TRUST CONTRACT STEP 3: Format response with evidence context
    final_answer = answer
    if evidence_block:
        final_answer = f"{evidence_block}\n\n{answer}"
    elif evidence_note:
        final_answer = f"{evidence_note}\n\n{answer}"

    # SELF-EXPLANATION v1: Add micro-disclosures if applicable
    micro_disclosures = build_micro_disclosures(
        using_evidence=bool(evidence_block),  # True if evidence was successfully fetched
        stress_test_mode=False,  # /ask doesn't use stress test mode
        using_conversation_context=False,  # TODO: Enable when conversation storage implemented
        using_profile=False  # /ask doesn't use profile yet
    )

    if micro_disclosures:
        final_answer = micro_disclosures + final_answer

    return AskResponse(
        answer=final_answer,
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


@router.post("/multi-agent", response_model=MultiAgentResponse)
@limiter.limit("30/minute")
async def ui_multi_agent_chat(
    request: Request,
    payload: MultiAgentRequest,
    token: str = Depends(verify_ui_token)
) -> MultiAgentResponse:
    """
    UI proxy for multi-agent chat with mode-based behavior.

    MODE BEHAVIORS:
    - normal: Raw peer replies from Claude/DeepSeek/Gemini with NO synthesis, NO evidence fetch,
              NO trust contract checks, NO stress test. Just natural model responses.
    - work: Full TRUST CONTRACT v1 + STRESS TEST v1 enforcement with structured outputs and synthesis.

    Rate limited to 30 requests per minute per IP.

    Args:
        request: FastAPI request (for rate limiting)
        payload: MultiAgentRequest with text, user_id, agents, mode
        token: Validated UI token

    Returns:
        MultiAgentResponse with messages, provider, trace_id
    """
    import uuid
    trace_id = str(uuid.uuid4())

    # Parse mode (case-insensitive, default to "normal")
    mode = (payload.mode or "normal").lower().strip()
    if mode not in ("normal", "work"):
        mode = "normal"

    logger.info(f"UI POST /multi-agent: user_id={payload.user_id}, mode={mode}, trace_id={trace_id}")

    # ============================================================
    # NORMAL MODE: Raw peer replies, no synthesis, no scaffolding
    # ============================================================
    if mode == "normal":
        # Run multi-agent chat in normal mode (bypasses all work-mode behaviors)
        messages_data, provider, fallback_reason, peers_unavailable = await run_multi_agent_chat(
            text=payload.text,
            user_id=payload.user_id,
            agents=payload.agents,
            trace_id=trace_id,
            evidence_context=None,  # No auto-evidence in normal mode
            stress_test_mode=False,  # No stress test in normal mode
            normal_mode=True  # Signal to skip synthesis
        )

        # Convert to MultiAgentMessage models
        messages = [MultiAgentMessage(**msg) for msg in messages_data]

        return MultiAgentResponse(
            messages=messages,
            provider=provider,
            trace_id=trace_id,
            fallback_reason=fallback_reason,
            peers_unavailable=peers_unavailable
        )

    # ============================================================
    # WORK MODE: Full trust contract + stress test + synthesis
    # ============================================================
    logger.info(f"[{trace_id}] Work mode: trust_contract=v1, stress_test=v1")

    # SELF-EXPLANATION v1: Check for transparency query (short-circuit before any LLM calls)
    if is_transparency_query(payload.text):
        logger.info(f"[{trace_id}] Transparency query detected in multi-agent - returning transparency card")

        # Check if this would be a stress test scenario
        stress_test_mode_check = detect_consequence(payload.text)

        # Check judgment profile existence (safe DB read in transparency path)
        user_key_for_profile = payload.user_id if payload.user_id else "global"
        profile_present = False
        profile_check_failed = False
        try:
            profile_present = judgment_profile_exists(db, user_key_for_profile)
        except Exception as e:
            logger.warning(f"[{trace_id}] Profile existence check failed: {e}")
            profile_check_failed = True

        # Build state dict for transparency card
        facts_used = []
        if profile_check_failed:
            facts_used.append({
                "text": "Profile availability could not be verified.",
                "source": "",
                "timestamp": ""
            })

        transparency_state = {
            "using_conversation_context": False,  # TODO: Enable when conversation storage implemented
            "using_session_context": False,  # Not yet implemented
            "using_profile": profile_present,  # True if judgment profile exists
            "using_evidence": False,  # Haven't fetched yet
            "stress_test_mode": stress_test_mode_check,
            "facts_used": facts_used,
            "not_assuming": ["I'm not filling missing details without you confirming them."],
            "needs_from_user": []
        }

        transparency_card = build_transparency_card(transparency_state)

        messages = [MultiAgentMessage(
            role="assistant",
            agent="quillo",
            content=transparency_card,
            model_id="self-explanation-v1",
            live=True,
            unavailable_reason=None
        )]

        return MultiAgentResponse(
            messages=messages,
            provider="self-explanation-v1",
            trace_id=trace_id,
            fallback_reason=None,
            peers_unavailable=False
        )

    # TRUST CONTRACT STEP 1: Check for missing assumptions
    context = {
        "has_previous_context": False,
        "has_attachments": False
    }

    ok_to_proceed, questions = enforce_no_assumptions(payload.text, context)

    if not ok_to_proceed and questions:
        # Return questions as a single message from Quillo
        logger.info(f"[{trace_id}] No-assumptions triggered in multi-agent: {len(questions)} questions")
        questions_text = "I need a few details before we can provide multi-agent perspectives (no guessing):\n\n"
        for i, question in enumerate(questions, 1):
            questions_text += f"{i}. {question}\n"

        messages = [MultiAgentMessage(
            role="assistant",
            agent="quillo",
            content=questions_text.strip(),
            model_id=None,
            live=True,
            unavailable_reason=None
        )]

        return MultiAgentResponse(
            messages=messages,
            provider="trust-contract-v1",
            trace_id=trace_id,
            fallback_reason=None,
            peers_unavailable=False
        )

    # TRUST CONTRACT STEP 2: Check if evidence is needed
    needs_evidence = classify_prompt_needs_evidence(payload.text)
    evidence_context = None

    if needs_evidence:
        logger.info(f"[{trace_id}] Evidence default-on triggered for multi-agent prompt")
        try:
            evidence_response = await retrieve_evidence(payload.text)
            if evidence_response.ok and evidence_response.facts:
                # Build evidence context for agents
                evidence_lines = ["Evidence (from web sources):"]
                for fact in evidence_response.facts:
                    source = next((s for s in evidence_response.sources if s.id == fact.source_id), None)
                    source_label = f"{source.domain}" if source else "Unknown"
                    evidence_lines.append(f"- {fact.text} [{source_label}]")
                evidence_context = "\n".join(evidence_lines)
                logger.info(f"[{trace_id}] Evidence fetched for multi-agent: {len(evidence_response.facts)} facts")
            else:
                evidence_context = "Evidence fetch attempted but no results found. Proceed with limited factual certainty."
                logger.warning(f"[{trace_id}] Evidence fetch failed or empty for multi-agent")
        except Exception as e:
            evidence_context = "Evidence temporarily unavailable. Responses may have limited factual certainty."
            logger.error(f"[{trace_id}] Evidence fetch error in multi-agent: {e}")

    # STRESS TEST v1: Check if consequence/decision detected
    stress_test_mode = detect_consequence(payload.text)
    if stress_test_mode:
        logger.info(f"[{trace_id}] STRESS TEST v1 activated - consequence detected")
    else:
        logger.info(f"[{trace_id}] Normal multi-agent mode - no consequence detected")

    # Run multi-agent chat with evidence context and stress test mode (work mode = with synthesis)
    messages_data, provider, fallback_reason, peers_unavailable = await run_multi_agent_chat(
        text=payload.text,
        user_id=payload.user_id,
        agents=payload.agents,
        trace_id=trace_id,
        evidence_context=evidence_context,  # Pass evidence to multi-agent
        stress_test_mode=stress_test_mode,  # Pass stress test flag
        normal_mode=False  # Work mode: include synthesis
    )

    # Convert to MultiAgentMessage models
    messages = [MultiAgentMessage(**msg) for msg in messages_data]

    # SELF-EXPLANATION v1: Add micro-disclosures to synthesis message if applicable
    micro_disclosures = build_micro_disclosures(
        using_evidence=bool(evidence_context and "Evidence (from web sources):" in evidence_context),
        stress_test_mode=stress_test_mode,
        using_conversation_context=False,  # TODO: Enable when conversation storage implemented
        using_profile=False  # Not yet used in multi-agent
    )

    if micro_disclosures and messages:
        # Prepend to the synthesis message (last message, typically from quillo)
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].role == "assistant" and messages[i].agent == "quillo":
                messages[i].content = micro_disclosures + messages[i].content
                break

    return MultiAgentResponse(
        messages=messages,
        provider=provider,
        trace_id=trace_id,
        fallback_reason=fallback_reason,
        peers_unavailable=peers_unavailable
    )


@router.post("/evidence", response_model=EvidenceResponse)
@limiter.limit("30/minute")
async def ui_evidence_retrieval(
    request: Request,
    payload: EvidenceRequest,
    token: str = Depends(verify_ui_token)
) -> EvidenceResponse:
    """
    Evidence Layer v1: Manual-only, sourced, non-authorial evidence retrieval.

    Retrieves live web data and extracts neutral facts with sources and timestamps.

    CRITICAL RULES (enforced):
    - Manual trigger only (no automatic invocation)
    - Non-authorial: facts only, no advice/recommendations
    - Separation from judgment: no synthesis or interpretation
    - Hard limits: max 10 facts, max 8 sources

    Rate limited to 30 requests per minute per IP.

    Args:
        request: FastAPI request (for rate limiting)
        payload: EvidenceRequest with query or use_last_message flag
        token: Validated UI token

    Returns:
        EvidenceResponse with facts, sources, timestamps, and optional limits note
    """
    logger.info(f"UI POST /evidence: query={payload.query[:50] if payload.query else 'None'}, use_last_message={payload.use_last_message}")

    # Determine query
    query = None
    if payload.query and payload.query.strip():
        query = payload.query.strip()
    elif payload.use_last_message:
        # TODO: In future, retrieve last user message from conversation storage
        # For v1, return error since we don't have conversation storage yet
        from datetime import datetime, timezone
        return EvidenceResponse(
            ok=False,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=0,
            facts=[],
            sources=[],
            error="Conversation storage not yet implemented. Please provide a query."
        )

    # Validate query
    if not query:
        from datetime import datetime, timezone
        return EvidenceResponse(
            ok=False,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=0,
            facts=[],
            sources=[],
            error="No query provided. Please specify a query or use_last_message."
        )

    # Retrieve evidence
    return await retrieve_evidence(query)


# Tasks Module v1 Endpoints

@router.post("/tasks/intents", response_model=TaskIntentOut)
@limiter.limit("30/minute")
async def ui_create_task_intent(
    request: Request,
    payload: TaskIntentCreate,
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> TaskIntentOut:
    """
    Create a new task intent (v1).

    Stores a user task intent for future orchestration.
    V1 is minimal: just intent storage, no execution/workers.
    Rate limited to 30 requests per minute per IP.

    Args:
        request: FastAPI request (for rate limiting)
        payload: TaskIntentCreate with intent_text, optional origin_chat_id, user_key
        db: Database session
        token: Validated UI token

    Returns:
        TaskIntentOut with id, timestamps, status, intent_text, etc.
    """
    logger.info(
        f"UI POST /tasks/intents: user_key={payload.user_key}, "
        f"origin_chat_id={payload.origin_chat_id}, "
        f"text_len={len(payload.intent_text)}"
    )

    # Create task intent
    try:
        task_intent = TaskIntentService.create_intent(
            db=db,
            intent_text=payload.intent_text,
            origin_chat_id=payload.origin_chat_id,
            user_key=payload.user_key,
            scope_will_do=payload.scope_will_do,
            scope_wont_do=payload.scope_wont_do,
            scope_done_when=payload.scope_done_when
        )
    except ValueError as e:
        logger.warning(f"Invalid task intent creation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    return TaskIntentOut(
        id=task_intent.id,
        created_at=task_intent.created_at.isoformat(),
        updated_at=task_intent.updated_at.isoformat(),
        status=task_intent.status.value,
        intent_text=task_intent.intent_text,
        origin_chat_id=task_intent.origin_chat_id,
        user_key=task_intent.user_key,
        scope_will_do=task_intent.scope_will_do,
        scope_wont_do=task_intent.scope_wont_do,
        scope_done_when=task_intent.scope_done_when,
        approval_mode=task_intent.approval_mode
    )


@router.get("/tasks/intents", response_model=List[TaskIntentOut])
async def ui_list_task_intents(
    user_key: Optional[str] = Query(None, description="Optional user identifier to filter by"),
    limit: int = Query(20, ge=1, le=100, description="Max results (1-100, default 20)"),
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> List[TaskIntentOut]:
    """
    List task intents (v1).

    Returns task intents ordered by most recent first.
    If user_key provided, filter by user.
    Otherwise, return recent intents globally (for dev convenience).

    Args:
        user_key: Optional user identifier to filter by
        limit: Max results (1-100, default 20)
        db: Database session
        token: Validated UI token

    Returns:
        List of TaskIntentOut instances
    """
    logger.info(f"UI GET /tasks/intents: user_key={user_key}, limit={limit}")

    # List task intents
    task_intents = TaskIntentService.list_intents(
        db=db,
        user_key=user_key,
        limit=limit
    )

    return [
        TaskIntentOut(
            id=task_intent.id,
            created_at=task_intent.created_at.isoformat(),
            updated_at=task_intent.updated_at.isoformat(),
            status=task_intent.status.value,
            intent_text=task_intent.intent_text,
            origin_chat_id=task_intent.origin_chat_id,
            user_key=task_intent.user_key,
            scope_will_do=task_intent.scope_will_do,
            scope_wont_do=task_intent.scope_wont_do,
            scope_done_when=task_intent.scope_done_when,
            approval_mode=task_intent.approval_mode
        )
        for task_intent in task_intents
    ]


# Task Plan endpoints (v2 Phase 1)

@router.post("/tasks/{task_id}/plan", response_model=TaskPlanOut)
async def ui_create_task_plan(
    task_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> TaskPlanOut:
    """
    Create (or replace) a plan for a task intent.

    - Generates a deterministic plan based on task keywords
    - Returns the created plan
    - Idempotent: calling multiple times replaces the existing plan
    """
    logger.info(f"UI POST /tasks/{task_id}/plan")

    try:
        plan = TaskPlanService.create_plan(db, task_id)
    except ValueError as e:
        logger.warning(f"Invalid task plan creation: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    return TaskPlanOut(
        id=plan.id,
        task_intent_id=plan.task_intent_id,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        plan_steps=plan.plan_steps,
        summary=plan.summary,
        status=plan.status.value,
        approved_at=plan.approved_at.isoformat() if plan.approved_at else None
    )


@router.get("/tasks/{task_id}/plan", response_model=TaskPlanOut)
async def ui_get_task_plan(
    task_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> TaskPlanOut:
    """
    Get the plan for a task intent.

    Returns 404 if no plan exists for this task.
    """
    logger.info(f"UI GET /tasks/{task_id}/plan")

    plan = TaskPlanService.get_plan(db, task_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan found for task {task_id}")

    return TaskPlanOut(
        id=plan.id,
        task_intent_id=plan.task_intent_id,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        plan_steps=plan.plan_steps,
        summary=plan.summary,
        status=plan.status.value,
        approved_at=plan.approved_at.isoformat() if plan.approved_at else None
    )


@router.post("/tasks/{task_id}/plan/approve", response_model=TaskPlanOut)
async def ui_approve_task_plan(
    task_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> TaskPlanOut:
    """
    Approve a plan for a task intent.

    Sets status=approved and approved_at=now.
    Idempotent: if already approved, returns unchanged.

    Returns 404 if no task or no plan exists.
    """
    logger.info(f"UI POST /tasks/{task_id}/plan/approve")

    try:
        plan = TaskPlanService.approve_plan(db, task_id)
    except ValueError as e:
        logger.warning(f"Invalid plan approval: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    return TaskPlanOut(
        id=plan.id,
        task_intent_id=plan.task_intent_id,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        plan_steps=plan.plan_steps,
        summary=plan.summary,
        status=plan.status.value,
        approved_at=plan.approved_at.isoformat() if plan.approved_at else None
    )


@router.get("/prefs", response_model=UserPrefsOut)
async def ui_get_user_prefs(
    user_key: str = Query("global", description="User identifier (default: global)"),
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> UserPrefsOut:
    """
    Get user preferences (v1).

    Returns user preferences including task approval mode.
    Creates default preferences if none exist for the user.

    Args:
        user_key: User identifier (defaults to "global")
        db: Database session
        token: Validated UI token

    Returns:
        UserPrefsOut with user preferences
    """
    logger.info(f"UI GET /prefs: user_key={user_key}")

    # Get or create user preferences
    prefs = UserPrefsService.get_prefs(db, user_key)

    return UserPrefsOut(
        user_key=prefs.user_key,
        approval_mode=prefs.approval_mode,
        created_at=prefs.created_at.isoformat(),
        updated_at=prefs.updated_at.isoformat()
    )


@router.post("/prefs", response_model=UserPrefsOut)
async def ui_update_user_prefs(
    payload: UserPrefsUpdate,
    user_key: str = Query("global", description="User identifier (default: global)"),
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> UserPrefsOut:
    """
    Update user preferences (v1).

    Updates user's task approval mode preference.
    Creates preferences if none exist for the user.

    Args:
        payload: UserPrefsUpdate with approval_mode
        user_key: User identifier (defaults to "global")
        db: Database session
        token: Validated UI token

    Returns:
        UserPrefsOut with updated preferences
    """
    logger.info(f"UI POST /prefs: user_key={user_key}, approval_mode={payload.approval_mode}")

    # Update user preferences
    try:
        prefs = UserPrefsService.update_approval_mode(
            db=db,
            user_key=user_key,
            approval_mode=payload.approval_mode
        )
    except ValueError as e:
        logger.warning(f"Invalid approval mode: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))

    return UserPrefsOut(
        user_key=prefs.user_key,
        approval_mode=prefs.approval_mode,
        created_at=prefs.created_at.isoformat(),
        updated_at=prefs.updated_at.isoformat()
    )


# Judgment Profile v1 endpoints

@router.get("/profile/judgment", response_model=JudgmentProfileResponse)
async def ui_get_judgment_profile(
    user_key: str = Query("global", description="User identifier (default: global)"),
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> JudgmentProfileResponse:
    """
    Get judgment profile for a user (v1).

    Returns explicit, user-confirmed judgment preferences.
    NO automatic inference - all fields must be explicitly set by user.

    TODO: Replace user_key query param with session-derived identity when
    cookie-session infrastructure is implemented.

    Args:
        user_key: User identifier (defaults to "global")
        db: Database session
        token: Validated UI token

    Returns:
        JudgmentProfileResponse with profile data or null if no profile exists
    """
    logger.info(f"UI GET /profile/judgment: user_key={user_key}")

    profile_data = get_judgment_profile(db, user_key)

    if profile_data is None:
        return JudgmentProfileResponse(
            version="judgment_profile_v1",
            profile=None,
            updated_at=None
        )

    return JudgmentProfileResponse(
        version=profile_data["version"],
        profile=profile_data["profile"],
        updated_at=profile_data["updated_at"]
    )


@router.post("/profile/judgment", response_model=JudgmentProfileResponse)
@limiter.limit("30/minute")
async def ui_upsert_judgment_profile(
    request: Request,
    payload: JudgmentProfileCreateUpdate,
    user_key: str = Query("global", description="User identifier (default: global)"),
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> JudgmentProfileResponse:
    """
    Create or update judgment profile for a user (v1).

    Validates profile against strict v1 schema:
    - Only allowed keys (rejects unknown keys)
    - Each field must have source="explicit" and confirmed_at
    - Enum fields must have valid values
    - Max payload size: 20KB

    Rate limited to 30 requests per minute per IP.

    TODO: Replace user_key query param with session-derived identity when
    cookie-session infrastructure is implemented.

    TODO: Add CSRF protection when CSRF infrastructure is implemented.

    Args:
        request: FastAPI request (for rate limiting)
        payload: JudgmentProfileCreateUpdate with profile data
        user_key: User identifier (defaults to "global")
        db: Database session
        token: Validated UI token

    Returns:
        JudgmentProfileResponse with saved profile data

    Raises:
        HTTPException 400: If validation fails
    """
    logger.info(f"UI POST /profile/judgment: user_key={user_key}")

    try:
        profile_data = upsert_judgment_profile(
            db=db,
            user_key=user_key,
            profile=payload.profile
        )
    except JudgmentProfileValidationError as e:
        logger.warning(f"Judgment profile validation failed for user_key={user_key}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    return JudgmentProfileResponse(
        version=profile_data["version"],
        profile=profile_data["profile"],
        updated_at=profile_data["updated_at"]
    )


@router.delete("/profile/judgment", response_model=JudgmentProfileDeleteResponse)
@limiter.limit("30/minute")
async def ui_delete_judgment_profile(
    request: Request,
    user_key: str = Query("global", description="User identifier (default: global)"),
    db: Session = Depends(get_db),
    token: str = Depends(verify_ui_token)
) -> JudgmentProfileDeleteResponse:
    """
    Delete judgment profile for a user (v1).

    Permanently removes user's judgment profile.
    Rate limited to 30 requests per minute per IP.

    TODO: Replace user_key query param with session-derived identity when
    cookie-session infrastructure is implemented.

    TODO: Add CSRF protection when CSRF infrastructure is implemented.

    Args:
        request: FastAPI request (for rate limiting)
        user_key: User identifier (defaults to "global")
        db: Database session
        token: Validated UI token

    Returns:
        JudgmentProfileDeleteResponse with deletion status
    """
    logger.info(f"UI DELETE /profile/judgment: user_key={user_key}")

    deleted = delete_judgment_profile(db, user_key)

    return JudgmentProfileDeleteResponse(deleted=deleted)
