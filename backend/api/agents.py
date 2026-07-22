"""Multi-Agent Framework API — agent management, task submission, and monitoring."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])

_orchestrator = None


async def _get_orch():
    global _orchestrator
    if _orchestrator is None:
        from agents.orchestrator import AgentOrchestrator

        _orchestrator = AgentOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator


class TaskSubmitRequest(BaseModel):
    agent_type: str = Field(..., description="Type of agent to handle this task")
    description: str = Field(..., min_length=1, max_length=2000)
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=50, ge=0, le=100)


class MessageRequest(BaseModel):
    sender_id: str = Field(..., description="Sending agent ID")
    recipient_id: str = Field(..., description="Receiving agent ID")
    payload: dict[str, Any] = Field(default_factory=dict)


@router.get("/")
async def list_agents():
    """List all registered agents with their status and capabilities."""
    orch = await _get_orch()
    agents = await orch.get_agents()
    return {"agents": agents, "count": len(agents)}


@router.post("/submit")
async def submit_task(body: TaskSubmitRequest):
    """Submit a task to the agent task queue."""
    orch = await _get_orch()
    task_id = await orch.submit_task(body.agent_type, body.description, body.payload, body.priority)
    return {"task_id": task_id, "status": "queued"}


@router.post("/execute-next")
async def execute_next():
    """Execute the next task from the queue."""
    orch = await _get_orch()
    result = await orch.execute_next()
    if result is None:
        return {"status": "no_tasks"}
    return result


@router.get("/tasks")
async def list_tasks(status: str | None = Query(None), agent_type: str | None = Query(None)):
    """List tasks with optional filters."""
    orch = await _get_orch()
    from agents.task_queue import TaskStatus

    status_filter = TaskStatus(status) if status else None
    tasks = orch.task_queue.list_tasks(status=status_filter, agent_type=agent_type)
    return {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)}


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a specific task's details."""
    orch = await _get_orch()
    task = orch.task_queue.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/messages")
async def send_message(body: MessageRequest):
    """Send a message between agents."""
    orch = await _get_orch()
    msg_id = await orch.send_message(body.sender_id, body.recipient_id, body.payload)
    return {"message_id": msg_id}


@router.get("/stats")
async def agent_stats():
    """Get agent system statistics."""
    orch = await _get_orch()
    return await orch.get_stats()


@router.post("/create")
async def create_agent(name: str, agent_type: str):
    """Create a new agent of the specified type."""
    orch = await _get_orch()
    agent = await orch.create_agent(name, agent_type)
    return {"agent_id": agent.agent_id, "name": agent.name, "type": agent_type, "status": "created"}
