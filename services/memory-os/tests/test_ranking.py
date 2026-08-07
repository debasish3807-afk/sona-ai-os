"""Unit tests for memory ranking."""

from datetime import UTC, datetime, timedelta

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.embedding_service import _hash_to_embedding
from sona_memory.infrastructure.ranking import MemoryRanker, RankingWeights


def _make_entry(
    id: str,
    content: str = "test",
    importance: float = 0.5,
    created_at: datetime | None = None,
    embedding: list[float] | None = None,
) -> MemoryEntry:
    return MemoryEntry(
        id=id,
        memory_type=MemoryType.LONG_TERM,
        content=content,
        importance=importance,
        created_at=created_at,
        embedding=embedding,
    )


class TestRankingBasic:
    """Tests for basic ranking functionality."""

    def test_empty_entries(self) -> None:
        ranker = MemoryRanker()
        scores = ranker.rank([])
        assert scores == []

    def test_single_entry(self) -> None:
        ranker = MemoryRanker()
        entries = [_make_entry("m1")]
        scores = ranker.rank(entries)
        assert len(scores) == 1
        assert scores[0].memory_id == "m1"

    def test_returns_sorted_by_combined(self) -> None:
        ranker = MemoryRanker()
        entries = [
            _make_entry("low", importance=0.1),
            _make_entry("high", importance=0.9),
        ]
        scores = ranker.rank(entries)
        assert scores[0].memory_id == "high"

    def test_importance_signal(self) -> None:
        ranker = MemoryRanker(
            weights=RankingWeights(similarity=0, recency=0, importance=1.0, access_frequency=0)
        )
        entries = [
            _make_entry("low", importance=0.2),
            _make_entry("high", importance=0.9),
        ]
        scores = ranker.rank(entries)
        assert scores[0].memory_id == "high"
        assert scores[0].importance == 0.9


class TestRankingSimilarity:
    """Tests for similarity-based ranking."""

    def test_similarity_with_embeddings(self) -> None:
        ranker = MemoryRanker(
            weights=RankingWeights(similarity=1.0, recency=0, importance=0, access_frequency=0)
        )
        query_emb = _hash_to_embedding("python programming", 64)
        close_emb = _hash_to_embedding("python programming", 64)  # same = perfect match
        far_emb = _hash_to_embedding("cooking recipes", 64)

        entries = [
            _make_entry("close", embedding=close_emb),
            _make_entry("far", embedding=far_emb),
        ]
        scores = ranker.rank(entries, query_embedding=query_emb)
        assert scores[0].memory_id == "close"
        assert scores[0].similarity > scores[1].similarity

    def test_no_query_embedding(self) -> None:
        ranker = MemoryRanker()
        entries = [_make_entry("m1", embedding=[0.5] * 64)]
        scores = ranker.rank(entries, query_embedding=None)
        assert scores[0].similarity == 0.0

    def test_no_entry_embedding(self) -> None:
        ranker = MemoryRanker()
        entries = [_make_entry("m1")]  # No embedding
        query_emb = [0.5] * 64
        scores = ranker.rank(entries, query_embedding=query_emb)
        assert scores[0].similarity == 0.0


class TestRankingRecency:
    """Tests for recency-based ranking."""

    def test_recency_newer_is_higher(self) -> None:
        ranker = MemoryRanker(
            weights=RankingWeights(similarity=0, recency=1.0, importance=0, access_frequency=0)
        )
        now = datetime.now(UTC)
        entries = [
            _make_entry("old", created_at=now - timedelta(days=7)),
            _make_entry("new", created_at=now - timedelta(minutes=5)),
        ]
        scores = ranker.rank(entries)
        assert scores[0].memory_id == "new"
        assert scores[0].recency > scores[1].recency

    def test_no_created_at_neutral(self) -> None:
        ranker = MemoryRanker()
        entries = [_make_entry("m1")]  # No created_at
        scores = ranker.rank(entries)
        assert scores[0].recency == 0.5  # neutral


class TestRankingFrequency:
    """Tests for access frequency ranking."""

    def test_frequency_signal(self) -> None:
        ranker = MemoryRanker(
            weights=RankingWeights(similarity=0, recency=0, importance=0, access_frequency=1.0)
        )
        entries = [
            _make_entry("rare"),
            _make_entry("frequent"),
        ]
        access_counts = {"rare": 1, "frequent": 50}
        scores = ranker.rank(entries, access_counts=access_counts, max_access_count=100)
        assert scores[0].memory_id == "frequent"
        assert scores[0].access_frequency > scores[1].access_frequency

    def test_zero_max_access_count(self) -> None:
        ranker = MemoryRanker()
        entries = [_make_entry("m1")]
        scores = ranker.rank(entries, max_access_count=0)
        assert scores[0].access_frequency == 0.0


class TestRankingWeights:
    """Tests for configurable weights."""

    def test_custom_weights(self) -> None:
        weights = RankingWeights(similarity=0.5, recency=0.3, importance=0.1, access_frequency=0.1)
        ranker = MemoryRanker(weights=weights)
        assert ranker.weights.similarity == 0.5
        assert ranker.weights.recency == 0.3

    def test_all_zero_weights(self) -> None:
        ranker = MemoryRanker(weights=RankingWeights(0, 0, 0, 0))
        entries = [_make_entry("m1", importance=0.9)]
        scores = ranker.rank(entries)
        assert scores[0].combined == 0.0

    def test_combined_score_normalized(self) -> None:
        ranker = MemoryRanker(
            weights=RankingWeights(similarity=0, recency=0, importance=1.0, access_frequency=0)
        )
        entries = [_make_entry("m1", importance=0.8)]
        scores = ranker.rank(entries)
        # Combined should be importance since that's the only non-zero weight
        assert abs(scores[0].combined - 0.8) < 0.01
