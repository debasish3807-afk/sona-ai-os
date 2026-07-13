"""High-level web intelligence interface."""

from __future__ import annotations

from config.logging import get_logger
from web.schemas import WebPage, WebResult
from web.search_engine import SearchEngine
from web.url_reader import URLReader

logger = get_logger(__name__)


class WebSearch:
    """High-level web intelligence interface."""

    def __init__(self) -> None:
        self._engine = SearchEngine()
        self._reader = URLReader()

    async def search(self, query: str, max_results: int = 10) -> list[WebResult]:
        """Search the web for results."""
        return await self._engine.search(query, max_results=max_results)

    async def search_news(self, query: str, max_results: int = 5) -> list[WebResult]:
        """Search for news articles."""
        return await self._engine.news_search(query, max_results=max_results)

    async def read_url(self, url: str) -> WebPage:
        """Read and extract content from a URL."""
        return await self._reader.read(url)

    async def search_and_read(self, query: str, top_n: int = 3) -> list[WebPage]:
        """Search then read the top results."""
        results = await self.search(query, max_results=top_n)
        urls = [r.url for r in results]
        return await self._reader.read_batch(urls)

    def generate_citations(self, results: list[WebResult]) -> list[dict]:
        """Generate citation entries from search results."""
        citations: list[dict] = []
        for i, result in enumerate(results):
            citations.append(
                {
                    "index": i + 1,
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "score": result.score,
                }
            )
        return citations

    def get_stats(self) -> dict:
        """Return web search statistics."""
        return {
            "engine": self._engine.get_stats(),
        }
