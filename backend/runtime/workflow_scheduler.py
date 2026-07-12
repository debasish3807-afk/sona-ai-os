"""Workflow scheduling and concurrency management."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from runtime.schemas import Workflow, WorkflowState

logger = get_logger(__name__)


class WorkflowScheduler:
    """Manages workflow scheduling with concurrency limits."""

    def __init__(self, max_concurrent: int = 4) -> None:
        self._pending: list[Workflow] = []
        self._running: dict[str, Workflow] = {}
        self._max_concurrent: int = max_concurrent

    def schedule(self, workflow: Workflow) -> bool:
        """Schedule a workflow for execution."""
        if len(self._running) >= self._max_concurrent:
            workflow.state = WorkflowState.QUEUED
            self._pending.append(workflow)
            logger.info("workflow_queued", workflow_id=workflow.workflow_id)
            return True
        workflow.state = WorkflowState.READY
        self._pending.append(workflow)
        logger.info("workflow_scheduled", workflow_id=workflow.workflow_id)
        return True

    def get_next(self) -> Workflow | None:
        """Get the next workflow ready for execution."""
        if not self._pending:
            return None
        if len(self._running) >= self._max_concurrent:
            return None
        return self._pending[0]

    def mark_running(self, workflow_id: str) -> bool:
        """Mark a workflow as running."""
        for i, wf in enumerate(self._pending):
            if wf.workflow_id == workflow_id:
                wf.state = WorkflowState.RUNNING
                self._running[workflow_id] = wf
                self._pending.pop(i)
                logger.info("workflow_running", workflow_id=workflow_id)
                return True
        return False

    def mark_completed(self, workflow_id: str) -> bool:
        """Mark a workflow as completed."""
        if workflow_id in self._running:
            self._running[workflow_id].state = WorkflowState.COMPLETED
            del self._running[workflow_id]
            logger.info("workflow_completed", workflow_id=workflow_id)
            return True
        return False

    def mark_failed(self, workflow_id: str) -> bool:
        """Mark a workflow as failed."""
        if workflow_id in self._running:
            self._running[workflow_id].state = WorkflowState.FAILED
            del self._running[workflow_id]
            logger.info("workflow_failed", workflow_id=workflow_id)
            return True
        return False

    def cancel(self, workflow_id: str) -> bool:
        """Cancel a workflow (from pending or running)."""
        for i, wf in enumerate(self._pending):
            if wf.workflow_id == workflow_id:
                wf.state = WorkflowState.CANCELLED
                self._pending.pop(i)
                logger.info("workflow_cancelled", workflow_id=workflow_id)
                return True
        if workflow_id in self._running:
            self._running[workflow_id].state = WorkflowState.CANCELLED
            del self._running[workflow_id]
            logger.info("workflow_cancelled", workflow_id=workflow_id)
            return True
        return False

    def list_pending(self) -> list[Workflow]:
        """Return all pending workflows."""
        return list(self._pending)

    def list_running(self) -> list[Workflow]:
        """Return all running workflows."""
        return list(self._running.values())

    def get_stats(self) -> dict[str, Any]:
        """Return scheduler statistics."""
        return {
            "pending_count": len(self._pending),
            "running_count": len(self._running),
            "max_concurrent": self._max_concurrent,
        }
