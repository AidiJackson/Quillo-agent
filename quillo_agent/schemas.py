"""
Pydantic schemas for request/response validation
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RouteRequest(BaseModel):
    """Request for intent routing"""
    text: str = Field(..., description="User input text to route")
    user_id: Optional[str] = Field(None, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class RouteResponse(BaseModel):
    """Response from intent router"""
    intent: str = Field(..., description="Detected intent")
    reasons: List[str] = Field(default_factory=list, description="Classification reasoning")
    slots: Optional[Dict[str, Any]] = Field(None, description="Extracted slots")


class PlanRequest(BaseModel):
    """Request for plan generation"""
    intent: str = Field(..., description="Intent to plan for")
    user_id: Optional[str] = None
    slots: Optional[Dict[str, Any]] = None
    text: Optional[str] = Field(None, description="Original user text")


class PlanStep(BaseModel):
    """Single step in a plan"""
    tool: str = Field(..., description="Tool to execute")
    premium: Optional[bool] = Field(None, description="Requires premium tier")
    rationale: str = Field(..., description="Why this step is needed")


class PlanResponse(BaseModel):
    """Response from plan generator"""
    steps: List[PlanStep] = Field(..., description="Execution steps")
    trace_id: str = Field(..., description="Trace identifier for debugging")


class ProfileIn(BaseModel):
    """Input for profile update"""
    user_id: str
    profile_md: str = Field(..., description="Markdown profile content")


class ProfileOut(BaseModel):
    """Output for profile retrieval"""
    profile_md: str
    updated_at: str = Field(..., description="ISO timestamp of last update")


class FeedbackIn(BaseModel):
    """Input for feedback recording"""
    user_id: str
    tool: str = Field(..., description="Tool that was used")
    outcome: bool = Field(..., description="True for success, False for failure")
    signals: Optional[Dict[str, Any]] = Field(None, description="Additional signals")


class FeedbackOut(BaseModel):
    """Output for feedback confirmation"""
    ok: bool = True


class AskRequest(BaseModel):
    """Request for Quillopreneur business advice"""
    text: str = Field(..., description="Business question or topic")
    user_id: Optional[str] = Field(None, description="User identifier for personalization")


class AskResponse(BaseModel):
    """Response from Quillopreneur advisor"""
    answer: str = Field(..., description="Business advice response")
    model: str = Field(..., description="Model used for response (e.g., 'claude-3-5-sonnet' or 'offline')")
    trace_id: str = Field(..., description="Trace identifier for debugging")


class ExecuteRequest(BaseModel):
    """Request for plan execution"""
    user_id: Optional[str] = Field(None, description="User identifier")
    text: str = Field(..., description="Original user input text")
    intent: str = Field(..., description="Detected intent")
    slots: Optional[Dict[str, Any]] = Field(None, description="Extracted slots")
    plan_steps: List[PlanStep] = Field(..., description="Plan steps to execute")
    dry_run: bool = Field(True, description="If true, simulates execution safely")


class ExecutionArtifact(BaseModel):
    """Artifact from a single execution step"""
    step_index: int = Field(..., description="Index of the step (0-based)")
    tool: str = Field(..., description="Tool that was executed")
    input_excerpt: str = Field(..., description="Brief input summary")
    output_excerpt: str = Field(..., description="Brief output summary")


class ExecuteResponse(BaseModel):
    """Response from plan execution"""
    output_text: str = Field(..., description="Final execution output")
    artifacts: List[ExecutionArtifact] = Field(default_factory=list, description="Step-by-step execution trace")
    trace_id: str = Field(..., description="Trace identifier for debugging")
    provider_used: str = Field(..., description="LLM provider used (openrouter/anthropic/offline)")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during execution")


class JudgmentRequest(BaseModel):
    """Request for judgment explanation"""
    text: str = Field(..., description="User input text to analyze")
    user_id: Optional[str] = Field(None, description="User identifier")
    intent: Optional[str] = Field(None, description="Detected intent (if already known)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class JudgmentResponse(BaseModel):
    """Response from judgment layer"""
    stakes: str = Field(..., description="Stakes level: low, medium, or high")
    what_i_see: str = Field(..., description="Grounded observation of the situation")
    why_it_matters: Optional[str] = Field(None, description="Reasoning (only for medium/high stakes)")
    recommendation: str = Field(..., description="Clear action recommendation")
    requires_confirmation: bool = Field(..., description="Whether user approval is needed")
    formatted_message: str = Field(..., description="User-ready formatted explanation")
    # Interaction Contract v1 fields
    mode: Optional[str] = Field(None, description="Contract mode: answer, clarify, confirm_required, or cannot_do_yet")
    assistant_message: Optional[str] = Field(None, description="Contract-compliant conversational message")
    questions: Optional[List[str]] = Field(None, description="Clarifying questions (if mode=clarify)")
    suggested_next_step: Optional[str] = Field(None, description="Next step suggestion (if mode=cannot_do_yet)")
