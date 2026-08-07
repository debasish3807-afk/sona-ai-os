"""HTML document loader."""

import re
import uuid

import structlog

from sona_knowledge.domain.models import Document, DocumentType
from sona_knowledge.infrastructure.loaders.base import DocumentLoader

logger = structlog.get_logger()


class HTMLLoader(DocumentLoader):
    """Loader for HTML documents.

    Strips HTML tags and extracts the title and body text.
    """

    async def load(self, source: str, **kwargs: object) -> Document:
        """Load HTML content as a Document.

        Args:
            source: The HTML content string.
            **kwargs: Optional 'title' and 'doc_id' overrides.

        Returns:
            A Document with stripped text content and extracted title.
        """
        title = str(kwargs.get("title", "")) or self._extract_title(source)
        doc_id = str(kwargs.get("doc_id", "")) or str(uuid.uuid4())
        source_url = str(kwargs.get("source_url", "")) or None

        text_content = self._strip_tags(source)

        logger.info(
            "loading_html_document",
            title=title,
            original_length=len(source),
            text_length=len(text_content),
        )

        return Document(
            id=doc_id,
            title=title,
            content=text_content,
            doc_type=DocumentType.HTML,
            metadata={
                "original_length": len(source),
                "word_count": len(text_content.split()),
            },
            source_url=source_url,
        )

    def supports(self, source: str) -> bool:
        """Check if source is HTML content."""
        lower = source.strip().lower()
        return (
            source.endswith(".html")
            or source.endswith(".htm")
            or lower.startswith("<!doctype")
            or lower.startswith("<html")
        )

    def _extract_title(self, html: str) -> str:
        """Extract title from <title> tag."""
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        # Try h1
        match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        if match:
            return self._strip_tags(match.group(1)).strip()
        return "Untitled HTML"

    def _strip_tags(self, html: str) -> str:
        """Remove HTML tags and normalize whitespace."""
        # Remove script and style blocks
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        # Remove tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Decode common HTML entities
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()
