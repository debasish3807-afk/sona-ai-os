"""Document ingestion — parse, chunk, and index documents.

Supports multiple file types: plain text, Markdown, code files,
JSON, CSV, YAML, XML, HTML. Extensible for PDF/DOCX via plugins.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import uuid4

from config.logging import get_logger
from storage.repository import DocumentRecord
from vector.embeddings import EmbeddingEngine, chunk_text
from vector.store import VectorRecord

logger = get_logger(__name__)


class SupportedFileType(str, Enum):
    """File types supported for ingestion."""

    TEXT = "txt"
    MARKDOWN = "md"
    PYTHON = "py"
    JAVASCRIPT = "js"
    TYPESCRIPT = "ts"
    JAVA = "java"
    KOTLIN = "kt"
    JSON = "json"
    CSV = "csv"
    YAML = "yaml"
    XML = "xml"
    HTML = "html"


EXTENSION_MAP: dict[str, SupportedFileType] = {
    ".txt": SupportedFileType.TEXT,
    ".md": SupportedFileType.MARKDOWN,
    ".py": SupportedFileType.PYTHON,
    ".js": SupportedFileType.JAVASCRIPT,
    ".ts": SupportedFileType.TYPESCRIPT,
    ".java": SupportedFileType.JAVA,
    ".kt": SupportedFileType.KOTLIN,
    ".json": SupportedFileType.JSON,
    ".csv": SupportedFileType.CSV,
    ".yaml": SupportedFileType.YAML,
    ".yml": SupportedFileType.YAML,
    ".xml": SupportedFileType.XML,
    ".html": SupportedFileType.HTML,
    ".htm": SupportedFileType.HTML,
}


@dataclass
class IngestionResult:
    """Result of document ingestion."""

    doc_id: str
    title: str
    chunks_created: int
    token_count: int
    doc_type: str


class DocumentIngester:
    """Ingests documents into the knowledge base.

    Pipeline: Read → Parse → Chunk → Embed → Store
    """

    def __init__(self, embedding_engine: EmbeddingEngine | None = None) -> None:
        self._embedder = embedding_engine or EmbeddingEngine()

    def detect_file_type(self, filename: str) -> str:
        """Detect file type from extension."""
        ext = os.path.splitext(filename)[1].lower()
        file_type = EXTENSION_MAP.get(ext)
        return file_type.value if file_type else "text"

    def ingest_text(
        self,
        content: str,
        title: str = "",
        source: str = "",
        doc_type: str = "text",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[DocumentRecord, list[VectorRecord]]:
        """Ingest text content into document + vector records.

        Args:
            content: The text content to ingest.
            title: Document title.
            source: Source path or URL.
            doc_type: Document type classification.
            tags: Optional tags.
            metadata: Optional metadata.

        Returns:
            Tuple of (DocumentRecord, list of VectorRecords).
        """
        doc_id = str(uuid4())
        chunks = chunk_text(content)

        # Create embeddings for each chunk
        vector_records: list[VectorRecord] = []
        for chunk in chunks:
            embedding = self._embedder.embed_text(chunk.content)
            vector_records.append(
                VectorRecord(
                    record_id=f"{doc_id}_{chunk.chunk_index}",
                    content=chunk.content,
                    embedding=embedding,
                    doc_id=doc_id,
                    chunk_index=chunk.chunk_index,
                    metadata={
                        "title": title,
                        "doc_type": doc_type,
                        "source": source,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        **(metadata or {}),
                    },
                )
            )

        # Create document record
        total_tokens = sum(c.token_estimate for c in chunks)
        doc_record = DocumentRecord(
            doc_id=doc_id,
            title=title or source or "Untitled",
            content=content,
            doc_type=doc_type,
            source=source,
            tags=tags or [],
            metadata=metadata or {},
            chunk_count=len(chunks),
            token_count=total_tokens,
        )

        logger.info(
            "Document ingested",
            doc_id=doc_id,
            chunks=len(chunks),
            tokens=total_tokens,
        )
        return doc_record, vector_records
