"""Checkpoint management for workflow state persistence."""

from __future__ import annotations

import time
import uuid
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """Manages workflow checkpoints for recovery and rollback."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, dict[str, Any]] = {}
        self._workflow_index: dict[str, list[str]] = {}

    def create(self, workflow_id: str, state: dict[str, Any]) -> str:
        """Create a checkpoint for a workflow and return its ID."""
        checkpoint_id = str(uuid.uuid4())
        self._checkpoints[checkpoint_id] = {
            "checkpoint_id": checkpoint_id,
            "workflow_id": workflow_id,
            "state": state,
            "created_at": time.time(),
        }
        if workflow_id not in self._workflow_index:
            self._workflow_index[workflow_id] = []
        self._workflow_index[workflow_id].append(checkpoint_id)
        logger.info("checkpoint_created", checkpoint_id=checkpoint_id, workflow_id=workflow_id)
        return checkpoint_id

    def load(self, checkpoint_id: str) -> dict[str, Any] | None:
        """Load a checkpoint by ID."""
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint:
            return dict(checkpoint["state"])
        return None

    def load_latest(self, workflow_id: str) -> dict[str, Any] | None:
        """Load the latest checkpoint for a workflow."""
        ids = self._workflow_index.get(workflow_id, [])
        if not ids:
            return None
        latest_id = ids[-1]
        return self.load(latest_id)

    def list_for_workflow(self, workflow_id: str) -> list[str]:
        """List all checkpoint IDs for a workflow."""
        return list(self._workflow_index.get(workflow_id, []))

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint by ID."""
        if checkpoint_id not in self._checkpoints:
            return False
        cp = self._checkpoints[checkpoint_id]
        workflow_id = cp["workflow_id"]
        del self._checkpoints[checkpoint_id]
        if workflow_id in self._workflow_index:
            self._workflow_index[workflow_id] = [
                cid for cid in self._workflow_index[workflow_id] if cid != checkpoint_id
            ]
        logger.info("checkpoint_deleted", checkpoint_id=checkpoint_id)
        return True

    def get_stats(self) -> dict[str, Any]:
        """Return checkpoint statistics."""
        return {
            "total_checkpoints": len(self._checkpoints),
            "workflows_with_checkpoints": len(self._workflow_index),
        }
