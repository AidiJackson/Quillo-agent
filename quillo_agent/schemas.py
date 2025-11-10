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
