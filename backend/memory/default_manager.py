"""Default Memory Manager — concrete implementation of MemoryManager."""

from __future__ import annotations

import time
import uuid
from typing import Any

from config.logging import get_logger

from .memory_router import MemoryRouter
from .memory_types import (
    ConversationMemory,
    EpisodicMemory,
    KnowledgeMemory,
    LongTermMemory,
    SemanticMemory,
    WorkingMemory,
)

logger = get_logger(__name__)


class MemoryEntry:
    """A stored memory entry."""

    def __init__(
        self,
        content: str,
        memory_type: str = "conversation",
        scope: str = "session",
        session_id: str = "",
        user_id: str = "",
        importance: float = 0.5,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.entry_id: str = str(uuid.uuid4())
        self.content = content
        self.memory_type = memory_type
        self.scope = scope
        self.session_id = session_id
        self.user_id = user_id
        self.importance = importance
        self.tags: list[str] = tags or []
        self.metadata: dict[str, Any] = metadata or {}
        self.created_at: float = time.time()
        self.accessed_at: float = time.time()
        self.access_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "scope": self.scope,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
        }


class DefaultMemoryManager:
    """Concrete memory manager with persistence support.

    Provides store, retrieve, search, consolidation, and context assembly.
    Uses in-memory index with optional persistence backend.
    """

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}
        self._conversations: dict[str, list[dict[str, Any]]] = {}
        self._initialized: bool = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the memory system."""
        self._initialized = True
        logger.info("memory_manager_initialized")

    async def shutdown(self) -> None:
        """Shutdown the memory system."""
        self._initialized = False
        logger.info("memory_manager_shutdown")

    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry. Returns entry_id."""
        self._entries[entry.entry_id] = entry
        logger.debug("memory_stored", entry_id=entry.entry_id, memory_type=entry.memory_type)
        return entry.entry_id

    async def get(self, entry_id: str) -> MemoryEntry | None:
        """Retrieve a memory entry by ID."""
        entry = self._entries.get(entry_id)
        if entry is not None:
            entry.accessed_at = time.time()
            entry.access_count += 1
        return entry

    async def search(
        self,
        query: str,
        memory_type: str | None = None,
        scope: str | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Search memories by content relevance."""
        results: list[MemoryEntry] = []
        query_lower = query.lower()

        for entry in self._entries.values():
            if memory_type and entry.memory_type != memory_type:
                continue
            if scope and entry.scope != scope:
                continue
            if query_lower in entry.content.lower() or any(
                query_lower in tag.lower() for tag in entry.tags
            ):
                results.append(entry)

        results.sort(key=lambda e: e.importance, reverse=True)
        return results[:limit]

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    async def create_conversation(self, user_id: str, title: str = "") -> str:
        """Create a new conversation. Returns conversation_id."""
        conversation_id = str(uuid.uuid4())
        self._conversations[conversation_id] = []
        logger.debug("conversation_created", conversation_id=conversation_id)
        return conversation_id

    async def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to a conversation."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append(
            {
                "message_id": str(uuid.uuid4()),
                "role": role,
                "content": content,
                "timestamp": time.time(),
            }
        )

    async def get_history(self, conversation_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get conversation message history."""
        messages = self._conversations.get(conversation_id, [])
        return messages[-limit:]

    async def consolidate(self) -> dict[str, Any]:
        """Run memory consolidation — merge low-importance old memories."""
        now = time.time()
        consolidated = 0
        for entry in list(self._entries.values()):
            age_hours = (now - entry.created_at) / 3600
            if age_hours > 24 and entry.importance < 0.3 and entry.access_count == 0:
                del self._entries[entry.entry_id]
                consolidated += 1
        logger.info("memory_consolidated", removed=consolidated)
        return {"consolidated": consolidated, "remaining": len(self._entries)}

    async def get_context(
        self, session_id: str, query: str, max_entries: int = 20
    ) -> list[dict[str, Any]]:
        """Assemble context for a session."""
        relevant = await self.search(query, limit=max_entries)
        session_entries = [e for e in self._entries.values() if e.session_id == session_id]
        session_entries.sort(key=lambda e: e.created_at, reverse=True)

        combined: list[MemoryEntry] = []
        seen: set[str] = set()
        for entry in relevant + session_entries[:max_entries]:
            if entry.entry_id not in seen:
                combined.append(entry)
                seen.add(entry.entry_id)

        return [e.to_dict() for e in combined[:max_entries]]

    async def hydrate_from_persistence(self, records: list[dict[str, Any]]) -> int:
        """Hydrate memory state from persistence records."""
        loaded = 0
        for record in records:
            entry = MemoryEntry(
                content=record.get("content", ""),
                memory_type=record.get("memory_type", "conversation"),
                scope=record.get("scope", "session"),
                session_id=record.get("session_id", ""),
                user_id=record.get("user_id", ""),
                importance=record.get("importance", 0.5),
                tags=record.get("tags", []),
                metadata=record.get("metadata", {}),
            )
            entry.entry_id = record.get("entry_id", entry.entry_id)
            entry.created_at = record.get("created_at", entry.created_at)
            self._entries[entry.entry_id] = entry
            loaded += 1
        logger.info("memory_hydrated", entries=loaded)
        return loaded

    def get_stats(self) -> dict[str, Any]:
        """Get memory system statistics."""
        by_type: dict[str, int] = {}
        for entry in self._entries.values():
            by_type[entry.memory_type] = by_type.get(entry.memory_type, 0) + 1
        return {
            "total_entries": len(self._entries),
            "total_conversations": len(self._conversations),
            "by_type": by_type,
            "initialized": self._initialized,
        }

    def get_memory_router(self) -> MemoryRouter:
        """Get a MemoryRouter with all 6 memory types initialized.

        Returns:
            A configured MemoryRouter instance.
        """
        return MemoryRouter(
            working=WorkingMemory(),
            conversation=ConversationMemory(),
            episodic=EpisodicMemory(),
            semantic=SemanticMemory(),
            long_term=LongTermMemory(),
            knowledge=KnowledgeMemory(),
        )
