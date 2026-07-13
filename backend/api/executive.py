"""Executive Intelligence API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from core.container import get_container
from executive.exceptions import ExecutiveError
from executive.schemas import GoalPriority

router = APIRouter(prefix="/executive", tags=["executive"])


def get_brain() -> Any:
    """Get the ExecutiveBrain from the DI container."""
    container = get_container()
    return container.resolve("executive_brain")


@router.get("/status")
async def executive_status() -> dict[str, Any]:
    """Get executive brain status."""
    brain = get_brain()
    return {"success": True, "status": brain.get_status()}


@router.get("/goals")
async def list_goals() -> dict[str, Any]:
    """List all goals."""
    brain = get_brain()
    goals = brain.list_goals()
    return {"success": True, "goals": [g.to_dict() for g in goals], "total": len(goals)}


@router.post("/goals")
async def create_goal(body: dict[str, Any]) -> dict[str, Any]:
    """Create a new goal."""
    brain = get_brain()
    title = body.get("title", "")
    description = body.get("description", "")
    priority_str = body.get("priority", "medium")
    try:
        priority = GoalPriority(priority_str)
    except ValueError:
        priority = GoalPriority.MEDIUM
    goal = brain.create_goal(title, description, priority)
    return {"success": True, "goal": goal.to_dict()}


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str) -> dict[str, Any]:
    """Get a specific goal by ID."""
    brain = get_brain()
    goal = brain.get_goal(goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"success": True, "goal": goal.to_dict()}


@router.post("/plan")
async def plan_execution(body: dict[str, Any]) -> dict[str, Any]:
    """Plan execution for a goal description."""
    brain = get_brain()
    title = body.get("title", "Untitled Goal")
    description = body.get("description", "")
    priority_str = body.get("priority", "medium")
    constraints = body.get("constraints", {})
    try:
        priority = GoalPriority(priority_str)
    except ValueError:
        priority = GoalPriority.MEDIUM
    try:
        result = await brain.process_goal(title, description, priority, constraints)
        return {"success": True, "result": result}
    except ExecutiveError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/events")
async def recent_events(limit: int = 50) -> dict[str, Any]:
    """Get recent executive events."""
    brain = get_brain()
    events = brain.get_events()[-limit:]
    return {"success": True, "events": events, "total": len(events)}
