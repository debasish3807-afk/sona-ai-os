"""Main entry point for the knowledge system."""

from __future__ import annotations

from config.logging import get_logger
from knowledge.chunking import ChunkingEngine
from knowledge.document_processor import DocumentProcessor
from knowledge.knowledge_search import KnowledgeSearch
from knowledge.knowledge_store import KnowledgeStore
from knowledge.schemas import Document, DocumentType, SearchResult

logger = get_logger(__name__)


class KnowledgeEngine:
    """Main entry point for the knowledge system."""

    def __init__(self) -> None:
        self._chunking = ChunkingEngine()
        self._processor = DocumentProcessor(self._chunking)
        self._store = KnowledgeStore()
        self._search = KnowledgeSearch(self._store)

    async def ingest(
        self,
        title: str,
        content: str,
        doc_type: str = "txt",
        source: str = "",
    ) -> str:
        """Ingest a document into the knowledge base. Returns doc_id."""
        dtype = DocumentType(doc_type)

        if dtype == DocumentType.MARKDOWN:
            doc = self._processor.process_markdown(title, content, source)
        elif dtype == DocumentType.HTML:
            doc = self._processor.process_html(title, content, source)
        else:
            doc = self._processor.process_text(title, content, source)

        # Store document and its chunks
        doc_id = self._store.add(doc)
        chunks = self._chunking.chunk_document(doc)
        self._store.store_chunks(doc_id, chunks)

        # Index for search
        await self._search.index_document(doc)

        logger.info("document_ingested", doc_id=doc_id, title=title)
        return doc_id

    async def ingest_url(self, url: str, title: str = "") -> str:
        """Ingest a URL placeholder into the knowledge base."""
        doc = self._processor.process_url(url, title)
        doc_id = self._store.add(doc)
        logger.info("url_ingested", doc_id=doc_id, url=url)
        return doc_id

    async def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """Search the knowledge base."""
        return await self._search.search(query, top_k=top_k)

    async def get_document(self, doc_id: str) -> Document | None:
        """Retrieve a document by ID."""
        return self._store.get(doc_id)

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the knowledge base."""
        return self._store.delete(doc_id)

    def get_stats(self) -> dict:
        """Return knowledge engine statistics."""
        return {
            "documents": self._store.count,
            "processor": self._processor.get_stats(),
        }
