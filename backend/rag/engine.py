"""RAG Engine — orchestrates ingestion, retrieval, and context building.

The central coordinator for the knowledge engine. Provides a unified
interface for document management, search, and AI context assembly.
"""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from rag.ingestion import DocumentIngester
from rag.retrieval import HybridRetriever, RetrievalResult
from storage.repository import DocumentRecord, StorageRepository
from storage.sqlite_backend import SQLiteBackend
from vector.embeddings import EmbeddingEngine
from vector.memory_store import InMemoryVectorStore
from vector.store import VectorStore

logger = get_logger(__name__)


class RAGEngine:
    """RAG Engine — document ingestion, search, and context building.

    Coordinates:
        - Document ingestion (parse → chunk → embed → store)
        - Hybrid retrieval (semantic + keyword)
        - Context building for AI prompts
    """

    def __init__(
        self,
        storage: StorageRepository | None = None,
        vector_store: VectorStore | None = None,
        embedding_engine: EmbeddingEngine | None = None,
    ) -> None:
        self._storage = storage or SQLiteBackend()
        self._vectors = vector_store or InMemoryVectorStore()
        self._embedder = embedding_engine or EmbeddingEngine()
        self._ingester = DocumentIngester(self._embedder)
        self._retriever = HybridRetriever(self._vectors, self._storage, self._embedder)
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        """Initialize storage and vector store."""
        await self._storage.initialize()
        await self._vectors.initialize()
        self._initialized = True
        logger.info("RAG engine initialized")

    async def shutdown(self) -> None:
        """Shutdown storage connections."""
        await self._storage.shutdown()
        self._initialized = False

    async def ingest_document(
        self,
        content: str,
        title: str = "",
        source: str = "",
        doc_type: str = "text",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DocumentRecord:
        """Ingest a document into the knowledge base.

        Pipeline: Parse → Chunk → Embed → Store (both DB and vectors)

        Args:
            content: Document text content.
            title: Document title.
            source: Source path/URL.
            doc_type: Type classification.
            tags: Optional tags.
            metadata: Optional metadata.

        Returns:
            The stored DocumentRecord.
        """
        # Ingest: chunk + embed
        doc_record, vector_records = self._ingester.ingest_text(
            content=content,
            title=title,
            source=source,
            doc_type=doc_type,
            tags=tags,
            metadata=metadata,
        )

        # Store document in persistent storage
        await self._storage.save_document(doc_record)

        # Store embeddings in vector store
        if vector_records:
            await self._vectors.add(vector_records)

        logger.info(
            "Document ingested and indexed",
            doc_id=doc_record.doc_id,
            chunks=doc_record.chunk_count,
        )
        return doc_record

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.1,
    ) -> list[RetrievalResult]:
        """Search the knowledge base using hybrid retrieval.

        Combines semantic (embedding) and keyword (FTS) search.

        Args:
            query: The search query.
            top_k: Maximum results.
            min_score: Minimum relevance threshold.

        Returns:
            Ranked list of RetrievalResults.
        """
        return await self._retriever.search(query, top_k, min_score)

    async def build_context(
        self,
        query: str,
        max_tokens: int = 2000,
        top_k: int = 5,
    ) -> str:
        """Build context string for AI prompt augmentation.

        Retrieves relevant documents and formats them as context
        to inject into an LLM prompt.

        Args:
            query: The user's question/request.
            max_tokens: Token budget for context.
            top_k: Max documents to include.

        Returns:
            Formatted context string.
        """
        results = await self.search(query, top_k=top_k)
        if not results:
            return ""

        context_parts: list[str] = []
        token_count = 0

        for result in results:
            chunk_tokens = len(result.content) // 4
            if token_count + chunk_tokens > max_tokens:
                break

            source_info = f" (source: {result.source})" if result.source else ""
            context_parts.append(f"[Relevance: {result.score:.2f}{source_info}]\n{result.content}")
            token_count += chunk_tokens

        if not context_parts:
            return ""

        return "--- Retrieved Context ---\n" + "\n\n".join(context_parts) + "\n--- End Context ---"

    async def get_document(self, doc_id: str) -> DocumentRecord | None:
        """Get a document by ID."""
        return await self._storage.get_document(doc_id)

    async def list_documents(
        self, doc_type: str | None = None, limit: int = 50
    ) -> list[DocumentRecord]:
        """List documents with optional type filter."""
        return await self._storage.list_documents(doc_type, limit)

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its vector embeddings."""
        # Delete vectors first
        await self._vectors.delete_by_doc(doc_id)
        # Delete document record
        deleted = await self._storage.delete_document(doc_id)
        if deleted:
            logger.info("Document deleted", doc_id=doc_id)
        return deleted

    async def get_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        docs = await self._storage.list_documents(limit=10000)
        vector_count = await self._vectors.count()
        return {
            "documents": len(docs),
            "vectors": vector_count,
            "embedding_dimensions": self._embedder.dimensions,
        }


# Global singleton
_rag_engine: RAGEngine | None = None


def get_rag_engine() -> RAGEngine:
    """Get the global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine


async def initialize_rag() -> RAGEngine:
    """Initialize the global RAG engine."""
    engine = get_rag_engine()
    if not engine.is_initialized:
        await engine.initialize()
    return engine
