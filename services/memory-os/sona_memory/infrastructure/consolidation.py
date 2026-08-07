"""Memory consolidation service.

Promotes important short-term memories to long-term storage,
merges similar memories for deduplication, and computes
importance scores.
"""

import asyncio

import structlog

from sona_memory.domain.models import MemoryEntry
from sona_memory.infrastructure.embedding_service import EmbeddingService, cosine_similarity
from sona_memory.infrastructure.long_term_memory import LongTermMemory
from sona_memory.infrastructure.short_term_memory import ShortTermMemory

logger = structlog.get_logger()


class ConsolidationConfig:
    """Configuration for memory consolidation."""

    def __init__(
        self,
        promotion_threshold: float = 0.7,
        merge_similarity_threshold: float = 0.9,
        min_age_seconds: float = 300,  # 5 minutes minimum age
    ) -> None:
        self.promotion_threshold = promotion_threshold
        self.merge_similarity_threshold = merge_similarity_threshold
        self.min_age_seconds = min_age_seconds


class ConsolidationService:
    """Handles memory consolidation from short-term to long-term.

    Promotes important memories, merges similar ones for deduplication,
    and can run periodically or on-demand.
    """

    def __init__(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        embedding_service: EmbeddingService,
        config: ConsolidationConfig | None = None,
    ) -> None:
        self._short_term = short_term
        self._long_term = long_term
        self._embedding = embedding_service
        self._config = config or ConsolidationConfig()
        self._lock = asyncio.Lock()

    @property
    def config(self) -> ConsolidationConfig:
        """Current consolidation configuration."""
        return self._config

    async def consolidate(self, user_id: str) -> int:
        """Run consolidation for a user.

        1. Gets consolidation candidates from short-term memory.
        2. Deduplicates against existing long-term memories.
        3. Promotes unique important memories to long-term.
        4. Removes promoted entries from short-term.

        Returns the number of memories consolidated.
        """
        async with self._lock:
            # Get candidates from short-term
            candidates = await self._short_term.get_consolidation_candidates(user_id)

            if not candidates:
                return 0

            # Get existing long-term memories for dedup
            existing_lt = await self._long_term.get_all(user_id)

            promoted_ids: set[str] = set()
            merged_ids: set[str] = set()

            for candidate in candidates:
                # Check for duplicates in long-term
                is_dup = await self._is_duplicate_of_existing(candidate, existing_lt)

                if is_dup:
                    merged_ids.add(candidate.id)
                    logger.debug(
                        "memory_merged",
                        user_id=user_id,
                        memory_id=candidate.id,
                    )
                else:
                    # Promote to long-term
                    await self._long_term.store(user_id, candidate)
                    promoted_ids.add(candidate.id)
                    logger.info(
                        "memory_promoted",
                        user_id=user_id,
                        memory_id=candidate.id,
                        importance=candidate.importance,
                    )

            # Remove promoted and merged entries from short-term
            all_processed = promoted_ids | merged_ids
            if all_processed:
                await self._short_term.remove_batch(user_id, all_processed)

            return len(promoted_ids)

    async def compute_importance(self, entry: MemoryEntry) -> float:
        """Compute importance score for a memory entry.

        Combines content length, existing importance, and metadata signals.
        """
        base_importance = entry.importance

        # Boost for longer content (more detailed memories)
        content_length = len(entry.content)
        length_boost = min(content_length / 500, 0.2)

        # Boost for entries with tags
        tag_boost = min(len(entry.tags) * 0.05, 0.15)

        # Boost for entries with metadata
        metadata_boost = 0.05 if entry.metadata else 0.0

        importance = base_importance + length_boost + tag_boost + metadata_boost
        return min(importance, 1.0)

    async def merge_similar(self, user_id: str) -> int:
        """Find and merge similar entries within long-term memory.

        Returns the number of entries merged (removed as duplicates).
        """
        async with self._lock:
            entries = await self._long_term.get_all(user_id)
            if len(entries) < 2:
                return 0

            # Ensure all entries have embeddings
            entries_with_embeddings: list[MemoryEntry] = []
            for entry in entries:
                if entry.embedding is not None:
                    entries_with_embeddings.append(entry)

            # Find duplicate pairs
            to_remove: set[str] = set()
            for i, entry_a in enumerate(entries_with_embeddings):
                if entry_a.id in to_remove:
                    continue
                for entry_b in entries_with_embeddings[i + 1 :]:
                    if entry_b.id in to_remove:
                        continue
                    if entry_a.embedding and entry_b.embedding:
                        sim = cosine_similarity(entry_a.embedding, entry_b.embedding)
                        if sim >= self._config.merge_similarity_threshold:
                            # Keep the more important one
                            if entry_a.importance >= entry_b.importance:
                                to_remove.add(entry_b.id)
                            else:
                                to_remove.add(entry_a.id)
                                break  # entry_a is being removed

            # Remove duplicates
            for memory_id in to_remove:
                await self._long_term.remove(user_id, memory_id)

            return len(to_remove)

    async def _is_duplicate_of_existing(
        self, candidate: MemoryEntry, existing: list[MemoryEntry]
    ) -> bool:
        """Check if candidate is a duplicate of an existing long-term memory."""
        if not existing:
            return False

        # Get embedding for candidate
        if candidate.embedding is None:
            candidate_embedding = await self._embedding.embed(candidate.content)
        else:
            candidate_embedding = candidate.embedding

        for entry in existing:
            if entry.embedding is not None:
                sim = cosine_similarity(candidate_embedding, entry.embedding)
                if sim >= self._config.merge_similarity_threshold:
                    return True

        return False
