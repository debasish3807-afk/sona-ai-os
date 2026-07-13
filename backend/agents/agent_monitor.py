"""Real-time agent monitoring."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AgentMonitor:
    """Monitors agent execution in real-time."""

    def __init__(self) -> None:
        self._active: dict[str, dict[str, Any]] = {}
        self._stats: dict[str, list[dict[str, Any]]] = {}

    def record_start(self, agent_id: str, task_id: str) -> None:
        """Record that an agent started a task."""
        self._active[agent_id] = {"task_id": task_id, "started_at": time.time()}
        logger.debug("monitor_task_start", agent_id=agent_id, task_id=task_id)

    def record_complete(self, agent_id: str, task_id: str, duration_ms: float) -> None:
        """Record a completed task."""
        self._active.pop(agent_id, None)
        record = {"task_id": task_id, "duration_ms": duration_ms, "success": True}
        self._stats.setdefault(agent_id, []).append(record)

    def record_failure(self, agent_id: str, task_id: str, error: str) -> None:
        """Record a failed task."""
        self._active.pop(agent_id, None)
        record = {"task_id": task_id, "error": error, "success": False}
        self._stats.setdefault(agent_id, []).append(record)

    def get_stats(self, agent_id: str | None = None) -> dict[str, Any]:
        """Get statistics, optionally for a specific agent."""
        if agent_id:
            records = self._stats.get(agent_id, [])
            return {
                "agent_id": agent_id,
                "total_tasks": len(records),
                "successes": sum(1 for r in records if r.get("success")),
                "failures": sum(1 for r in records if not r.get("success")),
            }
        total = sum(len(v) for v in self._stats.values())
        return {"total_agents": len(self._stats), "total_tasks": total}

    def get_active(self) -> list[str]:
        """Get list of active agent IDs."""
        return list(self._active.keys())
