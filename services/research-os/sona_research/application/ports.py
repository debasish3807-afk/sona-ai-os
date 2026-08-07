"""Abstract port interfaces for the Research OS service.

Defines the contracts that infrastructure adapters must implement
to provide web search, content extraction, and summarization capabilities.
"""

from abc import ABC, abstractmethod

from sona_research.domain.models import ResearchReport, SearchResult


class WebSearchPort(ABC):
    """Port for web search operations.

    Infrastructure adapters implement this port to provide web search
    capabilities using various search engines or APIs (e.g., Google, Bing,
    DuckDuckGo, Brave Search).
    """

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Perform a general web search.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return.

        Returns:
            A list of SearchResult instances ranked by relevance.
        """
        ...

    @abstractmethod
    async def search_news(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Perform a news-focused web search.

        Args:
            query: The search query string.
            max_results: Maximum number of news results to return.

        Returns:
            A list of SearchResult instances from news sources.
        """
        ...


class ContentExtractorPort(ABC):
    """Port for extracting content from web pages.

    Infrastructure adapters implement this port to provide content
    extraction from URLs, handling various page formats and rendering
    requirements.
    """

    @abstractmethod
    async def extract(self, url: str) -> str:
        """Extract the main text content from a web page.

        Args:
            url: The URL of the page to extract content from.

        Returns:
            The extracted text content of the page.
        """
        ...

    @abstractmethod
    async def extract_batch(self, urls: list[str]) -> list[str]:
        """Extract content from multiple web pages concurrently.

        Args:
            urls: A list of URLs to extract content from.

        Returns:
            A list of extracted text contents, in the same order as the input URLs.
        """
        ...


class SummarizationPort(ABC):
    """Port for content summarization and synthesis.

    Infrastructure adapters implement this port to provide text
    summarization and multi-source synthesis capabilities, typically
    backed by an LLM.
    """

    @abstractmethod
    async def summarize(self, content: str, max_length: int = 500) -> str:
        """Summarize a single piece of content.

        Args:
            content: The text content to summarize.
            max_length: Maximum length of the summary in characters.

        Returns:
            A concise summary of the input content.
        """
        ...

    @abstractmethod
    async def synthesize(self, contents: list[str], query: str) -> ResearchReport:
        """Synthesize multiple content sources into a research report.

        Analyzes and combines information from multiple sources to produce
        a comprehensive research report with key findings and confidence scoring.

        Args:
            contents: A list of text contents from different sources.
            query: The original research query to guide synthesis.

        Returns:
            A ResearchReport with summary, sources, confidence, and key findings.
        """
        ...
