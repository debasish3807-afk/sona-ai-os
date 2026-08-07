"""User memory manager.

Stores per-user preferences, traits, and persistent facts.
Key-value style access that never expires and influences
all retrieval operations.
"""

import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass
class UserPreference:
    """A single user preference entry."""

    key: str
    value: Any
    category: str = "general"
    confidence: float = 1.0
    source: str = "explicit"  # explicit, inferred, default


class UserMemory:
    """Per-user preference and trait storage.

    Provides key-value style access for user preferences that
    never expire and can influence all memory retrieval operations.
    """

    def __init__(self) -> None:
        # user_id -> key -> UserPreference
        self._store: dict[str, dict[str, UserPreference]] = {}
        self._lock = asyncio.Lock()

    async def set_preference(
        self,
        user_id: str,
        key: str,
        value: Any,
        category: str = "general",
        confidence: float = 1.0,
        source: str = "explicit",
    ) -> None:
        """Set a user preference."""
        async with self._lock:
            if user_id not in self._store:
                self._store[user_id] = {}
            self._store[user_id][key] = UserPreference(
                key=key,
                value=value,
                category=category,
                confidence=confidence,
                source=source,
            )

    async def get_preference(self, user_id: str, key: str) -> UserPreference | None:
        """Get a specific user preference by key."""
        async with self._lock:
            if user_id not in self._store:
                return None
            return self._store[user_id].get(key)

    async def get_value(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get a preference value directly, with optional default."""
        async with self._lock:
            if user_id not in self._store:
                return default
            pref = self._store[user_id].get(key)
            if pref is None:
                return default
            return pref.value

    async def get_by_category(self, user_id: str, category: str) -> list[UserPreference]:
        """Get all preferences in a category."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return [pref for pref in self._store[user_id].values() if pref.category == category]

    async def get_all(self, user_id: str) -> list[UserPreference]:
        """Get all preferences for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return list(self._store[user_id].values())

    async def delete_preference(self, user_id: str, key: str) -> bool:
        """Delete a specific preference."""
        async with self._lock:
            if user_id not in self._store:
                return False
            if key in self._store[user_id]:
                del self._store[user_id][key]
                return True
            return False

    async def delete_by_category(self, user_id: str, category: str) -> int:
        """Delete all preferences in a category."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            keys_to_delete = [
                k for k, pref in self._store[user_id].items() if pref.category == category
            ]
            for key in keys_to_delete:
                del self._store[user_id][key]
            return len(keys_to_delete)

    async def clear(self, user_id: str) -> int:
        """Clear all preferences for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            count = len(self._store[user_id])
            self._store[user_id].clear()
            return count

    async def count(self, user_id: str) -> int:
        """Get the number of stored preferences for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            return len(self._store[user_id])

    async def has_preference(self, user_id: str, key: str) -> bool:
        """Check if a preference exists."""
        async with self._lock:
            if user_id not in self._store:
                return False
            return key in self._store[user_id]

    async def get_keys(self, user_id: str) -> list[str]:
        """Get all preference keys for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return list(self._store[user_id].keys())
