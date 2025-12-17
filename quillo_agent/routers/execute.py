"""
Plan execution endpoint
"""
import uuid
from fastapi import APIRouter, Depends
from loguru import logger
from ..schemas import ExecuteRequest, ExecuteResponse, ExecutionArtifact
from ..services.execution import execution_service
from ..auth import verify_api_key

router = APIRouter(prefix="/execute", tags=["execution"])


@router.post("", response_model=ExecuteResponse)
async def execute_plan(
    request: ExecuteRequest,
    api_key: str = Depends(verify_api_key)
) -> ExecuteResponse:
    """
    Execute a plan by running each step with LLM-based tool simulation.

    This is a safe execution that simulates tools using LLM calls.
    No external actions (emails, APIs) are performed.

    Args:
        request: ExecuteRequest with intent, slots, plan_steps, etc.
        api_key: Validated API key (from auth dependency)

    Returns:
        ExecuteResponse with output_text, artifacts, trace_id, provider, warnings
    """
    logger.info(f"POST /execute: intent={request.intent}, user_id={request.user_id}, dry_run={request.dry_run}")

    # Generate trace ID
    trace_id = str(uuid.uuid4())

    # Execute the plan
    output_text, artifacts, provider_used, warnings = await execution_service.execute_plan(
        text=request.text,
        intent=request.intent,
        slots=request.slots,
        plan_steps=request.plan_steps,
        user_id=request.user_id,
        dry_run=request.dry_run
    )

    return ExecuteResponse(
        output_text=output_text,
        artifacts=artifacts,
        trace_id=trace_id,
        provider_used=provider_used,
        warnings=warnings
    )
