"""Task scheduling across agents."""

from __future__ import annotations

from typing import Any

from agents.schemas import Agent, AgentTask
from config.logging import get_logger

logger = get_logger(__name__)


class AgentScheduler:
    """Schedules tasks across available agents."""

    def __init__(self) -> None:
        self._assignments: dict[str, str] = {}  # task_id -> agent_id
        self._queue: list[AgentTask] = []

    def schedule(self, task: AgentTask, agents: list[Agent]) -> str:
        """Schedule a task to the best available agent. Returns assigned agent_id."""
        if not agents:
            logger.warning("no_agents_available", task_id=task.task_id)
            return ""
        # Simple strategy: assign to first available agent
        assigned = agents[0]
        self._assignments[task.task_id] = assigned.agent_id
        task.agent_id = assigned.agent_id
        logger.debug(
            "task_scheduled",
            task_id=task.task_id,
            agent_id=assigned.agent_id,
        )
        return assigned.agent_id

    def reschedule(self, task_id: str, new_agent_id: str) -> bool:
        """Reschedule a task to a different agent."""
        if task_id not in self._assignments:
            return False
        self._assignments[task_id] = new_agent_id
        logger.info("task_rescheduled", task_id=task_id, new_agent_id=new_agent_id)
        return True

    def get_queue(self) -> list[dict[str, Any]]:
        """Get the current assignment queue."""
        return [{"task_id": k, "agent_id": v} for k, v in self._assignments.items()]
