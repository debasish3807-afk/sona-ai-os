"""Recovery management for failed or interrupted workflows."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger
from runtime.checkpoint_manager import CheckpointManager
from runtime.schemas import Workflow, WorkflowState

logger = get_logger(__name__)


class RecoveryManager:
    """Manages workflow recovery from checkpoints."""

    def __init__(self) -> None:
        self._recovery_log: list[dict[str, Any]] = []

    def recover(self, workflow: Workflow, checkpoint_manager: CheckpointManager) -> Workflow | None:
        """Attempt to recover a workflow from its latest checkpoint."""
        if not self.can_recover(workflow):
            return None

        checkpoint_state = checkpoint_manager.load_latest(workflow.workflow_id)
        if checkpoint_state is None:
            self._recovery_log.append(
                {
                    "workflow_id": workflow.workflow_id,
                    "timestamp": time.time(),
                    "success": False,
                    "reason": "no_checkpoint_found",
                }
            )
            return None

        workflow.state = WorkflowState.RECOVERING
        workflow.metadata["recovered_from"] = checkpoint_state.get("checkpoint_id", "unknown")
        workflow.state = WorkflowState.READY

        self._recovery_log.append(
            {
                "workflow_id": workflow.workflow_id,
                "timestamp": time.time(),
                "success": True,
                "reason": "recovered_from_checkpoint",
            }
        )
        logger.info("workflow_recovered", workflow_id=workflow.workflow_id)
        return workflow

    def can_recover(self, workflow: Workflow) -> bool:
        """Check if a workflow can be recovered."""
        recoverable_states = (
            WorkflowState.FAILED,
            WorkflowState.BLOCKED,
            WorkflowState.PAUSED,
        )
        return workflow.state in recoverable_states

    def get_recovery_log(self) -> list[dict[str, Any]]:
        """Return the full recovery log."""
        return list(self._recovery_log)
