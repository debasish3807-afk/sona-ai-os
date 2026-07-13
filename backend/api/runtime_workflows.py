"""Runtime workflow API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from config.logging import get_logger
from core.container import get_container
from runtime.schemas import Workflow, WorkflowTask, WorkflowType

logger = get_logger(__name__)

router = APIRouter(prefix="/runtime/workflows", tags=["workflows"])


def _get_engine() -> Any:
    """Get RuntimeEngine from DI container."""
    return get_container().resolve("runtime_engine")


@router.post("/", response_model=None)
async def create_workflow(body: dict[str, Any]) -> dict[str, Any]:
    """Create and submit a new workflow."""
    engine = _get_engine()
    name = body.get("name", "unnamed-workflow")
    workflow_type_str = body.get("workflow_type", "sequential")
    tasks_data = body.get("tasks", [])

    try:
        workflow_type = WorkflowType(workflow_type_str)
    except ValueError:
        workflow_type = WorkflowType.SEQUENTIAL

    tasks: list[WorkflowTask] = []
    for td in tasks_data:
        task = WorkflowTask(
            name=td.get("name", "task"),
            capability_id=td.get("capability_id", "unknown"),
            params=td.get("params", {}),
            dependencies=td.get("dependencies", []),
        )
        tasks.append(task)

    workflow = Workflow(name=name, workflow_type=workflow_type, tasks=tasks)
    workflow_id = await engine.submit_workflow(workflow)
    return {"workflow_id": workflow_id, "status": "submitted"}


@router.get("/", response_model=None)
async def list_workflows() -> dict[str, Any]:
    """List all workflows."""
    engine = _get_engine()
    workflows = engine.list_workflows()
    return {
        "workflows": [w.to_dict() for w in workflows],
        "total": len(workflows),
    }


@router.get("/{workflow_id}", response_model=None)
async def get_workflow(workflow_id: str) -> dict[str, Any]:
    """Get workflow details by ID."""
    engine = _get_engine()
    workflow = engine.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return dict(workflow.to_dict())


@router.get("/{workflow_id}/status", response_model=None)
async def get_workflow_status(workflow_id: str) -> dict[str, Any]:
    """Get workflow execution status."""
    engine = _get_engine()
    workflow = engine.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "workflow_id": workflow.workflow_id,
        "state": workflow.state.value,
        "total_duration_ms": workflow.total_duration_ms,
        "tasks_total": len(workflow.tasks),
    }


@router.post("/{workflow_id}/pause", response_model=None)
async def pause_workflow(workflow_id: str) -> dict[str, Any]:
    """Pause a running workflow."""
    engine = _get_engine()
    success = await engine.pause(workflow_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause workflow")
    return {"workflow_id": workflow_id, "status": "paused"}


@router.post("/{workflow_id}/resume", response_model=None)
async def resume_workflow(workflow_id: str) -> dict[str, Any]:
    """Resume a paused workflow."""
    engine = _get_engine()
    success = await engine.resume(workflow_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume workflow")
    return {"workflow_id": workflow_id, "status": "resumed"}


@router.post("/{workflow_id}/cancel", response_model=None)
async def cancel_workflow(workflow_id: str) -> dict[str, Any]:
    """Cancel a workflow."""
    engine = _get_engine()
    success = await engine.cancel(workflow_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel workflow")
    return {"workflow_id": workflow_id, "status": "cancelled"}
