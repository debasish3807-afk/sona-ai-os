"""In-memory vector store — development/testing implementation.

Uses cosine similarity over numpy-free pure Python vectors.
Suitable for development, testing, and small-scale deployments.
For production at scale, use Qdrant or ChromaDB backends.
"""

from __future__ import annotations

import math
from typing import Any

from config.logging import get_logger
from vector.store import SearchResult, VectorRecord, VectorStore

logger = get_logger(__name__)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore(VectorStore):
    """Pure-Python in-memory vector store with cosine similarity search.

    No external dependencies required. Suitable for:
        - Development and testing
        - Small collections (< 100K vectors)
        - Environments where ChromaDB/Qdrant aren't available
    """

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    async def initialize(self) -> None:
        logger.info("In-memory vector store initialized")

    async def add(self, records: list[VectorRecord]) -> int:
        count = 0
        for record in records:
            self._records[record.record_id] = record
            count += 1
        logger.debug("Added vectors", count=count, total=len(self._records))
        return count

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float = 0.0,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        scored: list[tuple[float, VectorRecord]] = []

        for record in self._records.values():
            # Apply metadata filter
            if filter_metadata:
                skip = False
                for key, val in filter_metadata.items():
                    if record.metadata.get(key) != val:
                        skip = True
                        break
                if skip:
                    continue

            score = _cosine_similarity(query_embedding, record.embedding)
            if score >= min_score:
                scored.append((score, record))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[SearchResult] = []
        for rank, (score, record) in enumerate(scored[:top_k]):
            results.append(SearchResult(record=record, score=score, rank=rank))

        return results

    async def delete(self, record_ids: list[str]) -> int:
        count = 0
        for rid in record_ids:
            if rid in self._records:
                del self._records[rid]
                count += 1
        return count

    async def delete_by_doc(self, doc_id: str) -> int:
        to_delete = [rid for rid, r in self._records.items() if r.doc_id == doc_id]
        for rid in to_delete:
            del self._records[rid]
        return len(to_delete)

    async def count(self) -> int:
        return len(self._records)
