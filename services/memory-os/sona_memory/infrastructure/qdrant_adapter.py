"""Mock Qdrant vector database adapter.

Provides an in-memory simulation of Qdrant vector operations
for long-term and semantic memory storage.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from sona_memory.infrastructure.embedding_service import cosine_similarity


@dataclass
class PointStruct:
    """A point in the vector space with payload."""

    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredPoint:
    """A point with its similarity score from a search."""

    id: str
    score: float
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


class QdrantAdapter:
    """In-memory mock of Qdrant vector database operations.

    Supports upsert, search (cosine similarity), delete, and scroll
    operations with payload filtering.
    """

    def __init__(self) -> None:
        self._collections: dict[str, list[PointStruct]] = {}
        self._lock = asyncio.Lock()

    async def create_collection(self, name: str, vector_size: int = 128) -> None:
        """Create a new collection (no-op if exists)."""
        async with self._lock:
            if name not in self._collections:
                self._collections[name] = []

    async def upsert(self, collection: str, points: list[PointStruct]) -> int:
        """Insert or update points in a collection."""
        async with self._lock:
            if collection not in self._collections:
                self._collections[collection] = []

            coll = self._collections[collection]
            existing_ids = {p.id: i for i, p in enumerate(coll)}

            upserted = 0
            for point in points:
                if point.id in existing_ids:
                    coll[existing_ids[point.id]] = point
                else:
                    coll.append(point)
                upserted += 1
            return upserted

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.0,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[ScoredPoint]:
        """Search for similar vectors using cosine similarity."""
        async with self._lock:
            if collection not in self._collections:
                return []

            results: list[ScoredPoint] = []
            for point in self._collections[collection]:
                # Apply filter conditions
                if filter_conditions and not self._matches_filter(point.payload, filter_conditions):
                    continue

                score = cosine_similarity(query_vector, point.vector)
                if score >= score_threshold:
                    results.append(
                        ScoredPoint(
                            id=point.id,
                            score=score,
                            vector=point.vector,
                            payload=point.payload,
                        )
                    )

            # Sort by score descending
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]

    async def delete(self, collection: str, point_ids: list[str]) -> int:
        """Delete points by their IDs."""
        async with self._lock:
            if collection not in self._collections:
                return 0

            id_set = set(point_ids)
            before = len(self._collections[collection])
            self._collections[collection] = [
                p for p in self._collections[collection] if p.id not in id_set
            ]
            return before - len(self._collections[collection])

    async def scroll(
        self,
        collection: str,
        limit: int = 100,
        offset: int = 0,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[PointStruct]:
        """Scroll through points in a collection with optional filtering."""
        async with self._lock:
            if collection not in self._collections:
                return []

            coll = self._collections[collection]

            if filter_conditions:
                filtered = [p for p in coll if self._matches_filter(p.payload, filter_conditions)]
            else:
                filtered = list(coll)

            return filtered[offset : offset + limit]

    async def count(self, collection: str) -> int:
        """Get the number of points in a collection."""
        async with self._lock:
            if collection not in self._collections:
                return 0
            return len(self._collections[collection])

    async def get(self, collection: str, point_id: str) -> PointStruct | None:
        """Get a single point by ID."""
        async with self._lock:
            if collection not in self._collections:
                return None
            for point in self._collections[collection]:
                if point.id == point_id:
                    return point
            return None

    async def delete_collection(self, name: str) -> bool:
        """Delete an entire collection."""
        async with self._lock:
            if name in self._collections:
                del self._collections[name]
                return True
            return False

    @staticmethod
    def _matches_filter(payload: dict[str, Any], conditions: dict[str, Any]) -> bool:
        """Check if a payload matches the filter conditions."""
        for key, value in conditions.items():
            if key not in payload:
                return False
            if isinstance(value, dict):
                # Support range queries
                if "$gte" in value and payload[key] < value["$gte"]:
                    return False
                if "$lte" in value and payload[key] > value["$lte"]:
                    return False
                if "$gt" in value and payload[key] <= value["$gt"]:
                    return False
                if "$lt" in value and payload[key] >= value["$lt"]:
                    return False
                if "$in" in value and payload[key] not in value["$in"]:
                    return False
            elif payload[key] != value:
                return False
        return True
