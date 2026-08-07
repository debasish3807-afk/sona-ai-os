"""Plain text document loader."""

import uuid

import structlog

from sona_knowledge.domain.models import Document, DocumentType
from sona_knowledge.infrastructure.loaders.base import DocumentLoader

logger = structlog.get_logger()


class TextLoader(DocumentLoader):
    """Loader for plain text documents.

    Supports .txt files and raw text content.
    """

    async def load(self, source: str, **kwargs: object) -> Document:
        """Load plain text content as a Document.

        Args:
            source: The text content or file path.
            **kwargs: Optional 'title' and 'doc_id' overrides.

        Returns:
            A Document with the text content.
        """
        title = str(kwargs.get("title", "")) or self._extract_title(source)
        doc_id = str(kwargs.get("doc_id", "")) or str(uuid.uuid4())
        source_url = str(kwargs.get("source_url", "")) or None

        logger.info("loading_text_document", title=title, length=len(source))

        return Document(
            id=doc_id,
            title=title,
            content=source,
            doc_type=DocumentType.TEXT,
            metadata={"word_count": len(source.split())},
            source_url=source_url,
        )

    def supports(self, source: str) -> bool:
        """Check if source is a text file or plain text content."""
        return source.endswith(".txt") or not any(
            source.startswith(prefix)
            for prefix in ("<!DOCTYPE", "<html", "# ", "http://", "https://")
        )

    def _extract_title(self, content: str) -> str:
        """Extract a title from the first line of text content."""
        first_line = content.strip().split("\n")[0][:100] if content.strip() else "Untitled"
        return first_line
