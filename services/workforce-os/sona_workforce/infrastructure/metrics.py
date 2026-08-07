"""Workforce Metrics - tracking agent performance and system statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentMetrics:
    """Metrics for a single agent."""

    agent_id: str
    tasks_total: int = 0
    tasks_success: int = 0
    tasks_failed: int = 0
    execution_duration_ms_total: float = 0.0
    tokens_used_total: int = 0


@dataclass
class WorkforceMetrics:
    """Aggregate metrics for the entire workforce.

    Tracks: agent_tasks_total, agent_execution_duration_ms, agent_failures_total,
    agent_queue_depth, agent_active_count, and per_agent_stats.
    """

    agent_tasks_total: int = 0
    agent_execution_duration_ms: float = 0.0
    agent_failures_total: int = 0
    agent_queue_depth: int = 0
    agent_active_count: int = 0
    _per_agent: dict[str, AgentMetrics] = field(default_factory=dict)

    def record_task_completion(
        self,
        agent_id: str,
        duration_ms: float,
        tokens_used: int,
    ) -> None:
        """Record a successful task completion."""
        self.agent_tasks_total += 1
        self.agent_execution_duration_ms += duration_ms

        agent_metrics = self._get_or_create_agent(agent_id)
        agent_metrics.tasks_total += 1
        agent_metrics.tasks_success += 1
        agent_metrics.execution_duration_ms_total += duration_ms
        agent_metrics.tokens_used_total += tokens_used

    def record_task_failure(self, agent_id: str, duration_ms: float = 0.0) -> None:
        """Record a task failure."""
        self.agent_tasks_total += 1
        self.agent_failures_total += 1
        self.agent_execution_duration_ms += duration_ms

        agent_metrics = self._get_or_create_agent(agent_id)
        agent_metrics.tasks_total += 1
        agent_metrics.tasks_failed += 1
        agent_metrics.execution_duration_ms_total += duration_ms

    def update_queue_depth(self, depth: int) -> None:
        """Update the current queue depth metric."""
        self.agent_queue_depth = depth

    def update_active_count(self, count: int) -> None:
        """Update the current active agent count."""
        self.agent_active_count = count

    def get_agent_stats(self, agent_id: str) -> AgentMetrics | None:
        """Get metrics for a specific agent."""
        return self._per_agent.get(agent_id)

    def get_all_agent_stats(self) -> dict[str, AgentMetrics]:
        """Get metrics for all agents."""
        return dict(self._per_agent)

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all metrics."""
        avg_duration = (
            self.agent_execution_duration_ms / self.agent_tasks_total
            if self.agent_tasks_total > 0
            else 0.0
        )
        success_rate = (
            (self.agent_tasks_total - self.agent_failures_total) / self.agent_tasks_total
            if self.agent_tasks_total > 0
            else 0.0
        )
        return {
            "tasks_total": self.agent_tasks_total,
            "failures_total": self.agent_failures_total,
            "avg_duration_ms": avg_duration,
            "success_rate": success_rate,
            "queue_depth": self.agent_queue_depth,
            "active_count": self.agent_active_count,
            "agents_tracked": len(self._per_agent),
        }

    def _get_or_create_agent(self, agent_id: str) -> AgentMetrics:
        """Get or create agent metrics entry."""
        if agent_id not in self._per_agent:
            self._per_agent[agent_id] = AgentMetrics(agent_id=agent_id)
        return self._per_agent[agent_id]
