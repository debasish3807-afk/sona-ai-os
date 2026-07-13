"""URL reading and content extraction."""

from __future__ import annotations

import re
import time

from config.logging import get_logger
from web.schemas import WebPage

logger = get_logger(__name__)


class URLReader:
    """Reads and extracts content from URLs."""

    def __init__(self, timeout: float = 30.0, max_size_mb: int = 10) -> None:
        self._timeout = timeout
        self._max_size_mb = max_size_mb
        self._stats: dict = {"reads": 0, "errors": 0}

    async def read(self, url: str) -> WebPage:
        """Read content from a URL.

        Currently a placeholder that stores the URL as content.
        Will be connected to httpx for actual fetching.
        """
        self._stats["reads"] += 1
        logger.info("url_read", url=url)

        return WebPage(
            url=url,
            title=self._extract_title_from_url(url),
            content=f"Content from: {url}",
            status_code=200,
            fetched_at=time.time(),
        )

    async def read_batch(self, urls: list[str]) -> list[WebPage]:
        """Read content from multiple URLs."""
        pages: list[WebPage] = []
        for url in urls:
            page = await self.read(url)
            pages.append(page)
        return pages

    def extract_text(self, html: str) -> str:
        """Strip HTML tags and extract readable text."""
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from a URL."""
        path = url.rstrip("/").split("/")[-1]
        path = path.split("?")[0]
        path = path.replace("-", " ").replace("_", " ")
        return path or url
