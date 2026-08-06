"""Domain models for the Knowledge OS service.

Defines the data structures used by the Knowledge OS for document processing,
RAG (Retrieval-Augmented Generation) queries, and knowledge base management.
"""

from dataclasses import dataclass
from enum import StrEnum


class DocumentType(StrEnum):
    """Supported document types for ingestion and processing.

    Determines how the document processor extracts text,
    applies chunking strategies, and generates embeddings.
    """

    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    CODE = "code"
    JSON = "json"


@dataclass(frozen=True)
class Document:
    """A document to be ingested into a knowledge base.

    Attributes:
        id: Unique identifier for the document.
        title: Human-readable title of the document.
        content: The raw textual content of the document.
        doc_type: The type/format of the document.
        metadata: Optional metadata (e.g., author, tags, creation date).
        source_url: Optional URL where the document was sourced from.
    """

    id: str
    title: str
    content: str
    doc_type: DocumentType
    metadata: dict | None = None
    source_url: str | None = None


@dataclass(frozen=True)
class DocumentChunk:
    """A chunk of a processed document with its embedding.

    Documents are split into smaller chunks for embedding and retrieval.
    Each chunk maintains a reference to its parent document.

    Attributes:
        id: Unique identifier for the chunk.
        document_id: ID of the parent document this chunk belongs to.
        content: The text content of this chunk.
        embedding: The vector embedding for similarity search.
        chunk_index: Position index of this chunk within the document.
        metadata: Optional metadata for the chunk (e.g., section heading).
    """

    id: str
    document_id: str
    content: str
    embedding: list[float]
    chunk_index: int
    metadata: dict | None = None


@dataclass(frozen=True)
class RAGQuery:
    """A query to the RAG (Retrieval-Augmented Generation) pipeline.

    Attributes:
        query: The user's query text to search for.
        knowledge_base_id: Optional ID to restrict search to a specific knowledge base.
        top_k: Maximum number of relevant chunks to retrieve.
        min_similarity: Minimum similarity threshold for results (0.0 to 1.0).
        rerank: Whether to apply re-ranking to improve result quality.
    """

    query: str
    knowledge_base_id: str | None = None
    top_k: int = 5
    min_similarity: float = 0.7
    rerank: bool = True


@dataclass(frozen=True)
class RAGResult:
    """Result of a RAG query containing relevant chunks and augmented context.

    Attributes:
        chunks: The retrieved document chunks matching the query.
        augmented_context: The assembled context string for LLM augmentation.
        sources: List of source identifiers (URLs or document IDs) for attribution.
        confidence: Overall confidence score of the retrieval (0.0 to 1.0).
    """

    chunks: list[DocumentChunk]
    augmented_context: str
    sources: list[str]
    confidence: float
