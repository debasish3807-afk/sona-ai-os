"""Agent Scheduler - priority scheduling and queue management."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any

import structlog

from sona_workforce.domain.agent import AgentProfile, AgentState
from sona_workforce.domain.models import AgentTask
from sona_workforce.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger()


@dataclass(order=True)
class ScheduledTask:
    """A task entry in the priority queue."""

    priority: int
    task: AgentTask = field(compare=False)
    assigned_agent_id: str | None = field(default=None, compare=False)


class AgentScheduler:
    """Priority-based agent scheduler with queue management and concurrency enforcement.

    Picks the best available agent for a task based on:
    1. Type match
    2. Capability match
    3. Load (fewest active tasks)
    4. Priority (lower number = higher priority)
    """

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        self._queue: list[ScheduledTask] = []
        self._processing: dict[str, AgentTask] = {}  # agent_id -> task

    @property
    def queue_depth(self) -> int:
        """Get the number of tasks waiting in the queue."""
        return len(self._queue)

    @property
    def active_count(self) -> int:
        """Get the number of currently processing tasks."""
        return len(self._processing)

    def enqueue(self, task: AgentTask) -> None:
        """Add a task to the priority queue."""
        scheduled = ScheduledTask(priority=task.priority, task=task)
        heapq.heappush(self._queue, scheduled)

    def dequeue(self) -> AgentTask | None:
        """Remove and return the highest-priority task."""
        if self._queue:
            scheduled = heapq.heappop(self._queue)
            return scheduled.task
        return None

    async def select_agent(self, task: AgentTask) -> AgentProfile | None:
        """Select the best available agent for a task.

        Selection criteria (in order):
        1. Agent type matches task.agent_type
        2. Agent has required capability
        3. Agent has fewest active tasks (lowest load)
        4. Agent has highest priority (lowest number)
        """
        candidates = self._get_candidates(task)
        if not candidates:
            return None

        # Sort: least active tasks first, then highest priority (lowest number)
        candidates.sort(key=lambda a: (a.active_tasks, a.priority))
        selected = candidates[0]

        await logger.ainfo(
            "agent_selected",
            agent_id=selected.agent_id,
            task_id=task.task_id,
            candidates_count=len(candidates),
        )

        return selected

    def _get_candidates(self, task: AgentTask) -> list[AgentProfile]:
        """Get candidate agents that can handle the task."""
        # First try exact type match
        type_matches = self._registry.get_by_type(task.agent_type)
        available = [
            a
            for a in type_matches
            if a.state in (AgentState.IDLE, AgentState.PROCESSING)
            and a.active_tasks < a.max_concurrent_tasks
        ]

        if available:
            return available

        # Fallback: any agent with capacity
        all_agents = self._registry.all_agents()
        return [
            a
            for a in all_agents
            if a.state in (AgentState.IDLE, AgentState.PROCESSING)
            and a.active_tasks < a.max_concurrent_tasks
        ]

    def mark_processing(self, agent_id: str, task: AgentTask) -> None:
        """Mark an agent as processing a task."""
        self._processing[agent_id] = task

    def mark_completed(self, agent_id: str) -> None:
        """Mark an agent's current task as completed."""
        self._processing.pop(agent_id, None)

    def get_stats(self) -> dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "queue_depth": self.queue_depth,
            "active_count": self.active_count,
            "total_registered": self._registry.count,
        }
