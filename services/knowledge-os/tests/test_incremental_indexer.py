"""Tests for the incremental indexer."""

import pytest

from sona_knowledge.infrastructure.incremental_indexer import (
    IncrementalIndexer,
    IndexStatus,
)


@pytest.fixture
def indexer() -> IncrementalIndexer:
    return IncrementalIndexer()


class TestIncrementalIndexer:
    """Tests for IncrementalIndexer."""

    def test_new_document_needs_indexing(self, indexer: IncrementalIndexer) -> None:
        assert indexer.needs_indexing("doc-1", "content") is True

    def test_indexed_document_does_not_need_reindexing(self, indexer: IncrementalIndexer) -> None:
        indexer.mark_indexed("doc-1", "content", chunks_count=5)
        assert indexer.needs_indexing("doc-1", "content") is False

    def test_modified_document_needs_reindexing(self, indexer: IncrementalIndexer) -> None:
        indexer.mark_indexed("doc-1", "original content", chunks_count=5)
        assert indexer.needs_indexing("doc-1", "modified content") is True

    def test_compute_hash_deterministic(self, indexer: IncrementalIndexer) -> None:
        h1 = indexer.compute_hash("hello")
        h2 = indexer.compute_hash("hello")
        assert h1 == h2

    def test_compute_hash_different_content(self, indexer: IncrementalIndexer) -> None:
        h1 = indexer.compute_hash("hello")
        h2 = indexer.compute_hash("world")
        assert h1 != h2

    def test_mark_indexed_sets_status(self, indexer: IncrementalIndexer) -> None:
        indexer.mark_indexed("doc-1", "content", chunks_count=5, kb_id="kb-1")
        assert indexer.get_status("doc-1") == IndexStatus.INDEXED

    def test_mark_failed_sets_status(self, indexer: IncrementalIndexer) -> None:
        indexer.mark_failed("doc-1", "content")
        assert indexer.get_status("doc-1") == IndexStatus.FAILED

    def test_get_status_unknown_document(self, indexer: IncrementalIndexer) -> None:
        assert indexer.get_status("nonexistent") is None

    def test_get_record(self, indexer: IncrementalIndexer) -> None:
        indexer.mark_indexed("doc-1", "content", chunks_count=10, kb_id="kb-main")
        record = indexer.get_record("doc-1")
        assert record is not None
        assert record.document_id == "doc-1"
        assert record.chunks_count == 10
        assert record.kb_id == "kb-main"

    def test_get_record_nonexistent(self, indexer: IncrementalIndexer) -> None:
        assert indexer.get_record("nonexistent") is None

    def test_get_all_records(self, indexer: IncrementalIndexer) -> None:
        indexer.mark_indexed("doc-1", "content1", chunks_count=5)
        indexer.mark_indexed("doc-2", "content2", chunks_count=3)
        records = indexer.get_all_records()
        assert len(records) == 2

    def test_remove_existing(self, indexer: IncrementalIndexer) -> None:
        indexer.mark_indexed("doc-1", "content", chunks_count=5)
        assert indexer.remove("doc-1") is True
        assert indexer.get_status("doc-1") is None

    def test_remove_nonexistent(self, indexer: IncrementalIndexer) -> None:
        assert indexer.remove("nonexistent") is False

    def test_reindex_after_remove(self, indexer: IncrementalIndexer) -> None:
        indexer.mark_indexed("doc-1", "content", chunks_count=5)
        indexer.remove("doc-1")
        assert indexer.needs_indexing("doc-1", "content") is True

    def test_failed_document_needs_reindexing(self, indexer: IncrementalIndexer) -> None:
        indexer.mark_failed("doc-1", "content")
        # Same content but was marked failed - shouldn't need reindexing
        assert indexer.needs_indexing("doc-1", "content") is False
        # Different content should need reindexing
        assert indexer.needs_indexing("doc-1", "new content") is True
