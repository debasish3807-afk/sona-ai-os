"""Knowledge Manager - top-level orchestrator for Knowledge OS.

Implements the KnowledgeBasePort interface, coordinating the full
RAG pipeline: ingest (load → chunk → embed → store) and
query (embed → search → hybrid score → rerank → cite).
"""

from typing import Any

import structlog

from sona_knowledge.application.ports import KnowledgeBasePort
from sona_knowledge.domain.citations import Citation
from sona_knowledge.domain.events import (
    DocumentDeletedEvent,
    DocumentIngestedEvent,
    QueryExecutedEvent,
)
from sona_knowledge.domain.models import (
    Document,
    DocumentChunk,
    RAGQuery,
    RAGResult,
)
from sona_knowledge.infrastructure.chunking.recursive import RecursiveChunker
from sona_knowledge.infrastructure.citation_engine import CitationEngine
from sona_knowledge.infrastructure.embedding_service import EmbeddingService
from sona_knowledge.infrastructure.hybrid_search import HybridSearch
from sona_knowledge.infrastructure.incremental_indexer import IncrementalIndexer
from sona_knowledge.infrastructure.metadata_extractor import MetadataExtractor
from sona_knowledge.infrastructure.reranker import Reranker
from sona_knowledge.infrastructure.retriever import Retriever
from sona_knowledge.infrastructure.vector_store import VectorStore

logger = structlog.get_logger()


