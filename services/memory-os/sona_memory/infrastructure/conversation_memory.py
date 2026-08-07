"""Conversation memory manager.

Session-scoped conversation history using a ring buffer approach
for fast recent-history retrieval with bounded capacity.
"""

import asyncio
from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime

from sona_memory.domain.models import MemoryEntry, MemoryType


@dataclass
class ConversationConfig:
    """Configuration for conversation memory."""

    max_messages_per_session: int = 100
    max_sessions_per_user: int = 50


class ConversationMemory:
    """Session-scoped conversation history with ring buffer.

    Each session has a bounded deque (ring buffer) that automatically
    drops oldest messages when the limit is reached.
    """

    def __init__(self, config: ConversationConfig | None = None) -> None:
        self._config = config or ConversationConfig()
        # user_id -> session_id -> deque of entries
        self._store: dict[str, dict[str, deque[MemoryEntry]]] = {}
        self._lock = asyncio.Lock()

    @property
    def config(self) -> ConversationConfig:
        """Current configuration."""
        return self._config

    async def add_message(self, user_id: str, session_id: str, entry: MemoryEntry) -> str:
        """Add a message to the conversation history.

        Automatically drops oldest messages when buffer is full.
        """
        async with self._lock:
            if user_id not in self._store:
                self._store[user_id] = {}

            user_sessions = self._store[user_id]

            # Evict oldest session if at session limit
            while len(user_sessions) >= self._config.max_sessions_per_user:
                if session_id not in user_sessions:
                    # Remove the oldest session (first key)
                    oldest_key = next(iter(user_sessions))
                    del user_sessions[oldest_key]
                else:
                    break

            if session_id not in user_sessions:
                user_sessions[session_id] = deque(maxlen=self._config.max_messages_per_session)

            # Ensure memory type is WORKING for conversation
            if entry.memory_type != MemoryType.WORKING:
                entry = replace(entry, memory_type=MemoryType.WORKING)

            # Add session metadata
            if entry.metadata is None:
                entry = replace(entry, metadata={"session_id": session_id})
            elif "session_id" not in entry.metadata:
                new_meta = dict(entry.metadata)
                new_meta["session_id"] = session_id
                entry = replace(entry, metadata=new_meta)

            user_sessions[session_id].append(entry)
            return entry.id

    async def get_history(
        self, user_id: str, session_id: str, limit: int | None = None
    ) -> list[MemoryEntry]:
        """Get conversation history for a session.

        Returns messages in chronological order (oldest first).
        """
        async with self._lock:
            if user_id not in self._store:
                return []
            if session_id not in self._store[user_id]:
                return []

            messages = list(self._store[user_id][session_id])
            if limit is not None:
                return messages[-limit:]
            return messages

    async def get_recent(self, user_id: str, session_id: str, limit: int = 10) -> list[MemoryEntry]:
        """Get the most recent messages from a session."""
        async with self._lock:
            if user_id not in self._store:
                return []
            if session_id not in self._store[user_id]:
                return []

            messages = list(self._store[user_id][session_id])
            return messages[-limit:]

    async def get_sessions(self, user_id: str) -> list[str]:
        """Get all session IDs for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return list(self._store[user_id].keys())

    async def session_length(self, user_id: str, session_id: str) -> int:
        """Get the number of messages in a session."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            if session_id not in self._store[user_id]:
                return 0
            return len(self._store[user_id][session_id])

    async def clear_session(self, user_id: str, session_id: str) -> int:
        """Clear all messages in a session."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            if session_id not in self._store[user_id]:
                return 0
            count = len(self._store[user_id][session_id])
            del self._store[user_id][session_id]
            return count

    async def clear_user(self, user_id: str) -> int:
        """Clear all sessions for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            total = sum(len(session) for session in self._store[user_id].values())
            del self._store[user_id]
            return total

    async def get_all_messages(self, user_id: str) -> list[MemoryEntry]:
        """Get all messages across all sessions for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            results: list[MemoryEntry] = []
            for session in self._store[user_id].values():
                results.extend(session)
            return results

    async def find_by_content(
        self, user_id: str, session_id: str, content_substring: str
    ) -> list[MemoryEntry]:
        """Find messages containing a substring."""
        async with self._lock:
            if user_id not in self._store:
                return []
            if session_id not in self._store[user_id]:
                return []
            return [
                entry
                for entry in self._store[user_id][session_id]
                if content_substring.lower() in entry.content.lower()
            ]

    async def get_messages_after(
        self, user_id: str, session_id: str, after: datetime
    ) -> list[MemoryEntry]:
        """Get messages created after a specific time."""
        async with self._lock:
            if user_id not in self._store:
                return []
            if session_id not in self._store[user_id]:
                return []

            after_ts = after.timestamp()
            return [
                entry
                for entry in self._store[user_id][session_id]
                if entry.created_at is not None and entry.created_at.timestamp() > after_ts
            ]
