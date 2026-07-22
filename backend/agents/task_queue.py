"""Persistent task queue with priority ordering, retry, and status tracking."""

from __future__ import annotations

import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class QueueTask:
    """A task in the queue."""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.QUEUED
    priority: int = 50
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    assigned_at: float = 0.0
    completed_at: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    assigned_agent_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "assigned_at": self.assigned_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "assigned_agent_id": self.assigned_agent_id,
        }


class TaskQueue:
    """Priority-ordered task queue with retry support."""

    def __init__(self) -> None:
        self._tasks: dict[str, QueueTask] = OrderedDict()
        self._max_size = 10000

    def enqueue(
        self,
        agent_type: str,
        description: str,
        payload: dict[str, Any] | None = None,
        priority: int = 50,
        max_retries: int = 3,
    ) -> str:
        """Enqueue a new task."""
        if len(self._tasks) >= self._max_size:
            raise RuntimeError(f"Task queue full ({self._max_size})")
        task = QueueTask(
            agent_type=agent_type,
            description=description,
            payload=payload or {},
            priority=priority,
            max_retries=max_retries,
        )
        self._tasks[task.task_id] = task
        logger.debug("task_enqueued", task_id=task.task_id, agent_type=agent_type)
        return task.task_id

    def dequeue(self, agent_type: str | None = None) -> QueueTask | None:
        """Dequeue the highest-priority task, optionally filtered by agent type."""
        candidates = [t for t in self._tasks.values() if t.status == TaskStatus.QUEUED]
        if agent_type:
            candidates = [t for t in candidates if t.agent_type == agent_type]
        if not candidates:
            return None
        candidates.sort(key=lambda t: (t.priority, t.created_at))
        task = candidates[0]
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = time.time()
        return task

    def assign(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to an agent."""
        task = self._tasks.get(task_id)
        if task is None or task.status != TaskStatus.QUEUED:
            return False
        task.status = TaskStatus.ASSIGNED
        task.assigned_agent_id = agent_id
        task.assigned_at = time.time()
        return True

    def complete(self, task_id: str, result: dict[str, Any] | None = None) -> bool:
        """Mark a task as completed."""
        task = self._tasks.get(task_id)
        if task is None:
            return False
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.result = result or {}
        return True

    def fail(self, task_id: str, error: str = "") -> bool:
        """Mark a task as failed (with optional retry)."""
        task = self._tasks.get(task_id)
        if task is None:
            return False
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING
            task.status = TaskStatus.QUEUED
            logger.info("task_retry", task_id=task_id, attempt=task.retry_count)
        else:
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = time.time()
        return True

    def cancel(self, task_id: str) -> bool:
        """Cancel a queued or running task."""
        task = self._tasks.get(task_id)
        if task is None or task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            return False
        task.status = TaskStatus.CANCELLED
        task.completed_at = time.time()
        return True

    def get(self, task_id: str) -> QueueTask | None:
        return self._tasks.get(task_id)

    def list_tasks(
        self, status: TaskStatus | None = None, agent_type: str | None = None, limit: int = 100
    ) -> list[QueueTask]:
        candidates = list(self._tasks.values())
        if status:
            candidates = [t for t in candidates if t.status == status]
        if agent_type:
            candidates = [t for t in candidates if t.agent_type == agent_type]
        candidates.sort(key=lambda t: t.created_at, reverse=True)
        return candidates[:limit]

    def get_stats(self) -> dict[str, Any]:
        stats: dict[str, int] = {"total": len(self._tasks)}
        for s in TaskStatus:
            count = sum(1 for t in self._tasks.values() if t.status == s)
            if count:
                stats[s.value] = count
        return stats
