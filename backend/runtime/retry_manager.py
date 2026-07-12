"""Retry management with exponential backoff and jitter."""

from __future__ import annotations

import random
from typing import Any

from config.logging import get_logger
from runtime.schemas import WorkflowTask

logger = get_logger(__name__)


class RetryManager:
    """Manages task retry logic with exponential backoff."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0) -> None:
        self._base_delay: float = base_delay
        self._max_delay: float = max_delay
        self._total_retries: int = 0
        self._retry_records: dict[str, int] = {}

    def should_retry(self, task: WorkflowTask) -> bool:
        """Determine if a task should be retried."""
        return task.retry_count < task.max_retries

    def get_delay(self, task: WorkflowTask) -> float:
        """Calculate delay with exponential backoff and jitter."""
        exponential = self._base_delay * (2**task.retry_count)
        capped = min(exponential, self._max_delay)
        jitter = random.uniform(0, capped * 0.1)  # noqa: S311
        return float(capped + jitter)

    def record_retry(self, task: WorkflowTask) -> WorkflowTask:
        """Record a retry attempt and increment the task's retry count."""
        task.retry_count += 1
        self._total_retries += 1
        self._retry_records[task.task_id] = task.retry_count
        logger.info(
            "retry_recorded",
            task_id=task.task_id,
            retry_count=task.retry_count,
        )
        return task

    def get_stats(self) -> dict[str, Any]:
        """Return retry statistics."""
        return {
            "total_retries": self._total_retries,
            "by_task": dict(self._retry_records),
            "base_delay": self._base_delay,
            "max_delay": self._max_delay,
        }
