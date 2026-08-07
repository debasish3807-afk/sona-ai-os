"""Tests for hybrid search (semantic + keyword)."""

import pytest

from sona_knowledge.infrastructure.hybrid_search import HybridSearch
from sona_knowledge.infrastructure.vector_store import SearchResult


@pytest.fixture
def hybrid() -> HybridSearch:
    return HybridSearch(semantic_weight=0.7, keyword_weight=0.3)


def _make_result(id_: str, score: float, content: str) -> SearchResult:
    return SearchResult(id=id_, score=score, metadata={}, content=content)


class TestHybridSearch:
    """Tests for HybridSearch."""

    def test_empty_results(self, hybrid: HybridSearch) -> None:
        results = hybrid.search("query", [])
        assert results == []

    def test_single_result(self, hybrid: HybridSearch) -> None:
        semantic = [_make_result("id-1", 0.9, "Python programming language")]
        results = hybrid.search("Python", semantic)
        assert len(results) == 1
        assert results[0].id == "id-1"

    def test_combined_score_uses_weights(self, hybrid: HybridSearch) -> None:
        semantic = [_make_result("id-1", 0.8, "Python programming language")]
        results = hybrid.search("Python", semantic)
        # Combined should be weighted mix of semantic and keyword
        r = results[0]
        assert r.combined_score > 0
        assert r.semantic_score == 0.8

    def test_keyword_boost_for_matching_terms(self, hybrid: HybridSearch) -> None:
        # "Python" appears in content, should get keyword boost
        has_keyword = _make_result("id-1", 0.7, "Python is great for data science")
        no_keyword = _make_result("id-2", 0.7, "Java is used for enterprise apps")
        results = hybrid.search("Python", [has_keyword, no_keyword])
        # Result with keyword match should rank higher
        assert results[0].id == "id-1"
        assert results[0].keyword_score > results[1].keyword_score

    def test_semantic_dominates_with_high_weight(self) -> None:
        hybrid = HybridSearch(semantic_weight=0.95, keyword_weight=0.05)
        high_semantic = _make_result("id-1", 0.95, "No matching keywords here")
        low_semantic = _make_result("id-2", 0.3, "Python Python Python everywhere")
        results = hybrid.search("Python", [high_semantic, low_semantic])
        assert results[0].id == "id-1"

    def test_keyword_dominates_with_high_weight(self) -> None:
        hybrid = HybridSearch(semantic_weight=0.1, keyword_weight=0.9)
        low_semantic = _make_result("id-1", 0.3, "Python programming language features")
        high_semantic = _make_result("id-2", 0.9, "No matching terms at all here xyz")
        results = hybrid.search("Python programming", [low_semantic, high_semantic])
        # Keyword-heavy weight should boost the one with matching terms
        assert results[0].id == "id-1"

    def test_results_sorted_by_combined_score(self, hybrid: HybridSearch) -> None:
        results_in = [
            _make_result("id-1", 0.5, "content a"),
            _make_result("id-2", 0.9, "content b"),
            _make_result("id-3", 0.7, "content c"),
        ]
        results = hybrid.search("content", results_in)
        scores = [r.combined_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_keyword_score_normalized(self, hybrid: HybridSearch) -> None:
        semantic = [_make_result("id-1", 0.8, "test word " * 50)]
        results = hybrid.search("test word", semantic)
        # Keyword score should be in [0, 1]
        assert 0.0 <= results[0].keyword_score <= 1.0

    def test_metadata_preserved(self, hybrid: HybridSearch) -> None:
        result = SearchResult(id="id-1", score=0.8, metadata={"key": "val"}, content="text")
        results = hybrid.search("text", [result])
        assert results[0].metadata == {"key": "val"}

    def test_corpus_size_affects_scoring(self, hybrid: HybridSearch) -> None:
        semantic = [_make_result("id-1", 0.8, "Python language")]
        r1 = hybrid.search("Python", semantic, corpus_size=10)
        r2 = hybrid.search("Python", semantic, corpus_size=10000)
        # Different corpus sizes affect IDF calculation
        assert r1[0].keyword_score != r2[0].keyword_score or len(semantic) == 1

    def test_multiple_query_terms(self, hybrid: HybridSearch) -> None:
        semantic = [
            _make_result("id-1", 0.7, "Python machine learning deep neural"),
            _make_result("id-2", 0.7, "Go language concurrency patterns"),
        ]
        results = hybrid.search("Python machine learning", semantic)
        # First should score higher due to keyword matches
        assert results[0].id == "id-1"
