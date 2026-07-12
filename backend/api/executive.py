"""Executive Intelligence API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from executive.approval_engine import ApprovalEngine
from executive.capability_orchestrator import CapabilityOrchestrator
from executive.confidence_engine import ConfidenceEngine
from executive.cost_engine import CostEngine
from executive.decision_engine import DecisionEngine
from executive.exceptions import ExecutiveError
from executive.execution_planner import ExecutionPlanner
from executive.executive_brain import ExecutiveBrain
from executive.goal_manager import GoalManager
from executive.model_selector import ModelSelector
from executive.parallel_planner import ParallelPlanner
from executive.provider_selector import ProviderSelector
from executive.risk_engine import RiskEngine
from executive.schemas import GoalPriority
from executive.strategic_planner import StrategicPlanner
from executive.workflow_optimizer import WorkflowOptimizer

router = APIRouter(prefix="/executive", tags=["executive"])

_brain: ExecutiveBrain | None = None


def get_brain() -> ExecutiveBrain:
    """Get or create the global ExecutiveBrain instance."""
    global _brain
    if _brain is None:
        _brain = ExecutiveBrain(
            goal_manager=GoalManager(),
            strategic_planner=StrategicPlanner(),
            decision_engine=DecisionEngine(),
            execution_planner=ExecutionPlanner(),
            risk_engine=RiskEngine(),
            cost_engine=CostEngine(),
            confidence_engine=ConfidenceEngine(),
            capability_orchestrator=CapabilityOrchestrator(),
            provider_selector=ProviderSelector(),
            model_selector=ModelSelector(),
            workflow_optimizer=WorkflowOptimizer(),
            parallel_planner=ParallelPlanner(),
            approval_engine=ApprovalEngine(),
        )
    return _brain


@router.get("/status")
async def executive_status() -> dict[str, Any]:
    """Get executive brain status."""
    brain = get_brain()
    return {"success": True, "status": brain.get_status()}


@router.get("/goals")
async def list_goals() -> dict[str, Any]:
    """List all goals."""
    brain = get_brain()
    goals = brain._goal_manager.list_goals()
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
    goal = brain._goal_manager.create_goal(title, description, priority)
    return {"success": True, "goal": goal.to_dict()}


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str) -> dict[str, Any]:
    """Get a specific goal by ID."""
    brain = get_brain()
    goal = brain._goal_manager.get_goal(goal_id)
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
