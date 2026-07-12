"""Vector store interface — abstract contract for embedding storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorRecord:
    """A stored embedding with metadata."""

    record_id: str
    content: str
    embedding: list[float]
    doc_id: str = ""
    chunk_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """A single result from similarity search."""

    record: VectorRecord
    score: float  # 0.0 to 1.0 (higher = more similar)
    rank: int = 0


class VectorStore(ABC):
    """Abstract vector store for embedding storage and retrieval."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store."""
        ...

    @abstractmethod
    async def add(self, records: list[VectorRecord]) -> int:
        """Add records to the store. Returns count added."""
        ...

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float = 0.0,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar embeddings.

        Args:
            query_embedding: The query vector.
            top_k: Maximum results to return.
            min_score: Minimum similarity threshold.
            filter_metadata: Optional metadata filters.

        Returns:
            Ranked list of SearchResults.
        """
        ...

    @abstractmethod
    async def delete(self, record_ids: list[str]) -> int:
        """Delete records by ID. Returns count deleted."""
        ...

    @abstractmethod
    async def delete_by_doc(self, doc_id: str) -> int:
        """Delete all records for a document."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Total number of stored records."""
        ...
