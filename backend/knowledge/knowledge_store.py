"""In-memory knowledge document store."""

from __future__ import annotations

from config.logging import get_logger
from knowledge.schemas import Chunk, Document

logger = get_logger(__name__)


class KnowledgeStore:
    """Stores and retrieves knowledge documents."""

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}
        self._chunks: dict[str, list[Chunk]] = {}

    def add(self, doc: Document) -> str:
        """Add a document to the store. Returns doc_id."""
        self._documents[doc.doc_id] = doc
        logger.info("document_added", doc_id=doc.doc_id, title=doc.title)
        return doc.doc_id

    def get(self, doc_id: str) -> Document | None:
        """Retrieve a document by ID."""
        return self._documents.get(doc_id)

    def list_all(self, limit: int = 50) -> list[Document]:
        """List all documents, limited by count."""
        docs = list(self._documents.values())
        docs.sort(key=lambda d: d.created_at, reverse=True)
        return docs[:limit]

    def delete(self, doc_id: str) -> bool:
        """Delete a document and its chunks."""
        if doc_id not in self._documents:
            return False
        del self._documents[doc_id]
        self._chunks.pop(doc_id, None)
        logger.info("document_deleted", doc_id=doc_id)
        return True

    def search(self, query: str, limit: int = 10) -> list[Document]:
        """Simple text search across document content."""
        query_lower = query.lower()
        results: list[Document] = []

        for doc in self._documents.values():
            if query_lower in doc.content.lower() or query_lower in doc.title.lower():
                results.append(doc)
                if len(results) >= limit:
                    break

        return results

    def get_chunks(self, doc_id: str) -> list[Chunk]:
        """Get all chunks for a document."""
        return self._chunks.get(doc_id, [])

    def store_chunks(self, doc_id: str, chunks: list[Chunk]) -> None:
        """Store chunks for a document."""
        self._chunks[doc_id] = chunks

    @property
    def count(self) -> int:
        """Number of documents in the store."""
        return len(self._documents)
