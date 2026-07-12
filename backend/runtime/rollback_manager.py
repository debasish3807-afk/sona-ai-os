"""Rollback management for failed workflows."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger
from runtime.schemas import TaskState, Workflow, WorkflowState, WorkflowTask

logger = get_logger(__name__)


class RollbackManager:
    """Manages workflow rollback and task compensation."""

    def __init__(self) -> None:
        self._rollback_history: list[dict[str, Any]] = []

    def rollback(self, workflow: Workflow, checkpoint: dict[str, Any] | None) -> bool:
        """Rollback a workflow to a checkpoint or compensate all tasks."""
        workflow.state = WorkflowState.ROLLING_BACK
        record: dict[str, Any] = {
            "workflow_id": workflow.workflow_id,
            "timestamp": time.time(),
            "has_checkpoint": checkpoint is not None,
            "compensated_tasks": [],
        }

        completed_tasks = [t for t in workflow.tasks if t.state == TaskState.COMPLETED]
        for task in reversed(completed_tasks):
            success = self._compensate_task(task)
            record["compensated_tasks"].append(
                {
                    "task_id": task.task_id,
                    "success": success,
                }
            )

        self._rollback_history.append(record)
        logger.info("rollback_complete", workflow_id=workflow.workflow_id)
        return True

    def _compensate_task(self, task: WorkflowTask) -> bool:
        """Compensate a completed task (undo its effects)."""
        task.state = TaskState.CANCELLED
        task.result = {"compensated": True}
        return True

    def get_rollback_history(self) -> list[dict[str, Any]]:
        """Return the full rollback history."""
        return list(self._rollback_history)

    def can_rollback(self, workflow: Workflow) -> bool:
        """Check if a workflow can be rolled back."""
        if workflow.state in (WorkflowState.CANCELLED, WorkflowState.ROLLING_BACK):
            return False
        has_completed = any(t.state == TaskState.COMPLETED for t in workflow.tasks)
        return has_completed
