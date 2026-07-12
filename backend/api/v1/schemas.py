"""API v1 shared Pydantic schemas — request/response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = False
    error: str
    detail: str = ""
    correlation_id: str = ""


class SuccessResponse(BaseModel):
    """Standard success response model."""

    success: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = ""


class PipelineRequest(BaseModel):
    """Request model for the E2E pipeline."""

    user_input: str = Field(..., min_length=1, max_length=10000)
    session_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineResponse(BaseModel):
    """Response model for the E2E pipeline."""

    success: bool = True
    request_id: str = ""
    status: str = ""
    output: dict[str, Any] = Field(default_factory=dict)
    stages_completed: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    error: str = ""


class HealthResponse(BaseModel):
    """Unified health check response."""

    healthy: bool
    total_components: int = 0
    healthy_components: int = 0
    unhealthy_components: int = 0
    components: dict[str, bool] = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    """Unified metrics response."""

    counters: dict[str, int] = Field(default_factory=dict)
    gauges: dict[str, float] = Field(default_factory=dict)
    histograms: dict[str, dict[str, float]] = Field(default_factory=dict)


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a workflow."""

    name: str = "unnamed-workflow"
    workflow_type: str = "sequential"
    tasks: list[dict[str, Any]] = Field(default_factory=list)


class WorkflowResponse(BaseModel):
    """Response model for workflow operations."""

    success: bool = True
    workflow_id: str = ""
    status: str = ""


class GoalCreateRequest(BaseModel):
    """Request model for creating a goal."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    priority: str = "medium"
    constraints: dict[str, Any] = Field(default_factory=dict)


class GoalResponse(BaseModel):
    """Response model for goal operations."""

    success: bool = True
    goal: dict[str, Any] = Field(default_factory=dict)


class MemoryStoreRequest(BaseModel):
    """Request model for storing a memory."""

    content: str = Field(..., min_length=1)
    memory_type: str = "conversation"
    scope: str = "session"
    session_id: str = ""
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)


class MemorySearchRequest(BaseModel):
    """Request model for searching memories."""

    query: str = Field(..., min_length=1)
    memory_type: str | None = None
    scope: str | None = None
    limit: int = Field(default=10, ge=1, le=100)
