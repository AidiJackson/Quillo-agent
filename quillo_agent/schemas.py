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
    mode: str = Field("normal", description="Uorin mode: 'normal' (raw chat) or 'work' (judgment + evidence + guardrails)")


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
    suggested_next_step: Optional[str] = Field(None, description="Next step suggestion (values: 'add_agents' for multi-agent suggestion, or custom text for cannot_do_yet mode)")


class MultiAgentMessage(BaseModel):
    """Single message in multi-agent conversation"""
    role: str = Field(..., description="Message role: 'assistant' or 'user'")
    agent: str = Field(..., description="Agent name: 'quillo', 'claude', 'grok'")
    content: str = Field(..., description="Message content")
    model_id: Optional[str] = Field(None, description="Model ID attempted (e.g., 'anthropic/claude-3.5-sonnet')")
    live: bool = Field(True, description="True if live response, False if unavailable placeholder")
    unavailable_reason: Optional[str] = Field(None, description="Reason bucket if live=False: 'rate_limited', 'not_found', 'timeout', 'http_error', 'exception'")


class MultiAgentRequest(BaseModel):
    """Request for multi-agent chat"""
    text: str = Field(..., description="User input text")
    user_id: Optional[str] = Field(None, description="User identifier")
    agents: Optional[List[str]] = Field(None, description="List of agents to include (default: ['primary', 'claude', 'grok'])")
    mode: str = Field("normal", description="Uorin mode: 'normal' (raw chat) or 'work' (judgment + evidence + guardrails)")


class MultiAgentResponse(BaseModel):
    """Response from multi-agent chat"""
    messages: List[MultiAgentMessage] = Field(..., description="Multi-agent conversation messages")
    provider: str = Field(..., description="Provider used: 'openrouter' or 'template'")
    trace_id: str = Field(..., description="Trace identifier for debugging")
    fallback_reason: Optional[str] = Field(None, description="Reason for fallback if provider is 'template' (e.g., 'openrouter_timeout', 'openrouter_rate_limited', 'openrouter_http_error', 'openrouter_exception', 'openrouter_key_missing')")
    peers_unavailable: bool = Field(False, description="True if Quillo succeeded but all peer agents failed")


class EvidenceFact(BaseModel):
    """Single fact extracted from evidence sources"""
    text: str = Field(..., description="Fact statement in neutral language")
    source_id: str = Field(..., description="Reference to source ID")
    published_at: Optional[str] = Field(None, description="ISO timestamp when fact was published (if available)")


class EvidenceSource(BaseModel):
    """Source of evidence with metadata"""
    id: str = Field(..., description="Unique source identifier")
    title: str = Field(..., description="Page or article title")
    domain: str = Field(..., description="Domain name (e.g., 'example.com')")
    url: str = Field(..., description="Full URL to source")
    retrieved_at: str = Field(..., description="ISO timestamp when source was retrieved")


class EvidenceRequest(BaseModel):
    """Request for evidence retrieval"""
    query: Optional[str] = Field(None, description="Specific search query (optional)")
    use_last_message: bool = Field(False, description="Use last user message as query context")


class EvidenceResponse(BaseModel):
    """Response from evidence layer (v1.1 with guards)"""
    ok: bool = Field(..., description="Whether evidence retrieval succeeded")
    retrieved_at: str = Field(..., description="ISO timestamp of retrieval")
    duration_ms: int = Field(..., description="Total duration in milliseconds")
    facts: List[EvidenceFact] = Field(default_factory=list, description="Extracted neutral facts (max 10)")
    sources: List[EvidenceSource] = Field(default_factory=list, description="Source metadata (max 8)")
    limits: Optional[str] = Field(None, description="Optional single-line limitation or missing-data note")
    error: Optional[str] = Field(None, description="Error message if ok=False")
    empty_reason: Optional[str] = Field(None, description="Reason why facts are empty: no_results, ambiguous_query, computed_stat, source_fetch_blocked, unknown")


