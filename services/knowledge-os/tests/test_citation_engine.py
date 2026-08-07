"""Tests for the citation engine."""

import pytest

from sona_knowledge.infrastructure.citation_engine import CitationEngine
from sona_knowledge.infrastructure.hybrid_search import HybridResult


@pytest.fixture
def engine() -> CitationEngine:
    return CitationEngine(excerpt_length=100)


def _make_result(
    id_: str,
    content: str,
    score: float = 0.8,
    doc_id: str = "doc-1",
    title: str = "Test Doc",
) -> HybridResult:
    return HybridResult(
        id=id_,
        content=content,
        semantic_score=score,
        keyword_score=0.5,
        combined_score=score,
        metadata={
            "document_id": doc_id,
            "title": title,
            "source_url": "https://example.com",
            "section": "Introduction",
        },
    )


class TestCitationEngine:
    """Tests for CitationEngine."""

    def test_generate_empty_results(self, engine: CitationEngine) -> None:
        citations = engine.generate_citations([])
        assert citations == []

    def test_generate_single_citation(self, engine: CitationEngine) -> None:
        results = [_make_result("chunk-1", "This is the content.")]
        citations = engine.generate_citations(results)
        assert len(citations) == 1
        assert citations[0].chunk_id == "chunk-1"
        assert citations[0].document_id == "doc-1"
        assert citations[0].document_title == "Test Doc"

    def test_citation_has_content_excerpt(self, engine: CitationEngine) -> None:
        results = [_make_result("chunk-1", "Short content")]
        citations = engine.generate_citations(results)
        assert citations[0].content_excerpt == "Short content"

    def test_excerpt_truncated_for_long_content(self, engine: CitationEngine) -> None:
        long_content = "word " * 100  # 500 chars
        results = [_make_result("chunk-1", long_content)]
        citations = engine.generate_citations(results)
        assert len(citations[0].content_excerpt) <= 104  # 100 + "..."

    def test_citation_relevance_score(self, engine: CitationEngine) -> None:
        results = [_make_result("chunk-1", "content", score=0.92)]
        citations = engine.generate_citations(results)
        assert citations[0].relevance_score == 0.92

    def test_citation_source_url(self, engine: CitationEngine) -> None:
        results = [_make_result("chunk-1", "content")]
        citations = engine.generate_citations(results)
        assert citations[0].source_url == "https://example.com"

    def test_citation_section(self, engine: CitationEngine) -> None:
        results = [_make_result("chunk-1", "content")]
        citations = engine.generate_citations(results)
        assert citations[0].section == "Introduction"

    def test_multiple_citations(self, engine: CitationEngine) -> None:
        results = [
            _make_result("chunk-1", "First content", doc_id="doc-1"),
            _make_result("chunk-2", "Second content", doc_id="doc-2"),
            _make_result("chunk-3", "Third content", doc_id="doc-3"),
        ]
        citations = engine.generate_citations(results)
        assert len(citations) == 3

    def test_format_context_empty(self, engine: CitationEngine) -> None:
        context = engine.format_context([])
        assert context == ""

    def test_format_context_single(self, engine: CitationEngine) -> None:
        results = [_make_result("chunk-1", "Hello world content", title="My Doc")]
        context = engine.format_context(results)
        assert "[Source 1: My Doc]" in context
        assert "Hello world content" in context

    def test_format_context_multiple(self, engine: CitationEngine) -> None:
        results = [
            _make_result("chunk-1", "Content A", title="Doc A"),
            _make_result("chunk-2", "Content B", title="Doc B"),
        ]
        context = engine.format_context(results)
        assert "[Source 1: Doc A]" in context
        assert "[Source 2: Doc B]" in context
        assert "---" in context  # separator

    def test_format_context_preserves_content(self, engine: CitationEngine) -> None:
        results = [_make_result("chunk-1", "Important information about Python")]
        context = engine.format_context(results)
        assert "Important information about Python" in context

    def test_custom_excerpt_length(self) -> None:
        engine = CitationEngine(excerpt_length=20)
        long_content = "A very long piece of content that exceeds twenty characters easily"
        results = [_make_result("chunk-1", long_content)]
        citations = engine.generate_citations(results)
        assert len(citations[0].content_excerpt) <= 24  # 20 + "..."
