"""PDF document loader (simple text extraction without external deps)."""

import uuid

import structlog

from sona_knowledge.domain.models import Document, DocumentType
from sona_knowledge.infrastructure.loaders.base import DocumentLoader

logger = structlog.get_logger()


class PDFLoader(DocumentLoader):
    """Loader for PDF documents.

    Provides simple text extraction from PDF content without heavy
    external dependencies. For production use, integrates with
    PDF parsing libraries.
    """

    async def load(self, source: str, **kwargs: object) -> Document:
        """Load PDF content as a Document.

        In this implementation, source is expected to be pre-extracted
        text from a PDF (simulating PDF text extraction).

        Args:
            source: The extracted text content from PDF.
            **kwargs: Optional 'title', 'doc_id', 'page_count' overrides.

        Returns:
            A Document with the extracted text content.
        """
        title = str(kwargs.get("title", "")) or self._extract_title(source)
        doc_id = str(kwargs.get("doc_id", "")) or str(uuid.uuid4())
        source_url = str(kwargs.get("source_url", "")) or None
        page_count = int(kwargs.get("page_count", 0)) or self._estimate_pages(source)

        logger.info(
            "loading_pdf_document",
            title=title,
            estimated_pages=page_count,
        )

        return Document(
            id=doc_id,
            title=title,
            content=source,
            doc_type=DocumentType.PDF,
            metadata={
                "page_count": page_count,
                "word_count": len(source.split()),
            },
            source_url=source_url,
        )

    def supports(self, source: str) -> bool:
        """Check if source is a PDF file reference."""
        return source.endswith(".pdf") or source.startswith("%PDF")

    def _extract_title(self, content: str) -> str:
        """Extract title from the first line of PDF text."""
        lines = content.strip().split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped and len(stripped) > 3:
                return stripped[:100]
        return "Untitled PDF"

    def _estimate_pages(self, content: str) -> int:
        """Estimate page count based on content length.

        Approximate: ~3000 characters per page.
        """
        chars = len(content)
        return max(1, chars // 3000)
