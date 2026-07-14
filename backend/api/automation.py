"""Automation API — workflow management and execution."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from automation.engine import AutomationEngine
from automation.schemas import (
    ActionStep,
    ActionType,
    StepType,
    Trigger,
    TriggerType,
    WorkflowStep,
)
from config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/automation", tags=["automation"])

_engine = AutomationEngine()


class CreateWorkflowRequest(BaseModel):
    name: str
    description: str = ""
    steps: list[dict[str, Any]] = Field(default_factory=list)
    trigger_type: str = "manual"
    trigger_config: dict[str, Any] = Field(default_factory=dict)


class RunWorkflowRequest(BaseModel):
    workflow_id: str


@router.get("/workflows")
async def list_workflows() -> dict[str, Any]:
    workflows = _engine.list_workflows()
    return {
        "workflows": [
            {"id": w.workflow_id, "name": w.name, "enabled": w.enabled} for w in workflows
        ],
        "count": len(workflows),
    }


@router.post("/workflows")
async def create_workflow(req: CreateWorkflowRequest) -> dict[str, Any]:
    steps = _parse_steps(req.steps)
    trigger = Trigger(trigger_type=TriggerType(req.trigger_type), config=req.trigger_config)
    wf = _engine.create_workflow(req.name, steps, trigger, req.description)
    return {"workflow_id": wf.workflow_id, "name": wf.name}


@router.post("/run")
async def run_workflow(req: RunWorkflowRequest) -> dict[str, Any]:
    run = await _engine.run_workflow(req.workflow_id)
    return {
        "run_id": run.run_id,
        "status": run.status.value,
        "steps_completed": run.steps_completed,
        "output": run.output,
        "error": run.error,
    }


@router.get("/history")
async def get_history(limit: int = 50) -> dict[str, Any]:
    history = _engine.get_history(limit)
    return {
        "runs": [
            {
                "run_id": r.run_id,
                "workflow_id": r.workflow_id,
                "status": r.status.value,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "error": r.error,
            }
            for r in history
        ],
        "count": len(history),
    }


@router.get("/templates")
async def get_templates() -> dict[str, Any]:
    return {"templates": _engine.get_templates()}


@router.get("/status")
async def get_status() -> dict[str, Any]:
    return _engine.get_status()


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str) -> dict[str, Any]:
    deleted = _engine.delete_workflow(workflow_id)
    return {"deleted": deleted}


def _parse_steps(raw: list[dict[str, Any]]) -> list[WorkflowStep]:
    """Convert raw step dicts to WorkflowStep objects."""
    steps: list[WorkflowStep] = []
    for s in raw:
        action_type_str = s.get("type", "notification")
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            action_type = ActionType.NOTIFICATION
        action = ActionStep(
            action_type=action_type,
            params=s.get("params", {}),
            retry=s.get("retry", 0),
            timeout_seconds=s.get("timeout", 30.0),
        )
        steps.append(WorkflowStep(step_type=StepType.ACTION, action=action))
    return steps
