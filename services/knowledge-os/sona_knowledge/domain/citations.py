"""Citation models for source attribution."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    """A citation referencing a source chunk used in a RAG response.

    Attributes:
        chunk_id: Unique identifier of the referenced chunk.
        document_id: ID of the parent document.
        document_title: Human-readable title of the source document.
        content_excerpt: Brief excerpt from the chunk content.
        relevance_score: Similarity/relevance score (0.0 to 1.0).
        source_url: Optional URL for the original source.
        page_number: Optional page number within the document.
        section: Optional section heading within the document.
    """

    chunk_id: str
    document_id: str
    document_title: str
    content_excerpt: str
    relevance_score: float
    source_url: str = ""
    page_number: int | None = None
    section: str = ""
