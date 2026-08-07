"""Incremental indexing for Knowledge OS.

Tracks which documents have been indexed, detects changes via content hashing,
and only re-indexes modified documents.
"""

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum

import structlog

logger = structlog.get_logger()


class IndexStatus(StrEnum):
    """Status of a document's indexing state."""

    PENDING = "pending"
    INDEXED = "indexed"
    MODIFIED = "modified"
    FAILED = "failed"


@dataclass
class IndexRecord:
    """Tracks indexing state for a document."""

    document_id: str
    content_hash: str
    status: IndexStatus = IndexStatus.PENDING
    chunks_count: int = 0
    kb_id: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


class IncrementalIndexer:
    """Tracks document indexing state for change detection.

    Uses content hashing to determine which documents need re-indexing.
    Only processes changed or new documents.
    """

    def __init__(self) -> None:
        """Initialize the incremental indexer."""
        self._index_records: dict[str, IndexRecord] = {}

    def compute_hash(self, content: str) -> str:
        """Compute a content hash for change detection.

        Args:
            content: Document content to hash.

        Returns:
            SHA-256 hex digest of the content.
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def needs_indexing(self, document_id: str, content: str) -> bool:
        """Check if a document needs (re-)indexing.

        Args:
            document_id: The document identifier.
            content: Current document content.

        Returns:
            True if the document is new or content has changed.
        """
        new_hash = self.compute_hash(content)

        if document_id not in self._index_records:
            return True

        record = self._index_records[document_id]
        return record.content_hash != new_hash

    def mark_indexed(
        self,
        document_id: str,
        content: str,
        chunks_count: int,
        kb_id: str = "",
    ) -> None:
        """Mark a document as successfully indexed.

        Args:
            document_id: The document identifier.
            content: The document content (for hash).
            chunks_count: Number of chunks produced.
            kb_id: Knowledge base identifier.
        """
        self._index_records[document_id] = IndexRecord(
            document_id=document_id,
            content_hash=self.compute_hash(content),
            status=IndexStatus.INDEXED,
            chunks_count=chunks_count,
            kb_id=kb_id,
        )
        logger.debug(
            "document_marked_indexed",
            document_id=document_id,
            chunks_count=chunks_count,
        )

    def mark_failed(self, document_id: str, content: str) -> None:
        """Mark a document as failed to index.

        Args:
            document_id: The document identifier.
            content: The document content (for hash).
        """
        self._index_records[document_id] = IndexRecord(
            document_id=document_id,
            content_hash=self.compute_hash(content),
            status=IndexStatus.FAILED,
        )
        logger.warning("document_indexing_failed", document_id=document_id)

    def get_status(self, document_id: str) -> IndexStatus | None:
        """Get the indexing status of a document.

        Args:
            document_id: The document identifier.

        Returns:
            IndexStatus or None if not tracked.
        """
        record = self._index_records.get(document_id)
        return record.status if record else None

    def get_record(self, document_id: str) -> IndexRecord | None:
        """Get the full index record for a document.

        Args:
            document_id: The document identifier.

        Returns:
            IndexRecord or None if not tracked.
        """
        return self._index_records.get(document_id)

    def get_all_records(self) -> list[IndexRecord]:
        """Get all index records.

        Returns:
            List of all IndexRecord instances.
        """
        return list(self._index_records.values())

    def remove(self, document_id: str) -> bool:
        """Remove a document from the index tracker.

        Args:
            document_id: The document identifier.

        Returns:
            True if removed, False if not found.
        """
        if document_id in self._index_records:
            del self._index_records[document_id]
            return True
        return False
