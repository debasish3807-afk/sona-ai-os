"""Isolated execution context for agents."""

from __future__ import annotations

import copy
import time
import uuid
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AgentContext:
    """Provides an isolated execution context for an agent task."""

    def __init__(self, agent_id: str, task_id: str = "") -> None:
        self.agent_id = agent_id
        self.task_id = task_id
        self.context_id: str = str(uuid.uuid4())
        self.variables: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.created_at: float = time.time()

    def set(self, key: str, val: Any) -> None:
        """Set a context variable."""
        self.variables[key] = val
        self.history.append({"action": "set", "key": key, "timestamp": time.time()})

    def get(self, key: str, default: Any = None) -> Any:
        """Get a context variable."""
        return self.variables.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        """Create a snapshot of the current context."""
        return {
            "context_id": self.context_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "variables": copy.deepcopy(self.variables),
            "history": list(self.history),
            "created_at": self.created_at,
        }

    def restore(self, snapshot_data: dict[str, Any]) -> None:
        """Restore context from a snapshot."""
        self.variables = snapshot_data.get("variables", {})
        self.history = snapshot_data.get("history", [])
        logger.debug("context_restored", context_id=self.context_id)

    def isolate(self) -> AgentContext:
        """Create a deep copy of this context for isolation."""
        new_ctx = AgentContext(agent_id=self.agent_id, task_id=self.task_id)
        new_ctx.variables = copy.deepcopy(self.variables)
        new_ctx.history = list(self.history)
        return new_ctx
