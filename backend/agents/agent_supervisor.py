"""Agent supervisor — monitors and recovers agents."""

from __future__ import annotations

import time
from typing import Any

from agents.schemas import AgentState, AgentTask
from config.logging import get_logger

logger = get_logger(__name__)


class AgentSupervisor:
    """Monitors agent health and handles recovery."""

    def __init__(self) -> None:
        self._supervised: dict[str, dict[str, Any]] = {}

    async def supervise(self, agent_id: str, task: AgentTask) -> AgentTask:
        """Supervise an agent executing a task."""
        self._supervised[agent_id] = {"started_at": time.time(), "task_id": task.task_id}
        logger.debug("supervising_agent", agent_id=agent_id, task_id=task.task_id)
        # Mark task as running under supervision
        task.state = AgentState.RUNNING
        return task

    def check_health(self, agent_id: str) -> bool:
        """Check if a supervised agent is healthy."""
        info = self._supervised.get(agent_id)
        if info is None:
            return False
        elapsed = time.time() - float(info["started_at"])
        # Consider unhealthy if running longer than 600 seconds
        return bool(elapsed < 600.0)

    def restart_agent(self, agent_id: str) -> bool:
        """Restart a failed agent's supervision entry."""
        if agent_id in self._supervised:
            self._supervised[agent_id]["started_at"] = time.time()
            logger.info("agent_restarted", agent_id=agent_id)
            return True
        return False

    def get_supervised(self) -> list[str]:
        """Get list of supervised agent IDs."""
        return list(self._supervised.keys())
