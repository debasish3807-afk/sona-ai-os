"""In-memory vector store for Knowledge OS.

Provides vector storage and similarity search using cosine similarity.
Designed with the same interface as production vector databases.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

from sona_knowledge.infrastructure.embedding_service import cosine_similarity

logger = structlog.get_logger()


@dataclass
class VectorRecord:
    """A record stored in the vector store."""

    id: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    content: str = ""


@dataclass
class SearchResult:
    """A search result from the vector store."""

    id: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    content: str = ""


class VectorStore:
    """In-memory vector store with cosine similarity search.

    Supports upsert, search, delete, and metadata filtering.
    Suitable for testing and development without external dependencies.
    """

    def __init__(self) -> None:
        """Initialize an empty vector store."""
        self._records: dict[str, VectorRecord] = {}

    @property
    def size(self) -> int:
        """Return the number of records in the store."""
        return len(self._records)

    async def upsert(
        self,
        record_id: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
        content: str = "",
    ) -> None:
        """Insert or update a vector record.

        Args:
            record_id: Unique identifier for the record.
            vector: The embedding vector.
            metadata: Optional metadata associated with the record.
            content: Optional text content of the record.
        """
        self._records[record_id] = VectorRecord(
            id=record_id,
            vector=vector,
            metadata=metadata or {},
            content=content,
        )
        logger.debug("vector_upserted", record_id=record_id)

    async def upsert_batch(
        self,
        records: list[tuple[str, list[float], dict[str, Any], str]],
    ) -> None:
        """Insert or update multiple records in batch.

        Args:
            records: List of (id, vector, metadata, content) tuples.
        """
        for record_id, vector, metadata, content in records:
            self._records[record_id] = VectorRecord(
                id=record_id,
                vector=vector,
                metadata=metadata,
                content=content,
            )
        logger.debug("vector_batch_upserted", count=len(records))

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        min_score: float = 0.0,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for the most similar vectors.

        Args:
            query_vector: The query embedding vector.
            top_k: Maximum number of results to return.
            min_score: Minimum similarity score threshold.
            metadata_filter: Optional metadata key-value pairs to filter by.

        Returns:
            List of SearchResult sorted by descending similarity score.
        """
        results: list[SearchResult] = []

        for record in self._records.values():
            # Apply metadata filter
            if metadata_filter and not self._matches_filter(record.metadata, metadata_filter):
                continue

            score = cosine_similarity(query_vector, record.vector)
            if score >= min_score:
                results.append(
                    SearchResult(
                        id=record.id,
                        score=score,
                        metadata=record.metadata,
                        content=record.content,
                    )
                )

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def delete(self, record_id: str) -> bool:
        """Delete a record by ID.

        Args:
            record_id: The ID of the record to delete.

        Returns:
            True if record was found and deleted, False otherwise.
        """
        if record_id in self._records:
            del self._records[record_id]
            logger.debug("vector_deleted", record_id=record_id)
            return True
        return False

    async def delete_by_metadata(self, metadata_filter: dict[str, Any]) -> int:
        """Delete all records matching metadata filter.

        Args:
            metadata_filter: Key-value pairs to match.

        Returns:
            Number of records deleted.
        """
        to_delete = [
            rid
            for rid, record in self._records.items()
            if self._matches_filter(record.metadata, metadata_filter)
        ]
        for rid in to_delete:
            del self._records[rid]
        logger.debug("vectors_deleted_by_metadata", count=len(to_delete))
        return len(to_delete)

    async def get(self, record_id: str) -> VectorRecord | None:
        """Get a record by ID.

        Args:
            record_id: The ID of the record to retrieve.

        Returns:
            The VectorRecord if found, None otherwise.
        """
        return self._records.get(record_id)

    async def clear(self) -> None:
        """Remove all records from the store."""
        self._records.clear()
        logger.debug("vector_store_cleared")

    def _matches_filter(self, metadata: dict[str, Any], filter_dict: dict[str, Any]) -> bool:
        """Check if metadata matches all filter criteria."""
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
