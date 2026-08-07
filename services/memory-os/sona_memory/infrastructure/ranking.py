"""Memory ranking module.

Multi-signal ranking combining similarity, recency, importance,
and access frequency to produce final relevance scores.
"""

import time
from dataclasses import dataclass

from sona_memory.domain.models import MemoryEntry
from sona_memory.domain.scoring import RelevanceScore
from sona_memory.infrastructure.embedding_service import cosine_similarity


@dataclass
class RankingWeights:
    """Configurable weights for ranking signals.

    All weights should be non-negative. They are normalized internally.
    """

    similarity: float = 0.4
    recency: float = 0.25
    importance: float = 0.25
    access_frequency: float = 0.1


class MemoryRanker:
    """Ranks memory entries using multiple signals.

    Combines vector similarity, recency decay, importance, and
    access frequency with configurable weights.
    """

    def __init__(self, weights: RankingWeights | None = None) -> None:
        self._weights = weights or RankingWeights()

    @property
    def weights(self) -> RankingWeights:
        """Current ranking weights."""
        return self._weights

    def rank(
        self,
        entries: list[MemoryEntry],
        query_embedding: list[float] | None = None,
        access_counts: dict[str, int] | None = None,
        max_access_count: int = 100,
    ) -> list[RelevanceScore]:
        """Rank memory entries and return sorted relevance scores.

        Args:
            entries: Memory entries to rank.
            query_embedding: Optional query embedding for similarity.
            access_counts: Dict of memory_id -> access count.
            max_access_count: Max expected access count for normalization.

        Returns:
            List of RelevanceScore sorted by combined score (descending).
        """
        if not entries:
            return []

        scores: list[RelevanceScore] = []
        now = time.time()
        access_counts = access_counts or {}

        for entry in entries:
            similarity = self._compute_similarity(entry, query_embedding)
            recency = self._compute_recency(entry, now)
            importance = entry.importance
            frequency = self._compute_frequency(entry.id, access_counts, max_access_count)
            combined = self._compute_combined(similarity, recency, importance, frequency)

            scores.append(
                RelevanceScore(
                    memory_id=entry.id,
                    similarity=similarity,
                    recency=recency,
                    importance=importance,
                    access_frequency=frequency,
                    combined=combined,
                )
            )

        scores.sort(key=lambda s: s.combined, reverse=True)
        return scores

    def _compute_similarity(self, entry: MemoryEntry, query_embedding: list[float] | None) -> float:
        """Compute similarity score between query and entry embeddings."""
        if query_embedding is None or entry.embedding is None:
            return 0.0
        sim = cosine_similarity(query_embedding, entry.embedding)
        # Normalize from [-1, 1] to [0, 1]
        return (sim + 1.0) / 2.0

    def _compute_recency(self, entry: MemoryEntry, now: float) -> float:
        """Compute recency score using exponential time decay.

        Decay half-life is 24 hours.
        """
        if entry.created_at is None:
            return 0.5  # neutral if no timestamp

        entry_time = entry.created_at.timestamp()
        age_hours = (now - entry_time) / 3600.0

        if age_hours < 0:
            return 1.0

        # Exponential decay with 24-hour half-life
        half_life = 24.0
        return 2.0 ** (-age_hours / half_life)

    def _compute_frequency(
        self, memory_id: str, access_counts: dict[str, int], max_count: int
    ) -> float:
        """Compute normalized access frequency score."""
        count = access_counts.get(memory_id, 0)
        if max_count <= 0:
            return 0.0
        return min(count / max_count, 1.0)

    def _compute_combined(
        self,
        similarity: float,
        recency: float,
        importance: float,
        frequency: float,
    ) -> float:
        """Compute weighted combined score."""
        w = self._weights
        total_weight = w.similarity + w.recency + w.importance + w.access_frequency
        if total_weight == 0:
            return 0.0

        raw = (
            w.similarity * similarity
            + w.recency * recency
            + w.importance * importance
            + w.access_frequency * frequency
        )
        return raw / total_weight
