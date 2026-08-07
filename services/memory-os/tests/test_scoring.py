"""Unit tests for Memory OS relevance scoring models."""

from dataclasses import FrozenInstanceError

import pytest

from sona_memory.domain.scoring import RelevanceScore


class TestRelevanceScore:
    """Tests for the RelevanceScore dataclass."""

    def test_creation_with_defaults(self) -> None:
        score = RelevanceScore(memory_id="mem-1")
        assert score.memory_id == "mem-1"
        assert score.similarity == 0.0
        assert score.recency == 0.0
        assert score.importance == 0.0
        assert score.access_frequency == 0.0
        assert score.combined == 0.0

    def test_creation_with_all_values(self) -> None:
        score = RelevanceScore(
            memory_id="mem-2",
            similarity=0.8,
            recency=0.6,
            importance=0.9,
            access_frequency=0.3,
            combined=0.72,
        )
        assert score.memory_id == "mem-2"
        assert score.similarity == 0.8
        assert score.recency == 0.6
        assert score.importance == 0.9
        assert score.access_frequency == 0.3
        assert score.combined == 0.72

    def test_is_frozen(self) -> None:
        score = RelevanceScore(memory_id="mem-3", combined=0.5)
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            score.combined = 0.9  # type: ignore[misc]

    def test_scores_in_valid_range(self) -> None:
        score = RelevanceScore(
            memory_id="mem-4",
            similarity=0.0,
            recency=1.0,
            importance=0.5,
            access_frequency=0.0,
            combined=0.5,
        )
        assert 0.0 <= score.similarity <= 1.0
        assert 0.0 <= score.recency <= 1.0
        assert 0.0 <= score.importance <= 1.0
        assert 0.0 <= score.access_frequency <= 1.0
        assert 0.0 <= score.combined <= 1.0

    def test_multiple_scores_can_be_sorted(self) -> None:
        scores = [
            RelevanceScore(memory_id="a", combined=0.3),
            RelevanceScore(memory_id="b", combined=0.9),
            RelevanceScore(memory_id="c", combined=0.6),
        ]
        sorted_scores = sorted(scores, key=lambda s: s.combined, reverse=True)
        assert sorted_scores[0].memory_id == "b"
        assert sorted_scores[1].memory_id == "c"
        assert sorted_scores[2].memory_id == "a"

    def test_equality(self) -> None:
        s1 = RelevanceScore(memory_id="x", combined=0.5)
        s2 = RelevanceScore(memory_id="x", combined=0.5)
        assert s1 == s2

    def test_inequality(self) -> None:
        s1 = RelevanceScore(memory_id="x", combined=0.5)
        s2 = RelevanceScore(memory_id="x", combined=0.6)
        assert s1 != s2

    def test_zero_combined_score(self) -> None:
        score = RelevanceScore(
            memory_id="zero",
            similarity=0.0,
            recency=0.0,
            importance=0.0,
            access_frequency=0.0,
            combined=0.0,
        )
        assert score.combined == 0.0

    def test_max_combined_score(self) -> None:
        score = RelevanceScore(
            memory_id="max",
            similarity=1.0,
            recency=1.0,
            importance=1.0,
            access_frequency=1.0,
            combined=1.0,
        )
        assert score.combined == 1.0

    def test_partial_scores(self) -> None:
        score = RelevanceScore(
            memory_id="partial",
            similarity=0.9,
            recency=0.0,
            importance=0.8,
            access_frequency=0.0,
            combined=0.45,
        )
        assert score.similarity == 0.9
        assert score.recency == 0.0

    def test_memory_id_required(self) -> None:
        score = RelevanceScore(memory_id="required")
        assert score.memory_id == "required"

    def test_score_with_high_similarity_low_others(self) -> None:
        score = RelevanceScore(
            memory_id="sim-high",
            similarity=0.95,
            recency=0.1,
            importance=0.2,
            access_frequency=0.05,
            combined=0.5,
        )
        assert score.similarity > score.recency
        assert score.similarity > score.importance

    def test_score_comparison_by_combined(self) -> None:
        better = RelevanceScore(memory_id="a", combined=0.8)
        worse = RelevanceScore(memory_id="b", combined=0.3)
        assert better.combined > worse.combined
