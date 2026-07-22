"""API v1 Router — versioned endpoint assembly with DI container integration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from api.v1.schemas import (
    GoalCreateRequest,
    GoalResponse,
    HealthResponse,
    MemorySearchRequest,
    MemoryStoreRequest,
    MetricsResponse,
    PipelineRequest,
    PipelineResponse,
    SuccessResponse,
    WorkflowCreateRequest,
    WorkflowResponse,
)
from config.logging import get_logger
from core.container import get_container
from core.observability import UnifiedHealthMonitor, UnifiedMetrics
from core.pipeline import Pipeline
from core.pipeline import PipelineRequest as PipelineReq

logger = get_logger(__name__)

# NOTE: No prefix here — the main router in app/main.py mounts at settings.api_prefix ("/api/v1")
router = APIRouter(tags=["v1"])

# Observability singletons
_health_monitor = UnifiedHealthMonitor()
_metrics = UnifiedMetrics()


def _get_pipeline() -> Pipeline:
    """Get or create the pipeline instance."""
    container = get_container()
    if not container.has("pipeline"):
        container.register_instance("pipeline", Pipeline(container))
    pipeline: Pipeline = container.resolve("pipeline")
    return pipeline


# ─── Pipeline Endpoints ─────────────────────────────────────────────────────


@router.post("/pipeline/execute", response_model=PipelineResponse)
async def execute_pipeline(body: PipelineRequest, request: Request) -> PipelineResponse:
    """Execute the end-to-end AI pipeline."""
    container = get_container()
    if not container.initialized:
        await container.initialize()

    pipeline = _get_pipeline()
    user_id = getattr(request.state, "user_id", "")
    correlation_id = getattr(request.state, "correlation_id", "")

    req = PipelineReq(
        user_input=body.user_input,
        user_id=user_id,
        session_id=body.session_id,
        correlation_id=correlation_id,
        metadata=body.metadata,
    )

    result = await pipeline.execute(req)
    _metrics.increment("pipeline_executions")
    _metrics.record_histogram("pipeline_duration_ms", result.duration_ms)

    return PipelineResponse(
        success=result.status.value == "completed",
        request_id=result.request_id,
        status=result.status.value,
        output=result.output,
        stages_completed=result.stages_completed,
        duration_ms=result.duration_ms,
        error=result.error,
    )


@router.get("/pipeline/{request_id}", response_model=PipelineResponse)
async def get_pipeline_result(request_id: str) -> PipelineResponse:
    """Get a pipeline execution result."""
    pipeline = _get_pipeline()
    result = pipeline.get_execution(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Pipeline execution not found")
    return PipelineResponse(
        success=result.status.value == "completed",
        request_id=result.request_id,
        status=result.status.value,
        output=result.output,
        stages_completed=result.stages_completed,
        duration_ms=result.duration_ms,
        error=result.error,
    )


# ─── Workflow Endpoints ──────────────────────────────────────────────────────


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow_v1(body: WorkflowCreateRequest) -> WorkflowResponse:
    """Create a workflow via the runtime engine."""
    container = get_container()
    if not container.initialized:
        await container.initialize()

    engine = container.resolve("runtime_engine")
    from runtime.schemas import Workflow, WorkflowTask, WorkflowType

    try:
        wtype = WorkflowType(body.workflow_type)
    except ValueError:
        wtype = WorkflowType.SEQUENTIAL

    tasks = [
        WorkflowTask(
            name=td.get("name", "task"),
            capability_id=td.get("capability_id", "general"),
            params=td.get("params", {}),
            dependencies=td.get("dependencies", []),
        )
        for td in body.tasks
    ]
    workflow = Workflow(name=body.name, workflow_type=wtype, tasks=tasks)
    workflow_id = await engine.submit_workflow(workflow)
    _metrics.increment("workflows_created")
    return WorkflowResponse(workflow_id=workflow_id, status="submitted")


@router.get("/workflows/{workflow_id}", response_model=SuccessResponse)
async def get_workflow_v1(workflow_id: str) -> SuccessResponse:
    """Get workflow details."""
    container = get_container()
    if not container.initialized:
        await container.initialize()

    engine = container.resolve("runtime_engine")
    workflow = engine.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return SuccessResponse(data=workflow.to_dict())


# ─── Goal Endpoints ──────────────────────────────────────────────────────────


@router.post("/goals", response_model=GoalResponse)
async def create_goal_v1(body: GoalCreateRequest) -> GoalResponse:
    """Create a new goal."""
    container = get_container()
    if not container.initialized:
        await container.initialize()

    brain = container.resolve("executive_brain")
    from executive.schemas import GoalPriority

    try:
        priority = GoalPriority(body.priority)
    except ValueError:
        priority = GoalPriority.MEDIUM

    goal = brain._goal_manager.create_goal(
        title=body.title, description=body.description, priority=priority
    )
    _metrics.increment("goals_created")
    return GoalResponse(goal=goal.to_dict())


@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal_v1(goal_id: str) -> GoalResponse:
    """Get a goal by ID."""
    container = get_container()
    if not container.initialized:
        await container.initialize()

    brain = container.resolve("executive_brain")
    goal = brain._goal_manager.get_goal(goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return GoalResponse(goal=goal.to_dict())


# ─── Memory Endpoints ────────────────────────────────────────────────────────


@router.post("/memory", response_model=SuccessResponse)
async def store_memory(body: MemoryStoreRequest) -> SuccessResponse:
    """Store a memory entry."""
    container = get_container()
    if not container.initialized:
        await container.initialize()

    from memory.default_manager import MemoryEntry

    manager = container.resolve("memory_manager")
    entry = MemoryEntry(
        content=body.content,
        memory_type=body.memory_type,
        session_id=body.session_id,
        tags=body.tags,
    )
    memory_id = await manager.store(entry)
    return SuccessResponse(data={"memory_id": memory_id})


@router.post("/memory/search", response_model=SuccessResponse)
async def search_memory(body: MemorySearchRequest) -> SuccessResponse:
    """Search memories."""
    container = get_container()
    if not container.initialized:
        await container.initialize()

    manager = container.resolve("memory_manager")
    results = await manager.search(
        query=body.query,
        memory_type=body.memory_type,
        limit=body.limit,
    )
    return SuccessResponse(data={"results": [r.to_dict() for r in results]})


# ─── Health & Metrics (v1) ──────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
async def health_v1() -> HealthResponse:
    """Health check for the v1 API."""
    summary = _health_monitor.get_summary()
    return HealthResponse(
        healthy=summary["healthy"],
        total_components=summary["total_components"],
        healthy_components=summary["healthy_components"],
        unhealthy_components=summary["unhealthy_components"],
        components=summary["components"],
    )


@router.get("/metrics", response_model=MetricsResponse)
async def metrics_v1() -> MetricsResponse:
    """Get metrics for the v1 API."""
    return MetricsResponse(
        counters={
            "pipeline_executions": _metrics.get_counter("pipeline_executions"),
            "workflows_created": _metrics.get_counter("workflows_created"),
            "goals_created": _metrics.get_counter("goals_created"),
        },
        histograms={
            "pipeline_duration_ms": _metrics.get_histogram_stats("pipeline_duration_ms"),
        },
    )


@router.get("/version")
async def version_v1() -> dict:
    """Get application version information (v1)."""
    import platform
    import sys

    from config.settings import get_settings
    from core.constants import API_VERSION

    settings = get_settings()
    return {
        "app": {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "api_version": API_VERSION,
        },
        "runtime": {
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "architecture": platform.machine(),
        },
    }
