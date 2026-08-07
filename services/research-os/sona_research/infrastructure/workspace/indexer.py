"""Workspace document indexer.

Processes and indexes workspace documents by chunking content,
generating document IDs, and tracking indexed documents.
"""

import hashlib
from datetime import UTC, datetime

import structlog

from sona_research.domain.events import WorkspaceIndexedEvent
from sona_research.domain.workspace_models import (
    IndexedDocument,
    WorkspaceDocument,
)
from sona_research.infrastructure.workspace.extractors import ContentExtractors

logger = structlog.get_logger()


def _generate_doc_id(path: str) -> str:
    """Generate a deterministic document ID from the path."""
    return hashlib.sha256(path.encode()).hexdigest()[:16]


def _chunk_content(content: str, chunk_size: int = 500) -> list[str]:
    """Split content into chunks of approximately chunk_size characters.

    Splits on paragraph boundaries where possible.

    Args:
        content: Text content to chunk.
        chunk_size: Target chunk size in characters.

    Returns:
        List of content chunks.
    """
    if not content:
        return []

    paragraphs = content.split("\n\n")
    chunks: list[str] = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


class WorkspaceIndexer:
    """Index workspace documents for knowledge retrieval."""

    def __init__(self, chunk_size: int = 500) -> None:
        """Initialize the workspace indexer.

        Args:
            chunk_size: Target size for content chunks.
        """
        self._chunk_size = chunk_size
        self._indexed: dict[str, IndexedDocument] = {}
        self._chunks: dict[str, list[str]] = {}
        self._events: list[WorkspaceIndexedEvent] = []

    @property
    def indexed_documents(self) -> dict[str, IndexedDocument]:
        """Access the indexed documents store."""
        return self._indexed

    @property
    def events(self) -> list[WorkspaceIndexedEvent]:
        """Access emitted events."""
        return self._events

    def get_chunks(self, doc_id: str) -> list[str]:
        """Get chunks for an indexed document.

        Args:
            doc_id: Document ID to retrieve chunks for.

        Returns:
            List of content chunks, or empty if not found.
        """
        return self._chunks.get(doc_id, [])

    async def index_document(self, document: WorkspaceDocument) -> IndexedDocument:
        """Index a single workspace document.

        Extracts text, chunks it, and stores the indexed record.

        Args:
            document: The workspace document to index.

        Returns:
            The indexed document record.
        """
        logger.info("workspace_indexer.index_document", path=document.path)

        # Extract text content
        extracted = await ContentExtractors.extract(document.content, document.format)

        # Chunk the content
        chunks = _chunk_content(extracted, self._chunk_size)

        # Generate document ID
        doc_id = _generate_doc_id(document.path)

        # Store the indexed document
        indexed = IndexedDocument(
            doc_id=doc_id,
            path=document.path,
            title=document.title,
            format=document.format,
            chunk_count=len(chunks),
            indexed_at=datetime.now(UTC).isoformat(),
            metadata=document.metadata,
        )

        self._indexed[doc_id] = indexed
        self._chunks[doc_id] = chunks

        return indexed

    async def index_batch(self, documents: list[WorkspaceDocument]) -> list[IndexedDocument]:
        """Index multiple documents and emit a workspace indexed event.

        Args:
            documents: List of documents to index.

        Returns:
            List of indexed document records.
        """
        logger.info("workspace_indexer.index_batch", count=len(documents))
        results: list[IndexedDocument] = []

        for doc in documents:
            indexed = await self.index_document(doc)
            results.append(indexed)

        # Emit event
        if results:
            path = results[0].path.rsplit("/", 1)[0] if "/" in results[0].path else "/"
            event = WorkspaceIndexedEvent(
                path=path,
                documents_indexed=len(results),
            )
            self._events.append(event)

        return results

    async def search(self, query: str) -> list[IndexedDocument]:
        """Search indexed documents by matching query terms.

        Args:
            query: Search query string.

        Returns:
            List of matching indexed documents.
        """
        query_lower = query.lower()
        results: list[IndexedDocument] = []

        for doc_id, indexed in self._indexed.items():
            # Check title match
            if query_lower in indexed.title.lower():
                results.append(indexed)
                continue

            # Check chunk content match
            chunks = self._chunks.get(doc_id, [])
            for chunk in chunks:
                if query_lower in chunk.lower():
                    results.append(indexed)
                    break

        return results

    async def remove_document(self, path: str) -> bool:
        """Remove a document from the index.

        Args:
            path: Path of the document to remove.

        Returns:
            True if the document was found and removed.
        """
        doc_id = _generate_doc_id(path)
        if doc_id in self._indexed:
            del self._indexed[doc_id]
            self._chunks.pop(doc_id, None)
            return True
        return False

    async def get_stats(self) -> dict[str, int]:
        """Get indexing statistics.

        Returns:
            Dictionary with document count, total chunks, and format breakdown.
        """
        format_counts: dict[str, int] = {}
        total_chunks = 0

        for indexed in self._indexed.values():
            fmt = indexed.format.value
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
            total_chunks += indexed.chunk_count

        return {
            "total_documents": len(self._indexed),
            "total_chunks": total_chunks,
            **{f"format_{k}": v for k, v in format_counts.items()},
        }
