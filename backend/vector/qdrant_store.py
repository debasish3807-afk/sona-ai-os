"""Qdrant vector database client for Sona AI OS.

Connects to a Qdrant instance via its REST API for vector similarity search.
Falls back to the in-memory VectorStore when Qdrant is unavailable.

Qdrant can run locally via Docker (free):
    docker run -p 6333:6333 qdrant/qdrant

Configure via QDRANT_URL env var: http://localhost:6333
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from config.logging import get_logger

logger = get_logger(__name__)

DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_COLLECTION = "sona_vectors"
_TIMEOUT = httpx.Timeout(30.0, connect=5.0)


class QdrantStore:
    """Qdrant vector database client with HTTP REST API.

    Provides vector upsert, search, and delete operations.
    Falls back gracefully when Qdrant is not running.
    """

    def __init__(
        self,
        qdrant_url: str | None = None,
        collection_name: str = DEFAULT_COLLECTION,
        dimension: int = 384,
    ) -> None:
        self._url = qdrant_url or os.environ.get("QDRANT_URL", DEFAULT_QDRANT_URL)
        self._collection = collection_name
        self._dimension = dimension
        self._client: httpx.AsyncClient | None = None
        self._available = False

    def _get_client(self) -> httpx.AsyncClient:
        """Lazily create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._url,
                timeout=_TIMEOUT,
            )
        return self._client

    async def initialize(self) -> None:
        """Connect to Qdrant and ensure collection exists."""
        try:
            client = self._get_client()
            # Check Qdrant health
            resp = await client.get("/healthz")
            if resp.status_code != 200:
                self._available = False
                logger.warning("qdrant_unhealthy", status=resp.status_code)
                return

            # Ensure collection exists
            await self._ensure_collection(client)
            self._available = True
            logger.info(
                "qdrant_initialized",
                url=self._url,
                collection=self._collection,
                dimension=self._dimension,
            )
        except httpx.ConnectError:
            self._available = False
            logger.warning("qdrant_unavailable", url=self._url)
        except Exception as exc:
            self._available = False
            logger.warning("qdrant_init_failed", error=str(exc))

    async def _ensure_collection(self, client: httpx.AsyncClient) -> None:
        """Create collection if it doesn't exist."""
        resp = await client.get(f"/collections/{self._collection}")
        if resp.status_code == 200:
            return  # Already exists

        # Create collection
        payload = {
            "vectors": {
                "size": self._dimension,
                "distance": "Cosine",
            }
        }
        resp = await client.put(f"/collections/{self._collection}", json=payload)
        if resp.status_code not in (200, 409):
            logger.error("qdrant_create_collection_failed", status=resp.status_code)

    async def shutdown(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        self._available = False

    @property
    def is_available(self) -> bool:
        """Whether Qdrant is connected and operational."""
        return self._available

    # --- Vector Operations ---

    async def upsert(
        self,
        doc_id: str,
        vector: list[float],
        payload: dict[str, Any] | None = None,
    ) -> bool:
        """Upsert a vector with optional metadata payload."""
        if not self._available:
            return False

        client = self._get_client()
        point_id = doc_id
        body = {
            "points": [
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": payload or {},
                }
            ]
        }

        try:
            resp = await client.put(
                f"/collections/{self._collection}/points",
                json=body,
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.error("qdrant_upsert_failed", error=str(exc))
            return False

    async def upsert_batch(
        self,
        items: list[tuple[str, list[float], dict[str, Any] | None]],
    ) -> int:
        """Batch upsert multiple vectors. Returns count of successful upserts."""
        if not self._available or not items:
            return 0

        client = self._get_client()
        points = [
            {
                "id": doc_id,
                "vector": vector,
                "payload": payload or {},
            }
            for doc_id, vector, payload in items
        ]

        try:
            resp = await client.put(
                f"/collections/{self._collection}/points",
                json={"points": points},
            )
            return len(items) if resp.status_code == 200 else 0
        except Exception as exc:
            logger.error("qdrant_batch_upsert_failed", error=str(exc))
            return 0

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        score_threshold: float = 0.0,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors. Returns list of {id, score, payload}."""
        if not self._available:
            return []

        client = self._get_client()
        body: dict[str, Any] = {
            "vector": query_vector,
            "limit": top_k,
            "with_payload": True,
            "score_threshold": score_threshold,
        }
        if filter_payload:
            body["filter"] = filter_payload

        try:
            resp = await client.post(
                f"/collections/{self._collection}/points/search",
                json=body,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = []
            for hit in data.get("result", []):
                results.append(
                    {
                        "id": hit.get("id", ""),
                        "score": hit.get("score", 0.0),
                        "payload": hit.get("payload", {}),
                    }
                )
            return results
        except Exception as exc:
            logger.error("qdrant_search_failed", error=str(exc))
            return []

    async def delete(self, doc_id: str) -> bool:
        """Delete a vector by ID."""
        if not self._available:
            return False

        client = self._get_client()
        body = {"points": [doc_id]}

        try:
            resp = await client.post(
                f"/collections/{self._collection}/points/delete",
                json=body,
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.error("qdrant_delete_failed", error=str(exc))
            return False

    async def delete_by_filter(self, field: str, value: str) -> bool:
        """Delete vectors matching a payload filter."""
        if not self._available:
            return False

        client = self._get_client()
        body = {"filter": {"must": [{"key": field, "match": {"value": value}}]}}

        try:
            resp = await client.post(
                f"/collections/{self._collection}/points/delete",
                json=body,
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.error("qdrant_delete_filter_failed", error=str(exc))
            return False

    async def count(self) -> int:
        """Get total number of vectors in collection."""
        if not self._available:
            return 0

        client = self._get_client()
        try:
            resp = await client.get(f"/collections/{self._collection}")
            if resp.status_code != 200:
                return 0
            data = resp.json()
            return int(data.get("result", {}).get("points_count", 0))
        except Exception:
            return 0

    async def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            client = self._get_client()
            resp = await client.get("/healthz", timeout=httpx.Timeout(3.0))
            healthy = resp.status_code == 200
            self._available = healthy
            return healthy
        except Exception:
            self._available = False
            return False

    def get_stats(self) -> dict[str, Any]:
        """Return connection stats."""
        return {
            "available": self._available,
            "url": self._url,
            "collection": self._collection,
            "dimension": self._dimension,
        }
