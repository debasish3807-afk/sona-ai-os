"""Hybrid retrieval — combines semantic and keyword search.

Implements a hybrid search strategy that merges vector similarity
results with full-text keyword matches, then ranks by a combined score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger
from storage.repository import StorageRepository
from vector.embeddings import EmbeddingEngine
from vector.store import VectorStore

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """A single retrieval result with combined scoring."""

    content: str
    score: float  # Combined relevance score
    source: str = ""
    doc_id: str = ""
    chunk_index: int = 0
    match_type: str = "semantic"  # semantic, keyword, hybrid
    metadata: dict[str, Any] = field(default_factory=dict)


class HybridRetriever:
    """Combines semantic search with keyword search for best results.

    Strategy:
        1. Semantic search via vector store (embedding similarity)
        2. Keyword search via storage full-text search (FTS5)
        3. Merge and re-rank by combined score
        4. Deduplicate overlapping results
    """

    def __init__(
        self,
        vector_store: VectorStore,
        storage: StorageRepository,
        embedding_engine: EmbeddingEngine | None = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> None:
        self._vectors = vector_store
        self._storage = storage
        self._embedder = embedding_engine or EmbeddingEngine()
        self._semantic_weight = semantic_weight
        self._keyword_weight = keyword_weight

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.1,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Perform hybrid search combining semantic and keyword retrieval.

        Args:
            query: The search query text.
            top_k: Maximum results to return.
            min_score: Minimum relevance threshold.
            filter_metadata: Optional metadata filters.

        Returns:
            Ranked list of RetrievalResults.
        """
        # Semantic search
        query_embedding = self._embedder.embed_text(query)
        semantic_results = await self._vectors.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,
            min_score=0.0,
            filter_metadata=filter_metadata,
        )

        # Keyword search
        keyword_docs = await self._storage.search_documents(query, limit=top_k)
        keyword_mems = await self._storage.search_memories(query, limit=top_k)

        # Build result map (deduplicate by content hash)
        seen_content: set[str] = set()
        results: list[RetrievalResult] = []

        # Add semantic results
        for sr in semantic_results:
            content_key = sr.record.content[:100]
            if content_key in seen_content:
                continue
            seen_content.add(content_key)
            results.append(
                RetrievalResult(
                    content=sr.record.content,
                    score=sr.score * self._semantic_weight,
                    source=sr.record.metadata.get("source", ""),
                    doc_id=sr.record.doc_id,
                    chunk_index=sr.record.chunk_index,
                    match_type="semantic",
                    metadata=sr.record.metadata,
                )
            )

        # Add keyword results from documents
        for doc in keyword_docs:
            content_key = doc.content[:100]
            if content_key in seen_content:
                # Boost existing result
                for r in results:
                    if r.content[:100] == content_key:
                        r.score += self._keyword_weight * 0.8
                        r.match_type = "hybrid"
                        break
                continue
            seen_content.add(content_key)
            results.append(
                RetrievalResult(
                    content=doc.content[:2000],
                    score=self._keyword_weight * 0.8,
                    source=doc.source,
                    doc_id=doc.doc_id,
                    match_type="keyword",
                    metadata={"title": doc.title, "doc_type": doc.doc_type},
                )
            )

        # Add keyword results from memories
        for mem in keyword_mems:
            content_key = mem.content[:100]
            if content_key in seen_content:
                continue
            seen_content.add(content_key)
            results.append(
                RetrievalResult(
                    content=mem.content,
                    score=self._keyword_weight * 0.6,
                    source=f"memory:{mem.memory_type}",
                    match_type="keyword",
                    metadata={"memory_type": mem.memory_type, "session_id": mem.session_id},
                )
            )

        # Sort by score and filter
        results.sort(key=lambda r: r.score, reverse=True)
        results = [r for r in results if r.score >= min_score]

        return results[:top_k]
