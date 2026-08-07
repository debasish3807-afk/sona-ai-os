"""Tests for workspace to knowledge integration."""

import pytest

from sona_research.domain.workspace_models import DocumentFormat
from sona_research.infrastructure.workspace.indexer import WorkspaceIndexer
from sona_research.infrastructure.workspace.scanner import WorkspaceScanner


@pytest.fixture
def populated_workspace() -> WorkspaceScanner:
    """Create a populated workspace for testing."""
    scanner = WorkspaceScanner()
    scanner.add_file("/project/README.md", "# My Project\n\nA great project description.")
    scanner.add_file(
        "/project/docs/architecture.md", "## Architecture\n\nMicroservices based design."
    )
    scanner.add_file("/project/docs/api.md", "## API Reference\n\nREST endpoints documentation.")
    scanner.add_file(
        "/project/src/main.py", '"""Main entry point."""\n\ndef main():\n    # Start app\n    pass'
    )
    scanner.add_file(
        "/project/src/auth.py",
        '"""Auth module."""\n\nclass AuthService:\n    # Handle authentication\n    pass',
    )
    scanner.add_file(
        "/project/config.yaml", "app:\n  name: myproject\n  port: 8080\n  debug: false"
    )
    scanner.add_file(
        "/project/package.json",
        '{"name": "myproject", "version": "1.0.0", "scripts": {"start": "python main.py"}}',
    )
    return scanner


class TestWorkspaceToKnowledgeScan:
    @pytest.mark.asyncio
    async def test_scan_project(self, populated_workspace: WorkspaceScanner) -> None:
        docs = await populated_workspace.scan("/project")
        assert len(docs) == 7

    @pytest.mark.asyncio
    async def test_scan_docs_only(self, populated_workspace: WorkspaceScanner) -> None:
        docs = await populated_workspace.scan("/project/docs")
        assert len(docs) == 2
        assert all(d.format == DocumentFormat.MARKDOWN for d in docs)

    @pytest.mark.asyncio
    async def test_scan_source_only(self, populated_workspace: WorkspaceScanner) -> None:
        docs = await populated_workspace.scan("/project/src")
        assert len(docs) == 2
        assert all(d.format == DocumentFormat.SOURCE_CODE for d in docs)

    @pytest.mark.asyncio
    async def test_format_detection(self, populated_workspace: WorkspaceScanner) -> None:
        docs = await populated_workspace.scan("/project")
        formats = {d.path: d.format for d in docs}
        assert formats["/project/config.yaml"] == DocumentFormat.YAML
        assert formats["/project/package.json"] == DocumentFormat.JSON


class TestWorkspaceToKnowledgeIndex:
    @pytest.mark.asyncio
    async def test_index_all_documents(self, populated_workspace: WorkspaceScanner) -> None:
        indexer = WorkspaceIndexer(chunk_size=200)
        docs = await populated_workspace.scan("/project")
        indexed = await indexer.index_batch(docs)
        assert len(indexed) == 7

    @pytest.mark.asyncio
    async def test_indexed_documents_searchable(
        self, populated_workspace: WorkspaceScanner
    ) -> None:
        indexer = WorkspaceIndexer(chunk_size=200)
        docs = await populated_workspace.scan("/project")
        await indexer.index_batch(docs)
        results = await indexer.search("architecture")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_api_docs(self, populated_workspace: WorkspaceScanner) -> None:
        indexer = WorkspaceIndexer(chunk_size=200)
        docs = await populated_workspace.scan("/project")
        await indexer.index_batch(docs)
        results = await indexer.search("REST")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_source_code(self, populated_workspace: WorkspaceScanner) -> None:
        indexer = WorkspaceIndexer(chunk_size=200)
        docs = await populated_workspace.scan("/project")
        await indexer.index_batch(docs)
        results = await indexer.search("AuthService")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_chunk_count_varies(self, populated_workspace: WorkspaceScanner) -> None:
        indexer = WorkspaceIndexer(chunk_size=50)
        docs = await populated_workspace.scan("/project")
        indexed = await indexer.index_batch(docs)
        # Longer documents should have more chunks
        chunk_counts = {i.path: i.chunk_count for i in indexed}
        assert all(c > 0 for c in chunk_counts.values())


class TestWorkspaceToKnowledgeStats:
    @pytest.mark.asyncio
    async def test_stats_after_indexing(self, populated_workspace: WorkspaceScanner) -> None:
        indexer = WorkspaceIndexer(chunk_size=200)
        docs = await populated_workspace.scan("/project")
        await indexer.index_batch(docs)
        stats = await indexer.get_stats()
        assert stats["total_documents"] == 7
        assert stats["total_chunks"] > 0

    @pytest.mark.asyncio
    async def test_stats_format_breakdown(self, populated_workspace: WorkspaceScanner) -> None:
        indexer = WorkspaceIndexer(chunk_size=200)
        docs = await populated_workspace.scan("/project")
        await indexer.index_batch(docs)
        stats = await indexer.get_stats()
        assert stats.get("format_markdown", 0) == 3
        assert stats.get("format_source_code", 0) == 2


class TestWorkspaceToKnowledgeRemoval:
    @pytest.mark.asyncio
    async def test_remove_indexed_document(self, populated_workspace: WorkspaceScanner) -> None:
        indexer = WorkspaceIndexer(chunk_size=200)
        docs = await populated_workspace.scan("/project")
        await indexer.index_batch(docs)
        removed = await indexer.remove_document("/project/README.md")
        assert removed is True
        stats = await indexer.get_stats()
        assert stats["total_documents"] == 6

    @pytest.mark.asyncio
    async def test_removed_document_not_searchable(
        self, populated_workspace: WorkspaceScanner
    ) -> None:
        indexer = WorkspaceIndexer(chunk_size=200)
        docs = await populated_workspace.scan("/project")
        await indexer.index_batch(docs)
        await indexer.remove_document("/project/README.md")
        results = await indexer.search("great project description")
        assert len(results) == 0


class TestWorkspaceToKnowledgeEvents:
    @pytest.mark.asyncio
    async def test_index_emits_event(self, populated_workspace: WorkspaceScanner) -> None:
        indexer = WorkspaceIndexer(chunk_size=200)
        docs = await populated_workspace.scan("/project")
        await indexer.index_batch(docs)
        assert len(indexer.events) == 1
        assert indexer.events[0].documents_indexed == 7
