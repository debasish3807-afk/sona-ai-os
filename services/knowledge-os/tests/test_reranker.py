"""Tests for the reranker module."""

import pytest

from sona_knowledge.infrastructure.hybrid_search import HybridResult
from sona_knowledge.infrastructure.reranker import Reranker


@pytest.fixture
def reranker() -> Reranker:
    return Reranker(exact_match_boost=0.2, diversity_penalty=0.1)


def _make_hybrid_result(id_: str, score: float, content: str, doc_id: str = "") -> HybridResult:
    return HybridResult(
        id=id_,
        content=content,
        semantic_score=score,
        keyword_score=0.5,
        combined_score=score,
        metadata={"document_id": doc_id} if doc_id else {},
    )


class TestReranker:
    """Tests for Reranker."""

    def test_empty_results(self, reranker: Reranker) -> None:
        results = reranker.rerank("query", [])
        assert results == []

    def test_single_result(self, reranker: Reranker) -> None:
        results = reranker.rerank("test", [_make_hybrid_result("id-1", 0.8, "test content")])
        assert len(results) == 1

    def test_exact_match_boosted(self, reranker: Reranker) -> None:
        exact = _make_hybrid_result("id-1", 0.7, "Python programming language")
        no_match = _make_hybrid_result("id-2", 0.7, "Something else entirely different")
        results = reranker.rerank("Python programming language", [exact, no_match])
        assert results[0].id == "id-1"
        assert results[0].combined_score > results[1].combined_score

    def test_partial_phrase_match_boosted(self, reranker: Reranker) -> None:
        partial = _make_hybrid_result("id-1", 0.7, "Python programming language basics")
        no_match = _make_hybrid_result("id-2", 0.7, "No related content here at all")
        results = reranker.rerank("learn Python programming language", [partial, no_match])
        assert results[0].id == "id-1"

    def test_diversity_penalty_same_document(self, reranker: Reranker) -> None:
        r1 = _make_hybrid_result("id-1", 0.8, "First chunk of doc A", doc_id="doc-a")
        r2 = _make_hybrid_result("id-2", 0.79, "Second chunk of doc A", doc_id="doc-a")
        r3 = _make_hybrid_result("id-3", 0.75, "Chunk from doc B", doc_id="doc-b")
        results = reranker.rerank("query", [r1, r2, r3])
        # Second chunk from same doc should be penalized
        doc_a_results = [r for r in results if r.metadata.get("document_id") == "doc-a"]
        assert doc_a_results[0].combined_score > doc_a_results[1].combined_score

    def test_diversity_promotes_variety(self, reranker: Reranker) -> None:
        # 3 chunks from doc-a, 1 from doc-b with slightly lower score
        r1 = _make_hybrid_result("id-1", 0.8, "content", doc_id="doc-a")
        r2 = _make_hybrid_result("id-2", 0.78, "content", doc_id="doc-a")
        r3 = _make_hybrid_result("id-3", 0.77, "content", doc_id="doc-a")
        r4 = _make_hybrid_result("id-4", 0.76, "content", doc_id="doc-b")
        results = reranker.rerank("query", [r1, r2, r3, r4])
        # Doc-b result should move up due to diversity penalty on doc-a repeats
        doc_b_position = next(i for i, r in enumerate(results) if r.id == "id-4")
        assert doc_b_position < 3  # Should not be last

    def test_term_overlap_boost(self, reranker: Reranker) -> None:
        has_terms = _make_hybrid_result("id-1", 0.7, "Python data science machine learning")
        no_terms = _make_hybrid_result("id-2", 0.7, "xyz abc def ghi jkl mno pqr stu")
        results = reranker.rerank("Python machine learning", [has_terms, no_terms])
        assert results[0].id == "id-1"

    def test_scores_non_negative(self, reranker: Reranker) -> None:
        results_in = [
            _make_hybrid_result(f"id-{i}", 0.1, "content", doc_id="same-doc") for i in range(10)
        ]
        results = reranker.rerank("query", results_in)
        for r in results:
            assert r.combined_score >= 0.0

    def test_sorted_by_combined_score(self, reranker: Reranker) -> None:
        results_in = [
            _make_hybrid_result("id-1", 0.5, "a"),
            _make_hybrid_result("id-2", 0.9, "b"),
            _make_hybrid_result("id-3", 0.7, "c"),
        ]
        results = reranker.rerank("query", results_in)
        scores = [r.combined_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_preserves_metadata(self, reranker: Reranker) -> None:
        r = HybridResult(
            id="id-1",
            content="text",
            semantic_score=0.8,
            keyword_score=0.5,
            combined_score=0.7,
            metadata={"key": "value", "document_id": "doc-1"},
        )
        results = reranker.rerank("text", [r])
        assert results[0].metadata["key"] == "value"

    def test_custom_boost_values(self) -> None:
        reranker = Reranker(exact_match_boost=0.5, diversity_penalty=0.0)
        r1 = _make_hybrid_result("id-1", 0.6, "exact match here")
        r2 = _make_hybrid_result("id-2", 0.7, "no match found xyz")
        results = reranker.rerank("exact match here", [r1, r2])
        # High boost should push exact match above
        assert results[0].id == "id-1"
