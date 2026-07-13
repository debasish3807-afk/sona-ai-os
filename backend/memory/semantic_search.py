"""Semantic search combining embeddings with vector store."""

from __future__ import annotations

from config.logging import get_logger
from memory.embeddings import EmbeddingProvider
from memory.vector_store import VectorStore

logger = get_logger(__name__)


class SemanticSearch:
    """Combines embedding + vector store for semantic memory retrieval."""

    def __init__(
        self,
        embedding: EmbeddingProvider,
        store: VectorStore,
    ) -> None:
        self._embedding = embedding
        self._store = store
        self._metadata: dict[str, dict] = {}

    async def index(
        self,
        doc_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        """Index a document for semantic search."""
        vector = await self._embedding.embed(content)
        self._store.add(doc_id, vector, metadata)
        self._metadata[doc_id] = metadata or {}
        logger.debug("document_indexed", doc_id=doc_id)

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Search for semantically similar documents.

        Returns list of dicts with doc_id, score, and metadata.
        """
        query_vector = await self._embedding.embed(query)
        results = self._store.search(query_vector, top_k=top_k)

        return [
            {
                "doc_id": doc_id,
                "score": score,
                "metadata": self._metadata.get(doc_id, {}),
            }
            for doc_id, score in results
        ]

    async def index_batch(
        self,
        items: list[tuple[str, str, dict | None]],
    ) -> None:
        """Index multiple documents at once.

        Args:
            items: List of (doc_id, content, metadata) tuples.
        """
        texts = [content for _, content, _ in items]
        vectors = await self._embedding.embed_batch(texts)

        for (doc_id, _, metadata), vector in zip(items, vectors, strict=True):
            self._store.add(doc_id, vector, metadata)
            self._metadata[doc_id] = metadata or {}

        logger.debug("batch_indexed", count=len(items))

    def remove(self, doc_id: str) -> bool:
        """Remove a document from the search index."""
        self._metadata.pop(doc_id, None)
        return self._store.remove(doc_id)
