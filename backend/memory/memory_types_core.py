"""Core memory store types: Working, Conversation, Episodic."""

from __future__ import annotations

import time
import uuid
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class WorkingMemory:
    """Fast key-value working memory for active session context."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._updated_at: float = time.time()

    def store(self, key: str, val: Any) -> None:
        """Store a value by key."""
        self._store[key] = val
        self._updated_at = time.time()

    def get(self, key: str) -> Any:
        """Get a value by key."""
        return self._store.get(key)

    def clear(self) -> None:
        """Clear all working memory."""
        self._store.clear()
        self._updated_at = time.time()

    def snapshot(self) -> dict[str, Any]:
        """Return a snapshot of current working memory state."""
        return {"data": dict(self._store), "updated_at": self._updated_at}

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return self.snapshot()


class ConversationMemory:
    """Conversation history memory with multi-conversation support."""

    def __init__(self) -> None:
        self._conversations: dict[str, list[dict[str, Any]]] = {}

    def create_conversation(self, user_id: str) -> str:
        """Create a new conversation. Returns conversation_id."""
        conv_id = str(uuid.uuid4())
        self._conversations[conv_id] = []
        logger.debug("conversation_created", conv_id=conv_id, user_id=user_id)
        return conv_id

    def add_message(self, conv_id: str, role: str, content: str) -> None:
        """Add a message to a conversation."""
        if conv_id not in self._conversations:
            self._conversations[conv_id] = []
        self._conversations[conv_id].append(
            {
                "message_id": str(uuid.uuid4()),
                "role": role,
                "content": content,
                "timestamp": time.time(),
            }
        )

    def get_history(self, conv_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get conversation message history."""
        messages = self._conversations.get(conv_id, [])
        return messages[-limit:]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {"conversations": dict(self._conversations)}


class EpisodicMemory:
    """Event-based episodic memory for experiences and outcomes."""

    def __init__(self) -> None:
        self._episodes: list[dict[str, Any]] = []

    def store_episode(
        self,
        event: str,
        context: str,
        outcome: str,
        importance: float = 0.5,
    ) -> None:
        """Store an episode with event, context, and outcome."""
        self._episodes.append(
            {
                "episode_id": str(uuid.uuid4()),
                "event": event,
                "context": context,
                "outcome": outcome,
                "importance": importance,
                "timestamp": time.time(),
            }
        )

    def get_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get most recent episodes."""
        return self._episodes[-limit:]

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search episodes by text matching."""
        query_lower = query.lower()
        results = [
            ep
            for ep in self._episodes
            if query_lower in ep["event"].lower()
            or query_lower in ep["context"].lower()
            or query_lower in ep["outcome"].lower()
        ]
        results.sort(key=lambda e: e["importance"], reverse=True)
        return results[:limit]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {"episodes": self._episodes, "count": len(self._episodes)}
