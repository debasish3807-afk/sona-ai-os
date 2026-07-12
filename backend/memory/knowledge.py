"""Knowledge memory - documents and external knowledge bases.

This module defines the knowledge memory interface for managing ingested
documents, external knowledge bases, and chunked content with embeddings.
It provides document lifecycle management and semantic search over
chunked document content.

Knowledge memory handles the RAG (Retrieval-Augmented Generation) document
store functionality, including document ingestion, chunking, embedding,
and retrieval.

Classes:
    KnowledgeConfig: Configuration for knowledge memory behavior.
    KnowledgeChunk: A single chunk of a document with optional embedding.
    KnowledgeDocument: A complete document with its chunks.
    KnowledgeMemory: Abstract interface extending MemoryStore for knowledge memory.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .base import MemoryStore


@dataclass(frozen=True, slots=True)
class KnowledgeConfig:
    """Configuration for knowledge memory behavior.

    Controls document capacity, chunking parameters, and embedding settings.

    Attributes:
        max_documents: Maximum number of documents to retain.
        chunk_size: Target chunk size in tokens.
        chunk_overlap: Number of overlapping tokens between adjacent chunks.
        auto_embed: Whether to automatically generate embeddings on ingest.
        max_chunks_per_document: Maximum chunks a single document can produce.
        supported_formats: List of supported document formats.
    """

    max_documents: int = 10000
    chunk_size: int = 512
    chunk_overlap: int = 50
    auto_embed: bool = True
    max_chunks_per_document: int = 1000
    supported_formats: list[str] = field(
        default_factory=lambda: ["text", "markdown", "html", "pdf", "json"]
    )


@dataclass(slots=True)
class KnowledgeChunk:
    """A single chunk of a document with optional embedding.

    Chunks are the fundamental retrieval units for knowledge memory.
    Documents are split into chunks for efficient storage and semantic search.

    Attributes:
        chunk_id: Unique identifier for this chunk (UUID4).
        doc_id: ID of the parent document this chunk belongs to.
        content: The text content of this chunk.
        position: Positional index within the parent document (0-based).
        embedding: Optional dense vector embedding for semantic search.
        token_count: Number of tokens in this chunk.
        metadata: Additional chunk metadata (e.g., section headers, page numbers).
    """

    doc_id: str
    content: str
    position: int
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    embedding: Optional[list[float]] = None
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class KnowledgeDocument:
    """A complete document with its chunks and metadata.

    Represents an ingested document including its original content,
    generated chunks, and processing status.

    Attributes:
        doc_id: Unique identifier for this document (UUID4).
        title: Document title.
        source: Source location or URL of the document.
        content: Full original content of the document.
        chunks: List of chunks generated from this document.
        embedded: Whether all chunks have been embedded.
        created_at: UTC timestamp when this document was ingested.
        updated_at: UTC timestamp of the most recent update.
        format: Document format ('text', 'markdown', 'html', etc.).
        size_bytes: Size of the original content in bytes.
        metadata: Additional document metadata.
    """

    title: str
    source: str
    content: str
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chunks: list[KnowledgeChunk] = field(default_factory=list)
    embedded: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    format: str = "text"
    size_bytes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeMemory(MemoryStore):
    """Abstract interface for knowledge memory operations.

    Extends the base MemoryStore with document ingestion, chunk-level
    search, document management, and re-indexing capabilities.
    """

    @abstractmethod
    async def ingest_document(self, document: KnowledgeDocument) -> str:
        """Ingest a new document into knowledge memory.

        Processes the document, generates chunks, and optionally
        creates embeddings for each chunk.

        Args:
            document: The document to ingest.

        Returns:
            The doc_id of the ingested document.
        """
        ...

    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve a document by its ID.

        Args:
            doc_id: The unique identifier of the document.

        Returns:
            The document if found, None otherwise.
        """
        ...

    @abstractmethod
    async def search_knowledge(
        self, query: str, max_chunks: int = 10
    ) -> list[KnowledgeChunk]:
        """Search knowledge memory for relevant chunks.

        Performs semantic and/or keyword search across all document
        chunks and returns the most relevant results.

        Args:
            query: The search query text.
            max_chunks: Maximum number of chunks to return.

        Returns:
            List of matching chunks ordered by relevance.
        """
        ...

    @abstractmethod
    async def list_documents(
        self, limit: int = 50, offset: int = 0
    ) -> list[KnowledgeDocument]:
        """List all documents with pagination.

        Args:
            limit: Maximum number of documents to return.
            offset: Number of documents to skip for pagination.

        Returns:
            List of documents (without full content for efficiency).
        """
        ...

    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all its chunks.

        Args:
            doc_id: The ID of the document to delete.

        Returns:
            True if the document was found and deleted, False otherwise.
        """
        ...

    @abstractmethod
    async def reindex_document(self, doc_id: str) -> None:
        """Re-chunk and re-embed a document.

        Useful when chunking or embedding configuration has changed.

        Args:
            doc_id: The ID of the document to re-index.
        """
        ...
