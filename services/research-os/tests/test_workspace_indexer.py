"""Tests for workspace document indexer."""

import pytest

from sona_research.domain.workspace_models import DocumentFormat, WorkspaceDocument
from sona_research.infrastructure.workspace.indexer import (
    WorkspaceIndexer,
    _chunk_content,
    _generate_doc_id,
)


class TestGenerateDocId:
    def test_deterministic(self) -> None:
        assert _generate_doc_id("/a/b.md") == _generate_doc_id("/a/b.md")

    def test_different_paths_different_ids(self) -> None:
        assert _generate_doc_id("/a") != _generate_doc_id("/b")

    def test_returns_16_chars(self) -> None:
        assert len(_generate_doc_id("/test")) == 16


class TestChunkContent:
    def test_empty_content(self) -> None:
        assert _chunk_content("") == []

    def test_small_content_single_chunk(self) -> None:
        chunks = _chunk_content("Small text", chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0] == "Small text"

    def test_paragraph_splitting(self) -> None:
        text = "Para 1\n\nPara 2\n\nPara 3"
        chunks = _chunk_content(text, chunk_size=15)
        assert len(chunks) >= 2

    def test_respects_chunk_size(self) -> None:
        text = "\n\n".join(f"Paragraph {i} content" for i in range(20))
        chunks = _chunk_content(text, chunk_size=50)
        for chunk in chunks:
            assert len(chunk) <= 100  # Allow some overflow for paragraph boundary


class TestWorkspaceIndexer:
    @pytest.fixture
    def indexer(self) -> WorkspaceIndexer:
        return WorkspaceIndexer(chunk_size=100)

    @pytest.mark.asyncio
    async def test_index_single_document(self, indexer: WorkspaceIndexer) -> None:
        doc = WorkspaceDocument(
            path="/docs/readme.md",
            title="Readme",
            content="# Welcome\n\nThis is a test document.",
            format=DocumentFormat.MARKDOWN,
        )
        indexed = await indexer.index_document(doc)
        assert indexed.path == "/docs/readme.md"
        assert indexed.title == "Readme"
        assert indexed.format == DocumentFormat.MARKDOWN
        assert indexed.chunk_count > 0

    @pytest.mark.asyncio
    async def test_index_stores_chunks(self, indexer: WorkspaceIndexer) -> None:
        doc = WorkspaceDocument(
            path="/doc.md", title="Doc", content="Hello world", format=DocumentFormat.MARKDOWN
        )
        indexed = await indexer.index_document(doc)
        chunks = indexer.get_chunks(indexed.doc_id)
        assert len(chunks) == indexed.chunk_count

    @pytest.mark.asyncio
    async def test_index_batch(self, indexer: WorkspaceIndexer) -> None:
        docs = [
            WorkspaceDocument(
                path=f"/doc{i}.md",
                title=f"Doc {i}",
                content=f"Content {i}",
                format=DocumentFormat.MARKDOWN,
            )
            for i in range(5)
        ]
        results = await indexer.index_batch(docs)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_index_batch_emits_event(self, indexer: WorkspaceIndexer) -> None:
        docs = [
            WorkspaceDocument(
                path="/a/doc.md", title="D", content="C", format=DocumentFormat.MARKDOWN
            )
        ]
        await indexer.index_batch(docs)
        assert len(indexer.events) == 1
        assert indexer.events[0].documents_indexed == 1

    @pytest.mark.asyncio
    async def test_search_by_title(self, indexer: WorkspaceIndexer) -> None:
        doc = WorkspaceDocument(
            path="/notes.md",
            title="Meeting Notes",
            content="Discussion about X",
            format=DocumentFormat.MARKDOWN,
        )
        await indexer.index_document(doc)
        results = await indexer.search("Meeting")
        assert len(results) == 1
        assert results[0].title == "Meeting Notes"

    @pytest.mark.asyncio
    async def test_search_by_content(self, indexer: WorkspaceIndexer) -> None:
        doc = WorkspaceDocument(
            path="/guide.md",
            title="Guide",
            content="How to deploy applications",
            format=DocumentFormat.TEXT,
        )
        await indexer.index_document(doc)
        results = await indexer.search("deploy")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_no_match(self, indexer: WorkspaceIndexer) -> None:
        doc = WorkspaceDocument(
            path="/a.md", title="A", content="Hello", format=DocumentFormat.TEXT
        )
        await indexer.index_document(doc)
        results = await indexer.search("xyz_not_found")
        assert results == []

    @pytest.mark.asyncio
    async def test_remove_document(self, indexer: WorkspaceIndexer) -> None:
        doc = WorkspaceDocument(
            path="/del.md", title="Del", content="Delete me", format=DocumentFormat.TEXT
        )
        await indexer.index_document(doc)
        removed = await indexer.remove_document("/del.md")
        assert removed is True
        results = await indexer.search("Delete")
        assert results == []

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, indexer: WorkspaceIndexer) -> None:
        removed = await indexer.remove_document("/nope.md")
        assert removed is False

    @pytest.mark.asyncio
    async def test_get_stats(self, indexer: WorkspaceIndexer) -> None:
        docs = [
            WorkspaceDocument(
                path="/a.md",
                title="A",
                content="Hello world content",
                format=DocumentFormat.MARKDOWN,
            ),
            WorkspaceDocument(
                path="/b.py",
                title="B",
                content="# A python comment\ndef my_func(): pass",
                format=DocumentFormat.SOURCE_CODE,
            ),
        ]
        await indexer.index_batch(docs)
        stats = await indexer.get_stats()
        assert stats["total_documents"] == 2
        assert stats["total_chunks"] >= 2