# Tasks Module v1 Schemas

class TaskIntentCreate(BaseModel):
    """Request to create a task intent"""
    intent_text: str = Field(..., description="The task intent text (required)")
    origin_chat_id: Optional[str] = Field(None, description="Optional chat/conversation ID where this originated")
    user_key: Optional[str] = Field(None, description="Optional user identifier (session-based or client-provided)")
    # Task Scope v1 - optional in create, backend will auto-generate if missing
    scope_will_do: Optional[List[str]] = Field(None, description="What the task will do (max 5 bullets)")
    scope_wont_do: Optional[List[str]] = Field(None, description="What the task won't do (max 5 bullets)")
    scope_done_when: Optional[str] = Field(None, description="When the task is considered done")


class TaskIntentOut(BaseModel):
    """Task intent output schema"""
    id: str = Field(..., description="Task intent UUID")
    created_at: str = Field(..., description="ISO timestamp of creation")
    updated_at: str = Field(..., description="ISO timestamp of last update")
    status: str = Field(..., description="Task status: approved, completed, or cancelled")
    intent_text: str = Field(..., description="The task intent text")
    origin_chat_id: Optional[str] = Field(None, description="Optional chat/conversation ID where this originated")
    user_key: Optional[str] = Field(None, description="Optional user identifier")
    # Task Scope v1
    scope_will_do: Optional[List[str]] = Field(None, description="What the task will do")
    scope_wont_do: Optional[List[str]] = Field(None, description="What the task won't do")
    scope_done_when: Optional[str] = Field(None, description="When the task is considered done")
    # Approval mode snapshot v1
    approval_mode: str = Field(..., description="Approval mode at task creation: confirm_every_step, plan_then_auto, or auto_lowrisk_confirm_highrisk")


# Task Plan Module v2 Schemas

class TaskPlanStepOut(BaseModel):
    """Task plan step output schema"""
    step_num: int = Field(..., description="Step number (1-indexed)")
    description: str = Field(..., description="Step description")


class TaskPlanOut(BaseModel):
    """Task plan output schema"""
    id: str = Field(..., description="Plan UUID")
    task_intent_id: str = Field(..., description="FK to task intent")
    created_at: str = Field(..., description="ISO timestamp of creation")
    updated_at: str = Field(..., description="ISO timestamp of last update")
    plan_steps: List[Dict] = Field(..., description="List of plan steps")
    summary: Optional[str] = Field(None, description="Plan summary")
    status: str = Field(..., description="Plan status: draft, approved, or rejected")
    approved_at: Optional[str] = Field(None, description="ISO timestamp when plan was approved (v2 Phase 2)")


# User Preferences Module v1 Schemas

class UserPrefsUpdate(BaseModel):
    """Request to update user preferences"""
    approval_mode: str = Field(..., description="Task approval mode: confirm_every_step, plan_then_auto, or auto_lowrisk_confirm_highrisk")


class UserPrefsOut(BaseModel):
    """User preferences output schema"""
    user_key: str = Field(..., description="User identifier")
    approval_mode: str = Field(..., description="Task approval mode")
    created_at: str = Field(..., description="ISO timestamp of creation")
    updated_at: str = Field(..., description="ISO timestamp of last update")


# Judgment Profile v1 schemas

class JudgmentProfileCreateUpdate(BaseModel):
    """Request to create or update judgment profile"""
    profile: Dict[str, Any] = Field(..., description="Judgment profile data (must conform to v1 schema)")


class JudgmentProfileResponse(BaseModel):
    """Response with judgment profile data"""
    version: str = Field(..., description="Profile schema version")
    profile: Optional[Dict[str, Any]] = Field(None, description="Profile data (null if no profile exists)")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last update")


class JudgmentProfileDeleteResponse(BaseModel):
    """Response after deleting judgment profile"""
    deleted: bool = Field(..., description="True if profile was deleted")
