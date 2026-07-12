"""Workflow monitoring and metrics collection."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class WorkflowMonitor:
    """Collects and reports workflow execution metrics."""

    def __init__(self) -> None:
        self._metrics: dict[str, dict[str, Any]] = {}
        self._total_workflows: int = 0
        self._completed_durations: list[float] = []
        self._failure_count: int = 0

    def record_start(self, workflow_id: str) -> None:
        """Record the start of a workflow execution."""
        self._metrics[workflow_id] = {
            "started_at": time.time(),
            "tasks_completed": 0,
            "tasks_failed": 0,
            "task_durations": [],
        }
        self._total_workflows += 1
        logger.debug("monitor_start", workflow_id=workflow_id)

    def record_task_complete(self, workflow_id: str, task_id: str, duration_ms: float) -> None:
        """Record a completed task within a workflow."""
        if workflow_id in self._metrics:
            self._metrics[workflow_id]["tasks_completed"] += 1
            self._metrics[workflow_id]["task_durations"].append(duration_ms)

    def record_task_failure(self, workflow_id: str, task_id: str, error: str) -> None:
        """Record a failed task within a workflow."""
        if workflow_id in self._metrics:
            self._metrics[workflow_id]["tasks_failed"] += 1
        self._failure_count += 1

    def record_complete(self, workflow_id: str, total_ms: float) -> None:
        """Record the completion of a workflow."""
        if workflow_id in self._metrics:
            self._metrics[workflow_id]["total_duration_ms"] = total_ms
            self._metrics[workflow_id]["completed_at"] = time.time()
        self._completed_durations.append(total_ms)
        logger.debug("monitor_complete", workflow_id=workflow_id, total_ms=total_ms)

    def get_workflow_metrics(self, workflow_id: str) -> dict[str, Any]:
        """Return metrics for a specific workflow."""
        return dict(self._metrics.get(workflow_id, {}))

    def get_summary(self) -> dict[str, Any]:
        """Return aggregate monitoring summary."""
        avg_duration = 0.0
        if self._completed_durations:
            avg_duration = sum(self._completed_durations) / len(self._completed_durations)

        failure_rate = 0.0
        if self._total_workflows > 0:
            failure_rate = self._failure_count / self._total_workflows

        return {
            "total_workflows": self._total_workflows,
            "avg_duration_ms": avg_duration,
            "failure_rate": failure_rate,
            "failure_count": self._failure_count,
            "active_workflows": len([m for m in self._metrics.values() if "completed_at" not in m]),
        }
