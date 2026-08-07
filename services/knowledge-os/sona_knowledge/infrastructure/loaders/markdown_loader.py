"""Markdown document loader."""

import re
import uuid

import structlog

from sona_knowledge.domain.models import Document, DocumentType
from sona_knowledge.infrastructure.loaders.base import DocumentLoader

logger = structlog.get_logger()


class MarkdownLoader(DocumentLoader):
    """Loader for Markdown documents.

    Extracts headings as metadata and preserves document structure.
    """

    async def load(self, source: str, **kwargs: object) -> Document:
        """Load Markdown content as a Document.

        Args:
            source: The markdown content string.
            **kwargs: Optional 'title' and 'doc_id' overrides.

        Returns:
            A Document with content and extracted heading metadata.
        """
        title = str(kwargs.get("title", "")) or self._extract_title(source)
        doc_id = str(kwargs.get("doc_id", "")) or str(uuid.uuid4())
        source_url = str(kwargs.get("source_url", "")) or None

        headings = self._extract_headings(source)

        logger.info(
            "loading_markdown_document",
            title=title,
            headings_count=len(headings),
        )

        return Document(
            id=doc_id,
            title=title,
            content=source,
            doc_type=DocumentType.MARKDOWN,
            metadata={
                "headings": headings,
                "word_count": len(source.split()),
            },
            source_url=source_url,
        )

    def supports(self, source: str) -> bool:
        """Check if source is Markdown content."""
        return source.endswith(".md") or source.lstrip().startswith("# ")

    def _extract_title(self, content: str) -> str:
        """Extract title from the first H1 heading."""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        # Fall back to first non-empty line
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped:
                return stripped[:100]
        return "Untitled Markdown"

    def _extract_headings(self, content: str) -> list[dict[str, object]]:
        """Extract all headings with their levels."""
        headings: list[dict[str, object]] = []
        for match in re.finditer(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append({"level": level, "text": text})
        return headings
