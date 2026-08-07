"""Long-term memory manager.

Provides unlimited-capacity persistent memory with embedding-based
similarity search. No auto-expiration.
"""

import asyncio
from dataclasses import dataclass, replace

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.embedding_service import EmbeddingService, cosine_similarity


@dataclass
class LongTermConfig:
    """Configuration for long-term memory."""

    similarity_threshold: float = 0.3
    default_top_k: int = 10


class LongTermMemory:
    """Unlimited-capacity long-term memory with embedding-based retrieval.

    Entries require embeddings for storage and support similarity search.
    No auto-expiration — entries persist until explicitly removed.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        config: LongTermConfig | None = None,
    ) -> None:
        self._embedding = embedding_service
        self._config = config or LongTermConfig()
        # user_id -> list of entries (all must have embeddings)
        self._store: dict[str, list[MemoryEntry]] = {}
        self._lock = asyncio.Lock()

    @property
    def config(self) -> LongTermConfig:
        """Current configuration."""
        return self._config

    async def store(self, user_id: str, entry: MemoryEntry) -> str:
        """Store an entry with embedding in long-term memory.

        If the entry lacks an embedding, one is generated automatically.
        """
        async with self._lock:
            if user_id not in self._store:
                self._store[user_id] = []

            # Ensure memory type
            if entry.memory_type != MemoryType.LONG_TERM:
                entry = replace(entry, memory_type=MemoryType.LONG_TERM)

        # Generate embedding if missing (outside lock for async)
        if entry.embedding is None:
            embedding = await self._embedding.embed(entry.content)
            entry = replace(entry, embedding=embedding)

        async with self._lock:
            if user_id not in self._store:
                self._store[user_id] = []
            self._store[user_id].append(entry)
            return entry.id

    async def search(
        self,
        user_id: str,
        query_text: str,
        top_k: int | None = None,
        min_importance: float = 0.0,
    ) -> list[tuple[MemoryEntry, float]]:
        """Search for similar memories using embedding similarity.

        Returns entries with their similarity scores, sorted by similarity.
        """
        top_k = top_k or self._config.default_top_k
        query_embedding = await self._embedding.embed(query_text)

        async with self._lock:
            if user_id not in self._store:
                return []

            scored: list[tuple[MemoryEntry, float]] = []
            for entry in self._store[user_id]:
                if entry.importance < min_importance:
                    continue
                if entry.embedding is None:
                    continue
                sim = cosine_similarity(query_embedding, entry.embedding)
                if sim >= self._config.similarity_threshold:
                    scored.append((entry, sim))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]

    async def get(self, user_id: str, memory_id: str) -> MemoryEntry | None:
        """Get a specific entry by ID."""
        async with self._lock:
            if user_id not in self._store:
                return None
            for entry in self._store[user_id]:
                if entry.id == memory_id:
                    return entry
            return None

    async def get_all(self, user_id: str) -> list[MemoryEntry]:
        """Get all entries for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return list(self._store[user_id])

    async def remove(self, user_id: str, memory_id: str) -> bool:
        """Remove a specific entry."""
        async with self._lock:
            if user_id not in self._store:
                return False
            initial_len = len(self._store[user_id])
            self._store[user_id] = [e for e in self._store[user_id] if e.id != memory_id]
            return len(self._store[user_id]) < initial_len

    async def count(self, user_id: str) -> int:
        """Get the number of entries for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            return len(self._store[user_id])

    async def clear(self, user_id: str) -> int:
        """Clear all long-term memory for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            count = len(self._store[user_id])
            self._store[user_id].clear()
            return count
