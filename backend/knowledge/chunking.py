"""Text chunking engine for document processing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from config.logging import get_logger
from knowledge.schemas import Chunk, Document, DocumentType

logger = get_logger(__name__)


@dataclass
class ChunkingEngine:
    """Splits documents into manageable chunks for indexing and retrieval."""

    max_chunk_size: int = 512
    overlap: int = 50
    _stats: dict = field(default_factory=lambda: {"chunks_created": 0})

    def chunk_text(self, text: str) -> list[str]:
        """Split plain text into overlapping chunks."""
        if not text.strip():
            return []

        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.max_chunk_size, text_len)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += self.max_chunk_size - self.overlap

        self._stats["chunks_created"] += len(chunks)
        return chunks

    def chunk_markdown(self, text: str) -> list[str]:
        """Split markdown by headings, then by size if needed."""
        if not text.strip():
            return []

        sections = re.split(r"(?m)^(#{1,6}\s+.+)$", text)
        chunks: list[str] = []
        current = ""

        for section in sections:
            section = section.strip()
            if not section:
                continue

            if len(current) + len(section) > self.max_chunk_size:
                if current.strip():
                    chunks.append(current.strip())
                if len(section) > self.max_chunk_size:
                    chunks.extend(self.chunk_text(section))
                    current = ""
                else:
                    current = section
            else:
                current = f"{current}\n{section}" if current else section

        if current.strip():
            chunks.append(current.strip())

        self._stats["chunks_created"] += len(chunks)
        return chunks

    def chunk_document(self, doc: Document) -> list[Chunk]:
        """Chunk a document based on its type."""
        if doc.doc_type == DocumentType.MARKDOWN:
            texts = self.chunk_markdown(doc.content)
        else:
            texts = self.chunk_text(doc.content)

        return [
            Chunk(
                doc_id=doc.doc_id,
                content=text,
                index=i,
                metadata={"doc_title": doc.title},
            )
            for i, text in enumerate(texts)
        ]
