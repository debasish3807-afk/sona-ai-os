"""Unit tests for Research OS domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest
from sona_research.domain.models import (
    ResearchQuery,
    ResearchReport,
    ResearchType,
    SearchResult,
)


class TestResearchType:
    """Tests for the ResearchType enum."""

    def test_all_types_defined(self) -> None:
        """Verify all expected research types are available."""
        assert ResearchType.WEB_SEARCH == "web_search"
        assert ResearchType.DEEP_RESEARCH == "deep_research"
        assert ResearchType.FACT_CHECK == "fact_check"
        assert ResearchType.SUMMARIZATION == "summarization"

    def test_type_count(self) -> None:
        """Verify exactly 4 research types exist."""
        assert len(ResearchType) == 4

    def test_type_is_str_enum(self) -> None:
        """Verify research types are usable as strings."""
        assert str(ResearchType.WEB_SEARCH) == "web_search"
        assert str(ResearchType.DEEP_RESEARCH) == "deep_research"


class TestResearchQuery:
    """Tests for the ResearchQuery frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        query = ResearchQuery(
            query="What is quantum computing?",
            research_type=ResearchType.WEB_SEARCH,
        )
        assert query.query == "What is quantum computing?"
        assert query.research_type == ResearchType.WEB_SEARCH

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        query = ResearchQuery(
            query="test query",
            research_type=ResearchType.DEEP_RESEARCH,
        )
        assert query.max_sources == 10
        assert query.language == "en"
        assert query.context is None

    def test_custom_values(self) -> None:
        """Create with custom values."""
        query = ResearchQuery(
            query="AI safety research",
            research_type=ResearchType.FACT_CHECK,
            max_sources=20,
            language="fr",
            context={"domain": "artificial intelligence"},
        )
        assert query.max_sources == 20
        assert query.language == "fr"
        assert query.context == {"domain": "artificial intelligence"}

    def test_is_frozen(self) -> None:
        """Verify ResearchQuery is immutable."""
        query = ResearchQuery(
            query="test",
            research_type=ResearchType.WEB_SEARCH,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            query.query = "changed"  # type: ignore[misc]


class TestSearchResult:
    """Tests for the SearchResult frozen dataclass."""

    def test_creation(self) -> None:
        """Create a search result with all fields."""
        result = SearchResult(
            title="Quantum Computing Overview",
            url="https://example.com/quantum",
            snippet="Quantum computing uses quantum bits...",
            relevance_score=0.95,
            source_domain="example.com",
        )
        assert result.title == "Quantum Computing Overview"
        assert result.url == "https://example.com/quantum"
        assert result.snippet == "Quantum computing uses quantum bits..."
        assert result.relevance_score == 0.95
        assert result.source_domain == "example.com"

    def test_is_frozen(self) -> None:
        """Verify SearchResult is immutable."""
        result = SearchResult(
            title="Test",
            url="https://test.com",
            snippet="A snippet",
            relevance_score=0.8,
            source_domain="test.com",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            result.title = "Modified"  # type: ignore[misc]

    def test_relevance_score_boundaries(self) -> None:
        """Verify score can hold boundary values."""
        low = SearchResult(
            title="Low",
            url="https://low.com",
            snippet="Low score",
            relevance_score=0.0,
            source_domain="low.com",
        )
        high = SearchResult(
            title="High",
            url="https://high.com",
            snippet="High score",
            relevance_score=1.0,
            source_domain="high.com",
        )
        assert low.relevance_score == 0.0
        assert high.relevance_score == 1.0


class TestResearchReport:
    """Tests for the ResearchReport frozen dataclass."""

    def test_creation(self) -> None:
        """Create a research report with all fields."""
        sources = [
            SearchResult(
                title="Source 1",
                url="https://src1.com",
                snippet="First source",
                relevance_score=0.9,
                source_domain="src1.com",
            ),
            SearchResult(
                title="Source 2",
                url="https://src2.com",
                snippet="Second source",
                relevance_score=0.85,
                source_domain="src2.com",
            ),
        ]
        report = ResearchReport(
            query="What is AI?",
            summary="AI is a branch of computer science...",
            sources=sources,
            confidence=0.92,
            key_findings=["AI mimics human intelligence", "ML is a subset of AI"],
        )
        assert report.query == "What is AI?"
        assert report.summary == "AI is a branch of computer science..."
        assert len(report.sources) == 2
        assert report.confidence == 0.92
        assert len(report.key_findings) == 2

    def test_empty_sources_and_findings(self) -> None:
        """Create a report with empty sources and findings."""
        report = ResearchReport(
            query="obscure topic",
            summary="No relevant information found.",
            sources=[],
            confidence=0.1,
            key_findings=[],
        )
        assert report.sources == []
        assert report.key_findings == []
        assert report.confidence == 0.1

    def test_is_frozen(self) -> None:
        """Verify ResearchReport is immutable."""
        report = ResearchReport(
            query="test",
            summary="summary",
            sources=[],
            confidence=0.5,
            key_findings=[],
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            report.summary = "changed"  # type: ignore[misc]
