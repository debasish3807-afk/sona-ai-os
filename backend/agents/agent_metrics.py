"""Agent-level metrics collection."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AgentMetrics:
    """Collects and reports agent-level performance metrics."""

    def __init__(self) -> None:
        self._records: dict[str, list[dict[str, Any]]] = {}
        self._start_time: float = time.time()

    def record_task(self, agent_id: str, duration_ms: float, success: bool) -> None:
        """Record a completed task metric."""
        record = {"duration_ms": duration_ms, "success": success, "timestamp": time.time()}
        self._records.setdefault(agent_id, []).append(record)

    def get_agent_stats(self, agent_id: str) -> dict[str, Any]:
        """Get stats for a specific agent."""
        records = self._records.get(agent_id, [])
        if not records:
            return {"agent_id": agent_id, "total": 0}
        durations = [r["duration_ms"] for r in records]
        return {
            "agent_id": agent_id,
            "total": len(records),
            "successes": sum(1 for r in records if r["success"]),
            "failures": sum(1 for r in records if not r["success"]),
            "avg_duration_ms": sum(durations) / len(durations),
        }

    def get_global_stats(self) -> dict[str, Any]:
        """Get global statistics across all agents."""
        total = sum(len(v) for v in self._records.values())
        successes = sum(1 for recs in self._records.values() for r in recs if r["success"])
        return {
            "total_agents": len(self._records),
            "total_tasks": total,
            "total_successes": successes,
            "total_failures": total - successes,
        }

    def get_throughput(self) -> float:
        """Get tasks per second throughput."""
        total = sum(len(v) for v in self._records.values())
        elapsed = time.time() - self._start_time
        if elapsed <= 0:
            return 0.0
        return total / elapsed
