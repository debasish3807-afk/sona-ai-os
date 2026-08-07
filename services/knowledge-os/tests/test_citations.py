"""Tests for Knowledge OS citation models."""

from dataclasses import FrozenInstanceError

import pytest

from sona_knowledge.domain.citations import Citation


class TestCitation:
    """Tests for the Citation dataclass."""

    def test_create_minimal(self) -> None:
        citation = Citation(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_title="Test Doc",
            content_excerpt="This is an excerpt...",
            relevance_score=0.85,
        )
        assert citation.chunk_id == "chunk-1"
        assert citation.document_id == "doc-1"
        assert citation.document_title == "Test Doc"
        assert citation.content_excerpt == "This is an excerpt..."
        assert citation.relevance_score == 0.85

    def test_default_optional_fields(self) -> None:
        citation = Citation(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_title="Doc",
            content_excerpt="text",
            relevance_score=0.5,
        )
        assert citation.source_url == ""
        assert citation.page_number is None
        assert citation.section == ""

    def test_with_all_fields(self) -> None:
        citation = Citation(
            chunk_id="chunk-5",
            document_id="doc-3",
            document_title="API Reference",
            content_excerpt="The API endpoint...",
            relevance_score=0.92,
            source_url="https://docs.example.com/api",
            page_number=42,
            section="Authentication",
        )
        assert citation.source_url == "https://docs.example.com/api"
        assert citation.page_number == 42
        assert citation.section == "Authentication"

    def test_is_frozen(self) -> None:
        citation = Citation(
            chunk_id="c1",
            document_id="d1",
            document_title="T",
            content_excerpt="e",
            relevance_score=0.5,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            citation.relevance_score = 0.9  # type: ignore[misc]

    def test_relevance_score_range(self) -> None:
        """Test citation with boundary relevance scores."""
        low = Citation(
            chunk_id="c1",
            document_id="d1",
            document_title="T",
            content_excerpt="e",
            relevance_score=0.0,
        )
        high = Citation(
            chunk_id="c2",
            document_id="d2",
            document_title="T2",
            content_excerpt="e2",
            relevance_score=1.0,
        )
        assert low.relevance_score == 0.0
        assert high.relevance_score == 1.0

    def test_page_number_none_vs_zero(self) -> None:
        """Ensure page_number=0 is different from None."""
        no_page = Citation(
            chunk_id="c1",
            document_id="d1",
            document_title="T",
            content_excerpt="e",
            relevance_score=0.5,
            page_number=None,
        )
        page_zero = Citation(
            chunk_id="c1",
            document_id="d1",
            document_title="T",
            content_excerpt="e",
            relevance_score=0.5,
            page_number=0,
        )
        assert no_page.page_number is None
        assert page_zero.page_number == 0

    def test_empty_source_url(self) -> None:
        citation = Citation(
            chunk_id="c1",
            document_id="d1",
            document_title="T",
            content_excerpt="e",
            relevance_score=0.5,
            source_url="",
        )
        assert citation.source_url == ""

    def test_equality(self) -> None:
        c1 = Citation(
            chunk_id="c1",
            document_id="d1",
            document_title="T",
            content_excerpt="e",
            relevance_score=0.5,
        )
        c2 = Citation(
            chunk_id="c1",
            document_id="d1",
            document_title="T",
            content_excerpt="e",
            relevance_score=0.5,
        )
        assert c1 == c2

    def test_inequality(self) -> None:
        c1 = Citation(
            chunk_id="c1",
            document_id="d1",
            document_title="T",
            content_excerpt="e",
            relevance_score=0.5,
        )
        c2 = Citation(
            chunk_id="c2",
            document_id="d1",
            document_title="T",
            content_excerpt="e",
            relevance_score=0.5,
        )
        assert c1 != c2
