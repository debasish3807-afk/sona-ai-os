"""Production Qdrant adapter using httpx for vector operations.

Connects to a real Qdrant instance via its REST API.
Falls back to the in-memory mock adapter if Qdrant is unavailable.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx
import structlog

from sona_memory.infrastructure.qdrant_adapter import (
    PointStruct,
    QdrantAdapter,
)

logger = structlog.get_logger()


@dataclass
class QdrantPoint:
    """A point to upsert into Qdrant."""

    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


class QdrantProductionAdapter:
    """Production Qdrant adapter with httpx and connection management.

    Connects to a real Qdrant instance via its REST API. Falls back to
    the in-memory mock adapter when Qdrant is not reachable.
    """

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection: str = "sona_memories",
        vector_size: int = 384,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self._url = url.rstrip("/")
        self._collection = collection
        self._vector_size = vector_size
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._client: httpx.AsyncClient | None = None
        self._connected = False
        self._use_real = False
        # Fallback to in-memory mock
        self._backend = QdrantAdapter()

    async def connect(self) -> bool:
        """Attempt to connect to Qdrant with exponential backoff retry.

        Returns True if connection established, False if falling back.
        """
        for attempt in range(self._max_retries):
            try:
                client = httpx.AsyncClient(
                    base_url=self._url,
                    timeout=httpx.Timeout(30.0),
                )
                response = await client.get("/healthz")
                if response.status_code == 200:
                    self._client = client
                    self._use_real = True
                    self._connected = True
                    await logger.ainfo(
                        "qdrant.connected",
                        url=self._url,
                        attempt=attempt + 1,
                    )
                    return True
                await client.aclose()
            except Exception as exc:  # noqa: BLE001
                delay = self._retry_delay * (2**attempt)
                await logger.awarning(
                    "qdrant.connect_retry",
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    delay=delay,
                    error=str(exc),
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(delay)

        await logger.awarning(
            "qdrant.fallback_to_mock",
            url=self._url,
            message="All connection attempts failed, using mock backend",
        )
        self._connected = True
        return False

    async def disconnect(self) -> None:
        """Close the httpx client."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception as exc:  # noqa: BLE001
                await logger.awarning("qdrant.disconnect_error", error=str(exc))
        self._client = None
        self._connected = False
        self._use_real = False
        await logger.ainfo("qdrant.disconnected")

    async def ensure_collection(self) -> None:
        """Create the collection if it does not exist."""
        if self._use_real and self._client is not None:
            try:
                response = await self._client.get(f"/collections/{self._collection}")
                if response.status_code == 404:
                    await self._client.put(
                        f"/collections/{self._collection}",
                        json={
                            "vectors": {
                                "size": self._vector_size,
                                "distance": "Cosine",
                            }
                        },
                    )
                    await logger.ainfo(
                        "qdrant.collection_created",
                        collection=self._collection,
                    )
            except Exception as exc:  # noqa: BLE001
                await logger.awarning("qdrant.ensure_collection_error", error=str(exc))
        else:
            await self._backend.create_collection(self._collection, self._vector_size)

    async def upsert(self, points: list[QdrantPoint]) -> None:
        """Upsert points into the collection."""
        if self._use_real and self._client is not None:
            payload = {
                "points": [
                    {
                        "id": p.id,
                        "vector": p.vector,
                        "payload": p.payload,
                    }
                    for p in points
                ]
            }
            try:
                response = await self._client.put(
                    f"/collections/{self._collection}/points",
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                await logger.aerror(
                    "qdrant.upsert_error",
                    status=exc.response.status_code,
                    detail=exc.response.text,
                )
                raise
        else:
            mock_points = [PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points]
            await self._backend.upsert(self._collection, mock_points)

    async def search(
        self,
        vector: list[float],
        limit: int = 10,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[tuple[QdrantPoint, float]]:
        """Search for similar vectors. Returns (point, score) tuples."""
        if self._use_real and self._client is not None:
            body: dict[str, Any] = {
                "vector": vector,
                "limit": limit,
                "with_payload": True,
                "with_vector": True,
            }
            if filter_payload:
                must_conditions = [
                    {"key": k, "match": {"value": v}} for k, v in filter_payload.items()
                ]
                body["filter"] = {"must": must_conditions}
            try:
                response = await self._client.post(
                    f"/collections/{self._collection}/points/search",
                    json=body,
                )
                response.raise_for_status()
                data = response.json()
                results: list[tuple[QdrantPoint, float]] = []
                for hit in data.get("result", []):
                    point = QdrantPoint(
                        id=str(hit["id"]),
                        vector=hit.get("vector", []),
                        payload=hit.get("payload", {}),
                    )
                    results.append((point, float(hit["score"])))
                return results
            except httpx.HTTPStatusError as exc:
                await logger.aerror(
                    "qdrant.search_error",
                    status=exc.response.status_code,
                )
                return []
        else:
            scored = await self._backend.search(
                collection=self._collection,
                query_vector=vector,
                limit=limit,
                filter_conditions=filter_payload,
            )
            return [
                (
                    QdrantPoint(id=sp.id, vector=sp.vector, payload=sp.payload),
                    sp.score,
                )
                for sp in scored
            ]

    async def delete(self, ids: list[str]) -> None:
        """Delete points by their IDs."""
        if self._use_real and self._client is not None:
            try:
                response = await self._client.post(
                    f"/collections/{self._collection}/points/delete",
                    json={"points": ids},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                await logger.aerror(
                    "qdrant.delete_error",
                    status=exc.response.status_code,
                )
                raise
        else:
            await self._backend.delete(self._collection, ids)

    async def count(self) -> int:
        """Get the number of points in the collection."""
        if self._use_real and self._client is not None:
            try:
                response = await self._client.get(f"/collections/{self._collection}")
                response.raise_for_status()
                data = response.json()
                result: int = data.get("result", {}).get("points_count", 0)
                return result
            except Exception:  # noqa: BLE001
                return 0
        return await self._backend.count(self._collection)

    @property
    def is_connected(self) -> bool:
        """Whether the adapter has an active connection (real or mock)."""
        return self._connected

    @property
    def is_using_real_qdrant(self) -> bool:
        """Whether the adapter is using a real Qdrant connection."""
        return self._use_real
