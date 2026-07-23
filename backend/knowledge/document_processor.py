"""Document processing for the knowledge system."""

from __future__ import annotations

import re

from config.logging import get_logger
from knowledge.chunking import ChunkingEngine
from knowledge.schemas import Document, DocumentType

logger = get_logger(__name__)


class DocumentProcessor:
    """Processes documents of various types into the knowledge format."""

    def __init__(self, chunking: ChunkingEngine | None = None) -> None:
        self._chunking = chunking or ChunkingEngine()
        self._stats: dict = {"documents_processed": 0, "by_type": {}}

    def process_text(self, title: str, content: str, source: str = "") -> Document:
        """Process plain text into a Document."""
        doc = Document(
            title=title,
            content=content,
            doc_type=DocumentType.TXT,
            source=source,
        )
        doc.chunks = self._chunking.chunk_text(content)  # type: ignore
        self._record_stat("txt")
        logger.info("processed_text_document", title=title)
        return doc

    def process_markdown(self, title: str, content: str, source: str = "") -> Document:
        """Process markdown content into a Document."""
        doc = Document(
            title=title,
            content=content,
            doc_type=DocumentType.MARKDOWN,
            source=source,
        )
        doc.chunks = self._chunking.chunk_markdown(content)  # type: ignore
        self._record_stat("markdown")
        logger.info("processed_markdown_document", title=title)
        return doc

    def process_html(self, title: str, content: str, source: str = "") -> Document:
        """Process HTML content, stripping tags via regex."""
        text = self._strip_html(content)
        doc = Document(
            title=title,
            content=text,
            doc_type=DocumentType.HTML,  # type: ignore
            source=source,
        )
        doc.chunks = self._chunking.chunk_text(text)  # type: ignore
        self._record_stat("html")
        logger.info("processed_html_document", title=title)
        return doc

    def process_url(self, url: str, title: str = "") -> Document:
        """Create a placeholder Document for a URL (content fetched later)."""
        doc = Document(
            title=title or url,
            content=url,
            doc_type=DocumentType.URL,  # type: ignore
            source=url,
        )
        self._record_stat("url")
        logger.info("processed_url_document", url=url)
        return doc

    def get_stats(self) -> dict:
        """Return processing statistics."""
        return dict(self._stats)

    def _strip_html(self, html: str) -> str:
        """Remove HTML tags using regex."""
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _record_stat(self, doc_type: str) -> None:
        """Record a processing stat."""
        self._stats["documents_processed"] += 1
        self._stats["by_type"][doc_type] = self._stats["by_type"].get(doc_type, 0) + 1
