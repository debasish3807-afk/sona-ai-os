"""Orchestration API — task planning, agent orchestration, workflows, goals."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestration.event_bus import EventBus
from orchestration.goal_manager import GoalManager
from orchestration.orchestrator import AgentOrchestrator
from orchestration.schemas import (
    AgentSpec,
    GoalStatus,
    PlanStep,
    ToolDefinition,
)
from orchestration.task_planner import TaskPlanner
from orchestration.tool_orchestrator import ToolOrchestrator
from orchestration.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/orchestration", tags=["orchestration"])

_planner = TaskPlanner()
_orchestrator = AgentOrchestrator()
_tools = ToolOrchestrator()
_workflows = WorkflowEngine()
_goals = GoalManager()
_bus = EventBus()


class _TaskBody(BaseModel):
    task_type: str
    agent_type: str = ""
    tool: str = ""
    params: dict[str, Any] = {}
    context: dict[str, Any] = {}


class _PlanBody(BaseModel):
    goal: str
    steps: list[dict[str, Any]] = []


class _GoalBody(BaseModel):
    title: str
    description: str = ""


@router.post("/plans")
async def create_plan(body: _PlanBody):
    plan = _planner.create_plan(body.goal)
    if body.steps:
        steps = [PlanStep(**s) for s in body.steps]
        _planner.decompose(plan.plan_id, steps)
    return {"plan_id": plan.plan_id, "goal": body.goal}


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str):
    plan = _planner.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404)
    return {"plan_id": plan.plan_id, "goal": plan.goal, "status": plan.status.value}


@router.post("/agents/spawn")
async def spawn_agent(agent_type: str, count: int = 1):
    agent_id = _orchestrator.spawn(AgentSpec(agent_type=agent_type))
    return {"agent_id": agent_id, "agent_type": agent_type}


@router.get("/agents")
async def list_agents():
    return {"agents": _orchestrator.list_agents(), "count": len(_orchestrator.list_agents())}


@router.post("/tools/register")
async def register_tool(name: str, description: str = ""):
    tid = _tools.register_tool(ToolDefinition(name=name, description=description))
    return {"tool_id": tid}


@router.post("/tools/execute")
async def execute_tool(body: _TaskBody):
    result = _tools.execute_with_retry(body.tool, body.params)
    return result


@router.get("/tools/history")
async def tool_history():
    return {"history": _tools.history(), "count": len(_tools.history())}


@router.post("/workflows")
async def create_workflow(name: str):
    wf = _workflows.create_workflow(name, [])
    return {"workflow_id": wf.workflow_id}


@router.post("/goals")
async def create_goal(body: _GoalBody):
    goal = _goals.create_goal(body.title, body.description)
    return {"goal_id": goal.goal_id, "title": goal.title}


@router.get("/goals")
async def list_goals(status: str | None = None):
    s = GoalStatus(status) if status else None
    goals = _goals.list_goals(s)
    return {"goals": [{"id": g.goal_id, "title": g.title, "status": g.status.value} for g in goals]}


@router.post("/events/publish")
async def publish_event(event_type: str):
    count = await _bus.publish(event_type)
    return {"published": True, "handlers_notified": count}


@router.get("/stats")
async def orchestration_stats():
    return {
        "plans": _planner.get_stats(),
        "agents": _orchestrator.get_stats(),
        "tools": _tools.get_stats(),
        "goals": _goals.get_stats(),
        "bus": _bus.get_stats(),
    }
