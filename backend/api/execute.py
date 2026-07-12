"""Execution & function calling API endpoints.

Endpoints:
    POST /execute       — Analyze intent, plan, and execute tools
    POST /function-call — Direct function call (single tool)
    GET  /plans/{id}    — Get plan details
    GET  /executions/{id} — Get execution results
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.logging import get_logger
from execution.engine import ExecutionEngine
from mcp.server import get_mcp_server
from planner.planner import TaskPlanner

logger = get_logger(__name__)

router = APIRouter(tags=["execution"])

# In-memory plan/execution store (production: use persistent store)
_plans: dict[str, dict[str, Any]] = {}
_executions: dict[str, dict[str, Any]] = {}


# --- Request/Response Schemas ---


class ExecuteRequest(BaseModel):
    """POST /execute request body."""

    message: str = Field(..., min_length=1, description="User request to analyze and execute")
    session_id: str | None = Field(default=None)
    auto_execute: bool = Field(default=True, description="Execute plan immediately")
    max_steps: int = Field(default=10, ge=1, le=50)


class ExecuteResponse(BaseModel):
    """POST /execute response body."""

    success: bool
    plan_id: str
    intent: str
    confidence: float
    plan_description: str
    steps_total: int
    steps_completed: int
    steps_failed: int
    status: str
    total_duration_ms: float
    outputs: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""


class FunctionCallRequest(BaseModel):
    """POST /function-call request body."""

    name: str = Field(..., description="Tool name to call")
    arguments: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = Field(default=None)


class FunctionCallResponse(BaseModel):
    """POST /function-call response body."""

    success: bool
    tool: str
    output: str = ""
    error: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0


class PlanResponse(BaseModel):
    """GET /plans/{id} response body."""

    success: bool = True
    plan: dict[str, Any]


class ExecutionResponse(BaseModel):
    """GET /executions/{id} response body."""

    success: bool = True
    execution: dict[str, Any]


# --- Endpoints ---


@router.post("/execute", response_model=ExecuteResponse)
async def execute_task(request: ExecuteRequest) -> ExecuteResponse:
    """Analyze user intent, create a plan, and execute tools.

    The full autonomous pipeline:
    1. Analyze intent from message
    2. Build execution plan with tool selection
    3. Execute plan steps sequentially
    4. Return aggregated results

    This is the primary endpoint for AI-driven tool execution.
    """
    planner = TaskPlanner()
    engine = ExecutionEngine()

    # Step 1: Analyze intent
    intent = planner.analyze_intent(request.message)

    # Step 2: Create plan
    plan = planner.create_plan(request.message, intent)

    # Limit steps
    if len(plan.steps) > request.max_steps:
        plan.steps = plan.steps[: request.max_steps]

    # Store plan
    _plans[plan.plan_id] = plan.to_dict()

    # Step 3: Execute if requested
    if request.auto_execute and plan.steps:
        result = await engine.execute_plan(plan, request.session_id)
        _executions[plan.plan_id] = {
            "plan_id": result.plan_id,
            "status": result.status,
            "steps_completed": result.steps_completed,
            "steps_failed": result.steps_failed,
            "total_duration_ms": result.total_duration_ms,
            "outputs": result.outputs,
            "summary": result.summary,
        }

        return ExecuteResponse(
            success=result.steps_failed == 0,
            plan_id=plan.plan_id,
            intent=intent.intent.value,
            confidence=intent.confidence,
            plan_description=plan.description,
            steps_total=result.steps_total,
            steps_completed=result.steps_completed,
            steps_failed=result.steps_failed,
            status=result.status,
            total_duration_ms=result.total_duration_ms,
            outputs=result.outputs,
            summary=result.summary,
        )

    # Plan created but not executed
    return ExecuteResponse(
        success=True,
        plan_id=plan.plan_id,
        intent=intent.intent.value,
        confidence=intent.confidence,
        plan_description=plan.description,
        steps_total=plan.step_count,
        steps_completed=0,
        steps_failed=0,
        status="created",
        total_duration_ms=0.0,
        summary="Plan created (auto_execute=false)",
    )


@router.post("/function-call", response_model=FunctionCallResponse)
async def function_call(request: FunctionCallRequest) -> FunctionCallResponse:
    """Execute a single tool by name (direct function call).

    Bypasses planning — directly invokes the named tool with
    the provided arguments. Used when the caller already knows
    which tool to use.
    """
    mcp = get_mcp_server()

    if not mcp.registry.has_tool(request.name):
        raise HTTPException(status_code=404, detail=f"Tool not found: {request.name}")

    result = await mcp.execute_tool(
        tool_name=request.name,
        params=request.arguments,
        session_id=request.session_id,
    )

    return FunctionCallResponse(
        success=result.success,
        tool=result.tool_name,
        output=result.output,
        error=result.error,
        data=result.data,
        duration_ms=result.duration_ms,
    )


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str) -> PlanResponse:
    """Get details of a previously created plan."""
    plan_data = _plans.get(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")
    return PlanResponse(plan=plan_data)


@router.get("/executions/{plan_id}", response_model=ExecutionResponse)
async def get_execution(plan_id: str) -> ExecutionResponse:
    """Get execution results for a plan."""
    exec_data = _executions.get(plan_id)
    if not exec_data:
        raise HTTPException(status_code=404, detail=f"Execution not found: {plan_id}")
    return ExecutionResponse(execution=exec_data)
