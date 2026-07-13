"""Search engine with caching support."""

from __future__ import annotations

import time

from config.logging import get_logger
from web.schemas import WebResult

logger = get_logger(__name__)


class SearchEngine:
    """Manages search across multiple sources with caching."""

    def __init__(self, cache_ttl: float = 3600.0) -> None:
        self._cache_ttl = cache_ttl
        self._cache: dict[str, tuple[list[WebResult], float]] = {}
        self._stats: dict = {"searches": 0, "cache_hits": 0}

    async def search(self, query: str, max_results: int = 10) -> list[WebResult]:
        """Search for web results.

        Currently returns placeholder results.
        Will be connected to actual search providers.
        """
        self._stats["searches"] += 1

        # Check cache first
        cached = self.get_cached(query)
        if cached is not None:
            self._stats["cache_hits"] += 1
            return cached[:max_results]

        # Placeholder search results
        results = [
            WebResult(
                title=f"Result for: {query}",
                url=f"https://example.com/search?q={query}",
                snippet=f"Search result snippet for '{query}'",
                score=0.9,
                cached_at=time.time(),
            )
        ]

        # Cache results
        self._cache[query.lower()] = (results, time.time())
        logger.info("search_executed", query=query, results=len(results))
        return results[:max_results]

    async def news_search(self, query: str, max_results: int = 5) -> list[WebResult]:
        """Search for news results."""
        results = await self.search(query, max_results=max_results)
        for r in results:
            r.url = r.url.replace("search", "news")
        return results

    def get_cached(self, query: str) -> list[WebResult] | None:
        """Get cached results for a query if still valid."""
        key = query.lower()
        if key not in self._cache:
            return None

        results, cached_at = self._cache[key]
        if time.time() - cached_at > self._cache_ttl:
            del self._cache[key]
            return None

        return results

    def clear_cache(self) -> int:
        """Clear all cached results. Returns count of cleared entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info("cache_cleared", entries=count)
        return count

    def get_stats(self) -> dict:
        """Return search engine statistics."""
        return {
            **self._stats,
            "cache_size": len(self._cache),
            "cache_ttl": self._cache_ttl,
        }
