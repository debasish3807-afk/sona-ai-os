"""Checkpoint and restore for agents."""

from __future__ import annotations

import uuid
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AgentCheckpoint:
    """Manages checkpoints for agent state persistence."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, dict[str, Any]] = {}

    def create(self, agent_id: str, state: dict[str, Any]) -> str:
        """Create a checkpoint and return its ID."""
        checkpoint_id = str(uuid.uuid4())
        self._checkpoints[checkpoint_id] = {
            "agent_id": agent_id,
            "state": state,
        }
        logger.debug("checkpoint_created", agent_id=agent_id, checkpoint_id=checkpoint_id)
        return checkpoint_id

    def restore(self, checkpoint_id: str) -> dict[str, Any] | None:
        """Restore a checkpoint by ID."""
        entry = self._checkpoints.get(checkpoint_id)
        if entry is None:
            return None
        return dict(entry["state"])

    def list_for_agent(self, agent_id: str) -> list[str]:
        """List checkpoint IDs for an agent."""
        return [cid for cid, entry in self._checkpoints.items() if entry["agent_id"] == agent_id]
