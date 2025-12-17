"""
Core Quillo service: routing and planning logic
"""
import uuid
from typing import Optional, Dict, Any, List
from loguru import logger
from ..schemas import RouteResponse, PlanResponse, PlanStep
from ..utils.classifier import classify
from ..utils.explain import build_rationale
from .llm import LLMRouter
from ..config import settings, is_offline_mode


llm_router = LLMRouter()


async def route(text: str, user_id: Optional[str] = None) -> RouteResponse:
    """
    Route user input to intent using rule-based classifier + LLM fallback.

    Args:
        text: User input text
        user_id: Optional user identifier

    Returns:
        RouteResponse with intent, reasons, and slots
    """
    logger.info(f"Routing request for user={user_id}")
    if settings.app_env == "dev":
        logger.debug(f"Input preview: {text[:30]}...")

    # Try rule-based classification first
    result = classify(text)
    intent = result["intent"]
    reasons = result["reasons"]
    slots = result.get("slots")
    confidence = result["confidence"]

    # If confidence is low and we have API keys, try LLM fallback
    if confidence < 0.6 and not is_offline_mode():
        logger.debug(f"Low confidence ({confidence}); trying LLM fallback")
        llm_result = await llm_router.classify_fallback(text)
        if llm_result:
            intent = llm_result.get("intent", intent)
            reasons = llm_result.get("reasons", reasons)
            slots = llm_result.get("slots", slots)
            confidence = llm_result.get("confidence", confidence)
            reasons.append(f"LLM fallback applied (confidence: {confidence:.2f})")
    elif confidence < 0.6:
        logger.debug(f"Low confidence ({confidence}) but offline mode - using rule-based result")
        reasons.append("Offline mode: rule-based classification only")

    logger.info(f"Routed to intent: {intent} (confidence: {confidence:.2f})")
    return RouteResponse(intent=intent, reasons=reasons, slots=slots)


async def plan(
    intent: str,
    slots: Optional[Dict[str, Any]] = None,
    text: Optional[str] = None,
    user_id: Optional[str] = None
) -> PlanResponse:
    """
    Generate execution plan for given intent.

    Args:
        intent: Detected intent
        slots: Extracted slots
        text: Original user text
        user_id: Optional user identifier

    Returns:
        PlanResponse with steps and trace_id
    """
    logger.info(f"Planning for intent: {intent} (user={user_id})")

    trace_id = str(uuid.uuid4())
    steps: List[PlanStep] = []

    # Try LLM-based planning if MODEL_ROUTING=premium and not in offline mode
    if settings.model_routing == "premium" and not is_offline_mode():
        logger.debug("Attempting LLM-based plan enrichment (premium mode)")
        llm_steps = await llm_router.plan_reasoning(intent, slots, text)
        if llm_steps:
            try:
                # Convert LLM steps to PlanStep objects
                steps = [PlanStep(**step) for step in llm_steps]
                logger.info(f"Using LLM-generated plan with {len(steps)} steps (trace_id={trace_id})")
                return PlanResponse(steps=steps, trace_id=trace_id)
            except Exception as e:
                logger.warning(f"Failed to parse LLM steps, falling back to deterministic: {e}")
    elif settings.model_routing == "premium":
        logger.debug("Premium mode requested but offline - using deterministic planning")

    # Deterministic planning (fallback or default for non-premium)
    if intent == "response":
        steps.append(PlanStep(
            tool="response_generator",
            premium=False,
            rationale="Generate initial response based on user profile and context"
        ))
        steps.append(PlanStep(
            tool="tone_adjuster",
            premium=True,
            rationale="Adjust tone to match user preferences and situation urgency"
        ))
        if slots and slots.get("outcome") == "Defuse":
            steps.append(PlanStep(
                tool="conflict_resolver",
                premium=True,
                rationale="Apply de-escalation techniques to defuse conflict"
            ))

    elif intent == "rewrite":
        steps.append(PlanStep(
            tool="rewriter",
            premium=False,
            rationale="Rewrite content for clarity and professionalism"
        ))
        steps.append(PlanStep(
            tool="style_enhancer",
            premium=True,
            rationale="Enhance with premium stylistic improvements"
        ))

    elif intent == "argue":
        steps.append(PlanStep(
            tool="argument_builder",
            premium=True,
            rationale="Construct persuasive arguments with supporting evidence"
        ))
        steps.append(PlanStep(
            tool="counter_analyzer",
            premium=True,
            rationale="Anticipate and address counter-arguments"
        ))

    elif intent == "clarity":
        steps.append(PlanStep(
            tool="clarity_simplifier",
            premium=False,
            rationale="Break down complex concepts into clear explanations"
        ))
        steps.append(PlanStep(
            tool="example_generator",
            premium=False,
            rationale="Provide concrete examples to illustrate points"
        ))

    else:
        # Default fallback
        steps.append(PlanStep(
            tool="general_assistant",
            premium=False,
            rationale=f"Handle generic intent: {intent}"
        ))

    logger.info(f"Generated plan with {len(steps)} steps (trace_id={trace_id})")
    return PlanResponse(steps=steps, trace_id=trace_id)
