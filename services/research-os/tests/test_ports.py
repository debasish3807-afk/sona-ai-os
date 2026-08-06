"""Unit tests for Research OS abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest

from application.ports import ContentExtractorPort, SummarizationPort, WebSearchPort
from domain.models import ResearchReport, SearchResult


class TestWebSearchPort:
    """Tests for the WebSearchPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify WebSearchPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            WebSearchPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = WebSearchPort.__abstractmethods__
        assert "search" in abstract_methods
        assert "search_news" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteSearch(WebSearchPort):
            async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
                return []

            async def search_news(self, query: str, max_results: int = 5) -> list[SearchResult]:
                return []

        search = ConcreteSearch()
        assert isinstance(search, WebSearchPort)

    @pytest.mark.asyncio
    async def test_search_returns_list_of_results(self) -> None:
        """Test that a concrete search() returns a list of SearchResult."""

        class MockSearch(WebSearchPort):
            async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
                return [
                    SearchResult(
                        title=f"Result for: {query}",
                        url="https://example.com/1",
                        snippet="A relevant snippet.",
                        relevance_score=0.9,
                        source_domain="example.com",
                    )
                ]

            async def search_news(self, query: str, max_results: int = 5) -> list[SearchResult]:
                return []

        search = MockSearch()
        results = await search.search("quantum computing")
        assert len(results) == 1
        assert results[0].title == "Result for: quantum computing"
        assert isinstance(results[0], SearchResult)

    @pytest.mark.asyncio
    async def test_search_news_returns_list_of_results(self) -> None:
        """Test that a concrete search_news() returns news results."""

        class MockSearch(WebSearchPort):
            async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
                return []

            async def search_news(self, query: str, max_results: int = 5) -> list[SearchResult]:
                return [
                    SearchResult(
                        title="Breaking News",
                        url="https://news.example.com/article",
                        snippet="Latest developments in AI.",
                        relevance_score=0.85,
                        source_domain="news.example.com",
                    )
                ]

        search = MockSearch()
        results = await search.search_news("AI developments")
        assert len(results) == 1
        assert results[0].source_domain == "news.example.com"


class TestContentExtractorPort:
    """Tests for the ContentExtractorPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify ContentExtractorPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ContentExtractorPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = ContentExtractorPort.__abstractmethods__
        assert "extract" in abstract_methods
        assert "extract_batch" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteExtractor(ContentExtractorPort):
            async def extract(self, url: str) -> str:
                return "Extracted content"

            async def extract_batch(self, urls: list[str]) -> list[str]:
                return ["content"] * len(urls)

        extractor = ConcreteExtractor()
        assert isinstance(extractor, ContentExtractorPort)

    @pytest.mark.asyncio
    async def test_extract_returns_string(self) -> None:
        """Test that a concrete extract() returns text content."""

        class MockExtractor(ContentExtractorPort):
            async def extract(self, url: str) -> str:
                return f"Content from {url}"

            async def extract_batch(self, urls: list[str]) -> list[str]:
                return [f"Content from {url}" for url in urls]

        extractor = MockExtractor()
        content = await extractor.extract("https://example.com")
        assert content == "Content from https://example.com"
        assert isinstance(content, str)

    @pytest.mark.asyncio
    async def test_extract_batch_returns_list(self) -> None:
        """Test that extract_batch() returns content for each URL."""

        class MockExtractor(ContentExtractorPort):
            async def extract(self, url: str) -> str:
                return f"Content from {url}"

            async def extract_batch(self, urls: list[str]) -> list[str]:
                return [f"Content from {url}" for url in urls]

        extractor = MockExtractor()
        urls = ["https://a.com", "https://b.com", "https://c.com"]
        results = await extractor.extract_batch(urls)
        assert len(results) == 3
        assert results[0] == "Content from https://a.com"


class TestSummarizationPort:
    """Tests for the SummarizationPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify SummarizationPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SummarizationPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = SummarizationPort.__abstractmethods__
        assert "summarize" in abstract_methods
        assert "synthesize" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteSummarizer(SummarizationPort):
            async def summarize(self, content: str, max_length: int = 500) -> str:
                return "Summary"

            async def synthesize(self, contents: list[str], query: str) -> ResearchReport:
                return ResearchReport(
                    query=query,
                    summary="Synthesized",
                    sources=[],
                    confidence=0.8,
                    key_findings=[],
                )

        summarizer = ConcreteSummarizer()
        assert isinstance(summarizer, SummarizationPort)

    @pytest.mark.asyncio
    async def test_summarize_returns_string(self) -> None:
        """Test that a concrete summarize() returns a summary string."""

        class MockSummarizer(SummarizationPort):
            async def summarize(self, content: str, max_length: int = 500) -> str:
                return content[:max_length]

            async def synthesize(self, contents: list[str], query: str) -> ResearchReport:
                return ResearchReport(
                    query=query,
                    summary="synthesized",
                    sources=[],
                    confidence=0.7,
                    key_findings=[],
                )

        summarizer = MockSummarizer()
        result = await summarizer.summarize("A long document about AI " * 100, max_length=50)
        assert len(result) <= 50
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_synthesize_returns_research_report(self) -> None:
        """Test that synthesize() returns a ResearchReport."""

        class MockSummarizer(SummarizationPort):
            async def summarize(self, content: str, max_length: int = 500) -> str:
                return "summary"

            async def synthesize(self, contents: list[str], query: str) -> ResearchReport:
                return ResearchReport(
                    query=query,
                    summary="Multi-source synthesis about AI.",
                    sources=[],
                    confidence=0.88,
                    key_findings=["Finding 1", "Finding 2"],
                )

        summarizer = MockSummarizer()
        report = await summarizer.synthesize(
            contents=["Source 1 text", "Source 2 text"],
            query="What is AI?",
        )
        assert isinstance(report, ResearchReport)
        assert report.query == "What is AI?"
        assert report.confidence == 0.88
        assert len(report.key_findings) == 2
