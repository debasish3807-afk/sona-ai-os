"""Semantic memory manager.

Stores factual knowledge with embedding-based retrieval.
No temporal decay — knowledge persists permanently with
high importance by default.
"""

import asyncio
from dataclasses import dataclass, replace

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.embedding_service import EmbeddingService, cosine_similarity


@dataclass
class SemanticConfig:
    """Configuration for semantic memory."""

    default_importance: float = 0.8
    similarity_threshold: float = 0.3
    default_top_k: int = 10
    dedup_threshold: float = 0.95  # above this, consider duplicate


class SemanticMemory:
    """Factual knowledge store with embedding-based retrieval.

    Stores semantic knowledge that never expires. High importance
    by default. Supports deduplication of similar facts.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        config: SemanticConfig | None = None,
    ) -> None:
        self._embedding = embedding_service
        self._config = config or SemanticConfig()
        # user_id -> list of entries
        self._store: dict[str, list[MemoryEntry]] = {}
        self._lock = asyncio.Lock()

    @property
    def config(self) -> SemanticConfig:
        """Current configuration."""
        return self._config

    async def store(self, user_id: str, entry: MemoryEntry) -> str:
        """Store a semantic memory entry.

        Generates embedding if not provided. Sets high default importance.
        Checks for duplicates before storing.
        """
        # Ensure memory type and importance
        if entry.memory_type != MemoryType.SEMANTIC:
            entry = replace(entry, memory_type=MemoryType.SEMANTIC)
        if entry.importance == 0.5:
            entry = replace(entry, importance=self._config.default_importance)

        # Generate embedding if missing
        if entry.embedding is None:
            embedding = await self._embedding.embed(entry.content)
            entry = replace(entry, embedding=embedding)

        async with self._lock:
            if user_id not in self._store:
                self._store[user_id] = []

            # Check for duplicates
            if entry.embedding is not None and not self._is_duplicate(user_id, entry.embedding):
                self._store[user_id].append(entry)

            elif entry.embedding is not None and self._is_duplicate(user_id, entry.embedding):
                # Update existing duplicate with newer content if more important
                self._update_duplicate(user_id, entry)

            return entry.id

    async def search(
        self,
        user_id: str,
        query_text: str,
        top_k: int | None = None,
        min_importance: float = 0.0,
    ) -> list[tuple[MemoryEntry, float]]:
        """Search semantic memory using embedding similarity.

        Returns entries with similarity scores sorted descending.
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
        """Get a specific semantic memory by ID."""
        async with self._lock:
            if user_id not in self._store:
                return None
            for entry in self._store[user_id]:
                if entry.id == memory_id:
                    return entry
            return None

    async def get_all(self, user_id: str) -> list[MemoryEntry]:
        """Get all semantic memories for a user."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return list(self._store[user_id])

    async def get_by_tags(self, user_id: str, tags: set[str]) -> list[MemoryEntry]:
        """Get semantic memories matching any of the given tags."""
        async with self._lock:
            if user_id not in self._store:
                return []
            return [entry for entry in self._store[user_id] if set(entry.tags) & tags]

    async def remove(self, user_id: str, memory_id: str) -> bool:
        """Remove a specific semantic memory."""
        async with self._lock:
            if user_id not in self._store:
                return False
            initial_len = len(self._store[user_id])
            self._store[user_id] = [e for e in self._store[user_id] if e.id != memory_id]
            return len(self._store[user_id]) < initial_len

    async def count(self, user_id: str) -> int:
        """Get the number of semantic memories for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            return len(self._store[user_id])

    async def clear(self, user_id: str) -> int:
        """Clear all semantic memory for a user."""
        async with self._lock:
            if user_id not in self._store:
                return 0
            count = len(self._store[user_id])
            self._store[user_id].clear()
            return count

    def _is_duplicate(self, user_id: str, embedding: list[float]) -> bool:
        """Check if a very similar entry already exists. Must hold lock."""
        if user_id not in self._store:
            return False
        for existing in self._store[user_id]:
            if existing.embedding is not None:
                sim = cosine_similarity(embedding, existing.embedding)
                if sim >= self._config.dedup_threshold:
                    return True
        return False

    def _update_duplicate(self, user_id: str, entry: MemoryEntry) -> None:
        """Update existing duplicate if new entry is more important. Must hold lock."""
        if user_id not in self._store or entry.embedding is None:
            return
        for i, existing in enumerate(self._store[user_id]):
            if existing.embedding is not None:
                sim = cosine_similarity(entry.embedding, existing.embedding)
                if sim >= self._config.dedup_threshold:
                    if entry.importance > existing.importance:
                        self._store[user_id][i] = entry
                    return
