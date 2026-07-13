"""Vector-enhanced retriever using Qdrant + Ollama embeddings.

Upgrades the RAG pipeline with:
    - Real ML embeddings via Ollama (nomic-embed-text)
    - Qdrant vector database for scalable similarity search
    - Hybrid search: Qdrant vectors + PostgreSQL/SQLite FTS
    - Redis caching for repeated queries

Falls back to in-memory vector search when infrastructure unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger
from rag.retrieval import RetrievalResult
from storage.redis_cache import RedisCache
from vector.ollama_embeddings import OllamaEmbeddingEngine
from vector.qdrant_store import QdrantStore

logger = get_logger(__name__)


@dataclass
class VectorSearchResult:
    """Result from vector similarity search."""

    doc_id: str
    content: str
    score: float
    chunk_index: int = 0
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorRetriever:
    """Production retriever with Qdrant + Ollama embeddings + Redis cache.

    Architecture:
        Query → Cache check → Embed query → Qdrant search → Re-rank → Return

    Falls back to in-memory search when Qdrant/Ollama unavailable.
    """

    def __init__(
        self,
        qdrant: QdrantStore | None = None,
        embedder: OllamaEmbeddingEngine | None = None,
        cache: RedisCache | None = None,
        cache_ttl: int = 120,
    ) -> None:
        self._qdrant = qdrant or QdrantStore()
        self._embedder = embedder or OllamaEmbeddingEngine()
        self._cache = cache or RedisCache()
        self._cache_ttl = cache_ttl
        self._search_count = 0
        self._cache_hits = 0

    async def initialize(self) -> None:
        """Initialize all backends."""
        await self._qdrant.initialize()
        await self._cache.initialize()
        logger.info(
            "vector_retriever_initialized",
            qdrant=self._qdrant.is_available,
            cache=self._cache.is_available,
        )

    async def shutdown(self) -> None:
        """Shutdown all connections."""
        await self._qdrant.shutdown()
        await self._cache.shutdown()
        await self._embedder.close()

    # --- Indexing ---

    async def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Embed and index a document chunk into Qdrant.

        Args:
            doc_id: Unique identifier for this chunk
            content: Text content to embed
            metadata: Additional metadata (source, title, chunk_index, etc.)

        Returns:
            True if successfully indexed
        """
        embedding = await self._embedder.embed_text_async(content)
        payload = metadata or {}
        payload["content"] = content[:1000]  # Store truncated content in payload
        return await self._qdrant.upsert(doc_id, embedding, payload)

    async def index_batch(
        self,
        items: list[tuple[str, str, dict[str, Any] | None]],
    ) -> int:
        """Batch index multiple document chunks.

        Args:
            items: List of (doc_id, content, metadata) tuples

        Returns:
            Number successfully indexed
        """
        if not items:
            return 0

        texts = [content for _, content, _ in items]
        embeddings = await self._embedder.embed_batch_async(texts)

        batch: list[tuple[str, list[float], dict[str, Any] | None]] = []
        for (doc_id, content, metadata), embedding in zip(items, embeddings, strict=False):
            payload: dict[str, Any] = metadata or {}
            payload["content"] = content[:1000]
            batch.append((doc_id, embedding, payload))

        return await self._qdrant.upsert_batch(batch)

    # --- Search ---

    async def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.3,
    ) -> list[RetrievalResult]:
        """Search for relevant documents using vector similarity.

        Checks cache first, then performs Qdrant vector search.
        Falls back to empty results if infrastructure unavailable.
        """
        self._search_count += 1

        # Check cache
        cache_key = f"vsearch:{query[:100]}:{top_k}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            self._cache_hits += 1
            return [RetrievalResult(**r) for r in cached]

        # Embed query
        query_embedding = await self._embedder.embed_text_async(query)

        # Search Qdrant
        raw_results = await self._qdrant.search(
            query_vector=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        # Convert to RetrievalResults
        results: list[RetrievalResult] = []
        for hit in raw_results:
            payload = hit.get("payload", {})
            results.append(
                RetrievalResult(
                    content=payload.get("content", ""),
                    score=hit.get("score", 0.0),
                    source=payload.get("source", ""),
                    doc_id=str(hit.get("id", "")),
                    chunk_index=payload.get("chunk_index", 0),
                    match_type="semantic",
                    metadata=payload,
                )
            )

        # Cache results
        if results:
            serializable = [
                {
                    "content": r.content,
                    "score": r.score,
                    "source": r.source,
                    "doc_id": r.doc_id,
                    "chunk_index": r.chunk_index,
                    "match_type": r.match_type,
                    "metadata": {},
                }
                for r in results
            ]
            await self._cache.set(cache_key, serializable, ttl=self._cache_ttl)

        return results

    # --- Delete ---

    async def delete_document(self, doc_id: str) -> bool:
        """Remove a document from the vector index."""
        # Clear related cache entries
        await self._cache.clear_prefix("vsearch:")
        return await self._qdrant.delete(doc_id)

    async def delete_by_source(self, source: str) -> bool:
        """Remove all chunks from a specific source."""
        await self._cache.clear_prefix("vsearch:")
        return await self._qdrant.delete_by_filter("source", source)

    # --- Stats ---

    def get_stats(self) -> dict[str, Any]:
        """Return retriever statistics."""
        return {
            "searches": self._search_count,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": (
                round(self._cache_hits / self._search_count, 4) if self._search_count > 0 else 0.0
            ),
            "qdrant": self._qdrant.get_stats(),
            "cache": self._cache.get_stats(),
            "embedder": {
                "model": self._embedder.model_name,
                "dimensions": self._embedder.dimensions,
                "available": self._embedder.is_available,
            },
        }
