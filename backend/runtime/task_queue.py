"""Priority-based task queue with dead-letter support."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from runtime.schemas import QueuePriority, WorkflowTask

logger = get_logger(__name__)


class TaskQueue:
    """Multi-priority task queue with dead-letter handling."""

    def __init__(self) -> None:
        self._queues: dict[QueuePriority, list[WorkflowTask]] = {
            priority: [] for priority in QueuePriority
        }
        self._dead_letters: list[tuple[WorkflowTask, str]] = []

    def enqueue(self, task: WorkflowTask) -> None:
        """Add a task to its priority queue."""
        self._queues[task.priority].append(task)
        logger.debug("task_enqueued", task_id=task.task_id, priority=task.priority.name)

    def dequeue(self) -> WorkflowTask | None:
        """Remove and return the highest-priority task, or None if empty."""
        for priority in QueuePriority:
            if self._queues[priority]:
                task = self._queues[priority].pop(0)
                logger.debug("task_dequeued", task_id=task.task_id)
                return task
        return None

    def peek(self) -> WorkflowTask | None:
        """Return the highest-priority task without removing it."""
        for priority in QueuePriority:
            if self._queues[priority]:
                return self._queues[priority][0]
        return None

    def size(self) -> int:
        """Return total number of tasks across all priority queues."""
        return sum(len(q) for q in self._queues.values())

    def is_empty(self) -> bool:
        """Check if all priority queues are empty."""
        return self.size() == 0

    def move_to_dead_letter(self, task: WorkflowTask, reason: str) -> None:
        """Move a failed task to the dead-letter queue."""
        self._dead_letters.append((task, reason))
        logger.warning("task_dead_lettered", task_id=task.task_id, reason=reason)

    def get_dead_letters(self) -> list[WorkflowTask]:
        """Return all dead-letter tasks."""
        return [t for t, _ in self._dead_letters]

    def clear_dead_letters(self) -> int:
        """Clear dead-letter queue and return count of cleared items."""
        count = len(self._dead_letters)
        self._dead_letters.clear()
        return count

    def get_stats(self) -> dict[str, Any]:
        """Return queue statistics."""
        return {
            "total_size": self.size(),
            "size_by_priority": {p.name: len(self._queues[p]) for p in QueuePriority},
            "dead_letter_count": len(self._dead_letters),
        }
