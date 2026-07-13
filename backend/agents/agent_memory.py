"""Per-agent memory storage."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AgentMemory:
    """Provides per-agent memory for storing state and history."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self._store: dict[str, Any] = {}
        self._history: list[dict[str, Any]] = []

    def store(self, key: str, value: Any) -> None:
        """Store a key-value pair."""
        self._store[key] = value
        self._history.append({"action": "store", "key": key, "timestamp": time.time()})

    def get(self, key: str) -> Any | None:
        """Retrieve a value by key."""
        return self._store.get(key)

    def get_history(self) -> list[dict[str, Any]]:
        """Get the access history."""
        return list(self._history)

    def clear(self) -> None:
        """Clear all stored data."""
        self._store.clear()
        self._history.clear()
        logger.debug("agent_memory_cleared", agent_id=self.agent_id)

    @property
    def size(self) -> int:
        """Number of stored items."""
        return len(self._store)

    def export(self) -> dict[str, Any]:
        """Export memory state."""
        return {
            "agent_id": self.agent_id,
            "store": dict(self._store),
            "history": list(self._history),
        }

    def import_state(self, data: dict[str, Any]) -> None:
        """Import memory state."""
        self._store = data.get("store", {})
        self._history = data.get("history", [])
