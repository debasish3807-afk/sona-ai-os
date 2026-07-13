"""Recovery from agent failures."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agents.schemas import AgentState, AgentTask, AgentType
from config.logging import get_logger

logger = get_logger(__name__)


class AgentRecovery:
    """Handles recovery from agent failures."""

    def __init__(self) -> None:
        self._strategies: dict[AgentType, Callable[..., Any]] = {}
        self._recovery_log: list[dict[str, Any]] = []

    async def recover(self, agent_id: str, error: str) -> bool:
        """Attempt to recover an agent from a failure."""
        self._recovery_log.append({"agent_id": agent_id, "error": error, "action": "recover"})
        logger.info("agent_recovery_attempted", agent_id=agent_id, error=error)
        return True

    async def recover_task(self, task: AgentTask) -> AgentTask | None:
        """Attempt to recover a failed task."""
        if task.state != AgentState.FAILED:
            return None
        task.state = AgentState.CREATED
        task.result = {}
        self._recovery_log.append({"task_id": task.task_id, "action": "recover_task"})
        logger.info("task_recovery", task_id=task.task_id)
        return task

    def add_recovery_strategy(self, agent_type: AgentType, strategy: Callable[..., Any]) -> None:
        """Register a recovery strategy for an agent type."""
        self._strategies[agent_type] = strategy
