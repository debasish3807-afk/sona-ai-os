"""In-memory vector store with cosine similarity search."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class _VectorEntry:
    """Internal storage entry."""

    doc_id: str
    vector: list[float]
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """In-memory vector store with cosine similarity search."""

    def __init__(self, dimension: int = 128) -> None:
        self._dimension = dimension
        self._entries: dict[str, _VectorEntry] = {}

    def add(
        self,
        doc_id: str,
        vector: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Add a vector to the store."""
        if len(vector) != self._dimension:
            msg = f"Vector dimension mismatch: expected {self._dimension}, got {len(vector)}"
            raise ValueError(msg)
        self._entries[doc_id] = _VectorEntry(
            doc_id=doc_id,
            vector=vector,
            metadata=metadata or {},
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
    ) -> list[tuple[str, float]]:
        """Search for most similar vectors by cosine similarity.

        Returns list of (doc_id, score) sorted by descending similarity.
        """
        if len(query_vector) != self._dimension:
            msg = (
                f"Query vector dimension mismatch: expected "
                f"{self._dimension}, got {len(query_vector)}"
            )
            raise ValueError(msg)

        results: list[tuple[str, float]] = []
        for entry in self._entries.values():
            score = self._cosine_similarity(query_vector, entry.vector)
            results.append((entry.doc_id, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def remove(self, doc_id: str) -> bool:
        """Remove a vector from the store."""
        if doc_id in self._entries:
            del self._entries[doc_id]
            return True
        return False

    @property
    def size(self) -> int:
        """Number of vectors in the store."""
        return len(self._entries)

    def clear(self) -> None:
        """Remove all vectors from the store."""
        self._entries.clear()

    def _cosine_similarity(
        self,
        vec_a: list[float],
        vec_b: list[float],
    ) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)