class KnowledgeManager(KnowledgeBasePort):
    """Top-level orchestrator implementing the Knowledge OS RAG pipeline.

    Coordinates:
    - ingest(): load → extract metadata → chunk → embed → store
    - query(): embed query → vector search → hybrid score → rerank → cite
    - list_knowledge_bases(): enumerate indexed collections
    - delete_document(): remove from store
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        retriever: Retriever,
        hybrid_search: HybridSearch,
        reranker: Reranker,
        citation_engine: CitationEngine,
        metadata_extractor: MetadataExtractor,
        incremental_indexer: IncrementalIndexer,
        chunker: RecursiveChunker | None = None,
    ) -> None:
        """Initialize the Knowledge Manager.

        Args:
            embedding_service: Service for generating embeddings.
            vector_store: Vector storage backend.
            retriever: Retrieval pipeline.
            hybrid_search: Hybrid search combining semantic + keyword.
            reranker: Result re-ranking module.
            citation_engine: Citation generation engine.
            metadata_extractor: Document metadata extractor.
            incremental_indexer: Change detection for documents.
            chunker: Text chunking strategy (defaults to RecursiveChunker).
        """
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._retriever = retriever
        self._hybrid_search = hybrid_search
        self._reranker = reranker
        self._citation_engine = citation_engine
        self._metadata_extractor = metadata_extractor
        self._incremental_indexer = incremental_indexer
        self._chunker = chunker or RecursiveChunker()
        self._knowledge_bases: dict[str, dict[str, Any]] = {}
        self._documents: dict[str, Document] = {}
        self._events: list[object] = []

    @property
    def events(self) -> list[object]:
        """Access emitted domain events."""
        return self._events

    async def ingest(self, document: Document, kb_id: str) -> str:
        """Ingest a document into a knowledge base.

        Pipeline: extract metadata → chunk → embed → store

        Args:
            document: The document to ingest.
            kb_id: The target knowledge base identifier.

        Returns:
            The document ID confirming successful ingestion.
        """
        logger.info(
            "ingesting_document",
            document_id=document.id,
            kb_id=kb_id,
            doc_type=document.doc_type,
        )

        # Check if document needs re-indexing
        if not self._incremental_indexer.needs_indexing(document.id, document.content):
            logger.info("document_already_indexed", document_id=document.id)
            return document.id

        # Extract metadata
        metadata = self._metadata_extractor.extract(document.content)

        # Chunk the document
        chunks_text = self._chunker.chunk(document.content)

        if not chunks_text:
            logger.warning("no_chunks_produced", document_id=document.id)
            return document.id

        # Generate embeddings for all chunks
        embeddings = await self._embedding_service.embed_batch(chunks_text)

        # Store chunks in vector store
        records: list[tuple[str, list[float], dict[str, Any], str]] = []
        doc_chunks: list[DocumentChunk] = []

        for i, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings, strict=True)):
            chunk_id = f"{document.id}_chunk_{i}"
            chunk_metadata: dict[str, Any] = {
                "document_id": document.id,
                "kb_id": kb_id,
                "chunk_index": i,
                "title": document.title,
                "doc_type": str(document.doc_type),
                "source_url": document.source_url or "",
                **{k: v for k, v in metadata.items() if k in ("keywords", "language")},
            }
            records.append((chunk_id, embedding, chunk_metadata, chunk_text))
            doc_chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=document.id,
                    content=chunk_text,
                    embedding=embedding,
                    chunk_index=i,
                    metadata=chunk_metadata,
                )
            )

        await self._vector_store.upsert_batch(records)

        # Track document
        self._documents[document.id] = document
        self._incremental_indexer.mark_indexed(
            document_id=document.id,
            content=document.content,
            chunks_count=len(doc_chunks),
            kb_id=kb_id,
        )

        # Register knowledge base
        if kb_id not in self._knowledge_bases:
            self._knowledge_bases[kb_id] = {
                "id": kb_id,
                "documents_count": 0,
                "chunks_count": 0,
            }
        self._knowledge_bases[kb_id]["documents_count"] = (
            int(self._knowledge_bases[kb_id]["documents_count"]) + 1
        )
        self._knowledge_bases[kb_id]["chunks_count"] = int(
            self._knowledge_bases[kb_id]["chunks_count"]
        ) + len(doc_chunks)

        # Emit domain event
        self._events.append(
            DocumentIngestedEvent(
                document_id=document.id,
                kb_id=kb_id,
                chunks_count=len(doc_chunks),
                doc_type=str(document.doc_type),
            )
        )

        logger.info(
            "document_ingested",
            document_id=document.id,
            kb_id=kb_id,
            chunks_count=len(doc_chunks),
        )
        return document.id

    async def query(self, rag_query: RAGQuery) -> RAGResult:
        """Query a knowledge base using the full RAG pipeline.

        Pipeline: embed query → vector search → hybrid score → rerank → cite

        Args:
            rag_query: The RAG query parameters.

        Returns:
            A RAGResult with relevant chunks and augmented context.
        """
        logger.info(
            "executing_query",
            query=rag_query.query[:50],
            kb_id=rag_query.knowledge_base_id,
            top_k=rag_query.top_k,
        )

        # Step 1: Retrieve via vector similarity
        semantic_results = await self._retriever.retrieve(
            query=rag_query.query,
            top_k=rag_query.top_k * 2,  # Get extra for reranking
            min_similarity=rag_query.min_similarity,
            kb_id=rag_query.knowledge_base_id,
        )

        if not semantic_results:
            self._events.append(
                QueryExecutedEvent(
                    query=rag_query.query,
                    results_count=0,
                    confidence=0.0,
                )
            )
            return RAGResult(
                chunks=[],
                augmented_context="",
                sources=[],
                confidence=0.0,
            )

        # Step 2: Hybrid search (combine semantic + keyword)
        hybrid_results = self._hybrid_search.search(
            query=rag_query.query,
            semantic_results=semantic_results,
            corpus_size=self._vector_store.size,
        )

        # Step 3: Rerank (if enabled)
        if rag_query.rerank:
            hybrid_results = self._reranker.rerank(rag_query.query, hybrid_results)

        # Limit to top_k
        hybrid_results = hybrid_results[: rag_query.top_k]

        # Step 4: Generate citations (for attribution tracking)
        self._citation_engine.generate_citations(hybrid_results)

        # Step 5: Format augmented context
        augmented_context = self._citation_engine.format_context(hybrid_results)

        # Build result chunks
        result_chunks: list[DocumentChunk] = []
        sources: list[str] = []

        for result in hybrid_results:
            chunk_id = result.id
            doc_id = str(result.metadata.get("document_id", ""))
            embedding = await self._embedding_service.embed(result.content)
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=doc_id,
                content=result.content,
                embedding=embedding,
                chunk_index=int(result.metadata.get("chunk_index", 0)),
                metadata=result.metadata,
            )
            result_chunks.append(chunk)
            if doc_id and doc_id not in sources:
                sources.append(doc_id)

        confidence = (
            sum(r.combined_score for r in hybrid_results) / len(hybrid_results)
            if hybrid_results
            else 0.0
        )

        # Emit domain event
        self._events.append(
            QueryExecutedEvent(
                query=rag_query.query,
                results_count=len(result_chunks),
                confidence=confidence,
            )
        )

        logger.info(
            "query_executed",
            results_count=len(result_chunks),
            confidence=confidence,
        )

        return RAGResult(
            chunks=result_chunks,
            augmented_context=augmented_context,
            sources=sources,
            confidence=confidence,
        )

    async def list_knowledge_bases(self, user_id: str) -> list[dict[str, Any]]:
        """List available knowledge bases.

        Args:
            user_id: The ID of the user (for access filtering).

        Returns:
            A list of dictionaries describing each knowledge base.
        """
        return list(self._knowledge_bases.values())

    async def delete_document(self, document_id: str) -> bool:
        """Remove a document and all its chunks from the knowledge base.

        Args:
            document_id: The ID of the document to delete.

        Returns:
            True if deleted successfully.
        """
        deleted_count = await self._vector_store.delete_by_metadata({"document_id": document_id})
        self._incremental_indexer.remove(document_id)
        self._documents.pop(document_id, None)

        if deleted_count > 0:
            self._events.append(DocumentDeletedEvent(document_id=document_id))
            logger.info(
                "document_deleted",
                document_id=document_id,
                chunks_deleted=deleted_count,
            )
            return True

        return False

    def get_citations(self) -> list[Citation]:
        """Get citations from the last query (convenience accessor)."""
        return []  # Citations are returned as part of the query context
