"""Cross-agent memory sharing with isolation control."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class SharedAgentMemory:
    """Cross-agent memory sharing with isolation control."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._access_log: list[dict[str, Any]] = []
        self._share_count = 0
        self._revoke_count = 0

    def share(self, from_agent: str, to_agent: str, key: str, value: Any) -> bool:
        """Share a memory value from one agent to another."""
        if not from_agent or not to_agent or not key:
            return False

        storage_key = f"{to_agent}:{key}"
        self._store[storage_key] = {
            "value": value,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "key": key,
            "timestamp": time.time(),
        }
        self._share_count += 1
        self._access_log.append(
            {
                "action": "share",
                "from": from_agent,
                "to": to_agent,
                "key": key,
                "timestamp": time.time(),
            }
        )
        logger.debug("memory_shared", from_agent=from_agent, to_agent=to_agent, key=key)
        return True

    def get_shared(self, agent_id: str, key: str) -> Any:
        """Get a shared memory value for an agent."""
        storage_key = f"{agent_id}:{key}"
        entry = self._store.get(storage_key)
        if entry is None:
            return None
        return entry["value"]

    def get_all_shared(self, agent_id: str) -> dict[str, Any]:
        """Get all shared memory values for an agent."""
        result: dict[str, Any] = {}
        prefix = f"{agent_id}:"
        for storage_key, entry in self._store.items():
            if storage_key.startswith(prefix):
                result[entry["key"]] = entry["value"]
        return result

    def revoke(self, from_agent: str, to_agent: str, key: str) -> bool:
        """Revoke a previously shared memory value."""
        storage_key = f"{to_agent}:{key}"
        entry = self._store.get(storage_key)
        if entry is None:
            return False
        if entry["from_agent"] != from_agent:
            return False

        del self._store[storage_key]
        self._revoke_count += 1
        self._access_log.append(
            {
                "action": "revoke",
                "from": from_agent,
                "to": to_agent,
                "key": key,
                "timestamp": time.time(),
            }
        )
        logger.debug("memory_revoked", from_agent=from_agent, to_agent=to_agent, key=key)
        return True

    def get_sharing_stats(self) -> dict[str, Any]:
        """Get statistics about memory sharing."""
        return {
            "total_shared": self._share_count,
            "total_revoked": self._revoke_count,
            "active_entries": len(self._store),
            "access_log_size": len(self._access_log),
        }
