"""Knowledge OS domain events."""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class DocumentIngestedEvent(DomainEvent):  # type: ignore[misc]
    """Raised when a document is successfully ingested into a knowledge base."""

    document_id: str = ""
    kb_id: str = ""
    chunks_count: int = 0
    doc_type: str = ""


@dataclass(frozen=True)
class DocumentDeletedEvent(DomainEvent):  # type: ignore[misc]
    """Raised when a document is deleted from a knowledge base."""

    document_id: str = ""


@dataclass(frozen=True)
class QueryExecutedEvent(DomainEvent):  # type: ignore[misc]
    """Raised when a RAG query is executed."""

    query: str = ""
    results_count: int = 0
    confidence: float = 0.0


@dataclass(frozen=True)
class IndexingCompletedEvent(DomainEvent):  # type: ignore[misc]
    """Raised when indexing of a knowledge base is completed."""

    kb_id: str = ""
    documents_indexed: int = 0
    chunks_indexed: int = 0
