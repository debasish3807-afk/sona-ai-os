"""Knowledge search combining text and semantic search."""

from __future__ import annotations

from config.logging import get_logger
from knowledge.knowledge_store import KnowledgeStore
from knowledge.schemas import Citation, Document, SearchResult
from memory.semantic_search import SemanticSearch

logger = get_logger(__name__)


class KnowledgeSearch:
    """Combines text search + semantic search over knowledge base."""

    def __init__(
        self,
        store: KnowledgeStore,
        semantic: SemanticSearch | None = None,
    ) -> None:
        self._store = store
        self._semantic = semantic

    async def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """Search across the knowledge base."""
        results: list[SearchResult] = []

        # Text search over documents
        docs = self._store.search(query, limit=top_k)
        for doc in docs:
            chunks = self._store.get_chunks(doc.doc_id)
            if chunks:
                for chunk in chunks[:3]:
                    results.append(
                        SearchResult(  # type: ignore
                            chunk_id=chunk.chunk_id,
                            doc_id=doc.doc_id,
                            content=chunk.content,
                            score=1.0,
                            metadata=chunk.metadata,
                        )
                    )
            else:
                results.append(
                    SearchResult(  # type: ignore
                        chunk_id="",
                        doc_id=doc.doc_id,
                        content=doc.content[:500],
                        score=0.8,
                        metadata={"title": doc.title},
                    )
                )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def search_with_citations(
        self, query: str, top_k: int = 5
    ) -> tuple[list[SearchResult], list[Citation]]:
        """Search and generate citations for results."""
        results = await self.search(query, top_k=top_k)
        citations: list[Citation] = []

        for result in results:
            doc = self._store.get(result.doc_id)
            if doc:
                citations.append(
                    Citation(  # type: ignore
                        source=doc.source or doc.title,
                        title=doc.title,
                        chunk_id=result.chunk_id,  # type: ignore
                        relevance=result.score,
                    )
                )

        return results, citations

    async def index_document(self, doc: Document) -> None:
        """Index all chunks of a document for semantic search."""
        chunks = self._store.get_chunks(doc.doc_id)
        if not chunks:
            logger.debug("no_chunks_to_index", doc_id=doc.doc_id)
            return

        if self._semantic:
            for chunk in chunks:
                await self._semantic.index(
                    doc_id=chunk.chunk_id,
                    content=chunk.content,
                    metadata={
                        "chunk_id": chunk.chunk_id,
                        "doc_id": chunk.doc_id,
                        **chunk.metadata,
                    },
                )
            logger.info(
                "document_indexed",
                doc_id=doc.doc_id,
                chunk_count=len(chunks),
            )
