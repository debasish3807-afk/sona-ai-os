"""Tests for the Knowledge Manager (full integration)."""

import pytest

from sona_knowledge.domain.events import (
    DocumentDeletedEvent,
    DocumentIngestedEvent,
    QueryExecutedEvent,
)
from sona_knowledge.domain.models import Document, DocumentType, RAGQuery
from sona_knowledge.infrastructure.di import create_knowledge_manager
from sona_knowledge.infrastructure.knowledge_manager import KnowledgeManager


@pytest.fixture
def manager() -> KnowledgeManager:
    return create_knowledge_manager(vector_size=64, chunk_size=200, chunk_overlap=20)


@pytest.fixture
def sample_doc() -> Document:
    return Document(
        id="doc-001",
        title="Python Guide",
        content=(
            "Python is a high-level programming language. "
            "It is known for its readability and simplicity. "
            "Python supports multiple programming paradigms including "
            "procedural, object-oriented, and functional programming. "
            "The language was created by Guido van Rossum and first "
            "released in 1991."
        ),
        doc_type=DocumentType.TEXT,
        metadata={"author": "Test"},
    )


class TestKnowledgeManagerIngest:
    """Tests for document ingestion."""

    @pytest.mark.asyncio
    async def test_ingest_returns_document_id(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        result = await manager.ingest(sample_doc, "kb-main")
        assert result == "doc-001"

    @pytest.mark.asyncio
    async def test_ingest_emits_event(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        await manager.ingest(sample_doc, "kb-main")
        events = [e for e in manager.events if isinstance(e, DocumentIngestedEvent)]
        assert len(events) == 1
        assert events[0].document_id == "doc-001"
        assert events[0].kb_id == "kb-main"
        assert events[0].chunks_count > 0

    @pytest.mark.asyncio
    async def test_ingest_creates_chunks(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        await manager.ingest(sample_doc, "kb-main")
        assert manager._vector_store.size > 0

    @pytest.mark.asyncio
    async def test_ingest_idempotent(self, manager: KnowledgeManager, sample_doc: Document) -> None:
        await manager.ingest(sample_doc, "kb-main")
        size_after_first = manager._vector_store.size
        await manager.ingest(sample_doc, "kb-main")
        # Should not re-index same content
        assert manager._vector_store.size == size_after_first

    @pytest.mark.asyncio
    async def test_ingest_multiple_documents(self, manager: KnowledgeManager) -> None:
        doc1 = Document(id="d1", title="Doc1", content="Content one.", doc_type=DocumentType.TEXT)
        doc2 = Document(id="d2", title="Doc2", content="Content two.", doc_type=DocumentType.TEXT)
        await manager.ingest(doc1, "kb-main")
        await manager.ingest(doc2, "kb-main")
        assert manager._vector_store.size >= 2

    @pytest.mark.asyncio
    async def test_ingest_registers_knowledge_base(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        await manager.ingest(sample_doc, "kb-test")
        kbs = await manager.list_knowledge_bases("user-1")
        assert any(kb["id"] == "kb-test" for kb in kbs)


class TestKnowledgeManagerQuery:
    """Tests for RAG query pipeline."""

    @pytest.mark.asyncio
    async def test_query_empty_store(self, manager: KnowledgeManager) -> None:
        query = RAGQuery(query="Python", min_similarity=0.0)
        result = await manager.query(query)
        assert result.chunks == []
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_query_after_ingest(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        await manager.ingest(sample_doc, "kb-main")
        query = RAGQuery(query="Python programming", min_similarity=0.0, top_k=3)
        result = await manager.query(query)
        assert len(result.chunks) > 0
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_query_returns_sources(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        await manager.ingest(sample_doc, "kb-main")
        query = RAGQuery(query="Python", min_similarity=0.0, top_k=3)
        result = await manager.query(query)
        assert "doc-001" in result.sources

    @pytest.mark.asyncio
    async def test_query_returns_augmented_context(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        await manager.ingest(sample_doc, "kb-main")
        query = RAGQuery(query="Python", min_similarity=0.0)
        result = await manager.query(query)
        assert result.augmented_context != ""

    @pytest.mark.asyncio
    async def test_query_emits_event(self, manager: KnowledgeManager, sample_doc: Document) -> None:
        await manager.ingest(sample_doc, "kb-main")
        query = RAGQuery(query="Python", min_similarity=0.0)
        await manager.query(query)
        events = [e for e in manager.events if isinstance(e, QueryExecutedEvent)]
        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_query_with_rerank_disabled(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        await manager.ingest(sample_doc, "kb-main")
        query = RAGQuery(query="Python", min_similarity=0.0, rerank=False)
        result = await manager.query(query)
        assert len(result.chunks) > 0

    @pytest.mark.asyncio
    async def test_query_kb_filter(self, manager: KnowledgeManager) -> None:
        doc1 = Document(
            id="d1",
            title="Doc1",
            content="Python programming language guide tutorial",
            doc_type=DocumentType.TEXT,
        )
        doc2 = Document(
            id="d2",
            title="Doc2",
            content="JavaScript web development framework guide",
            doc_type=DocumentType.TEXT,
        )
        await manager.ingest(doc1, "kb-python")
        await manager.ingest(doc2, "kb-js")
        query = RAGQuery(query="programming", knowledge_base_id="kb-python", min_similarity=0.0)
        result = await manager.query(query)
        for chunk in result.chunks:
            assert chunk.metadata is not None
            assert chunk.metadata.get("kb_id") == "kb-python"


class TestKnowledgeManagerDelete:
    """Tests for document deletion."""

    @pytest.mark.asyncio
    async def test_delete_existing_document(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        await manager.ingest(sample_doc, "kb-main")
        assert await manager.delete_document("doc-001") is True
        assert manager._vector_store.size == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, manager: KnowledgeManager) -> None:
        assert await manager.delete_document("nonexistent") is False

    @pytest.mark.asyncio
    async def test_delete_emits_event(
        self, manager: KnowledgeManager, sample_doc: Document
    ) -> None:
        await manager.ingest(sample_doc, "kb-main")
        await manager.delete_document("doc-001")
        events = [e for e in manager.events if isinstance(e, DocumentDeletedEvent)]
        assert len(events) == 1
        assert events[0].document_id == "doc-001"


class TestKnowledgeManagerList:
    """Tests for listing knowledge bases."""

    @pytest.mark.asyncio
    async def test_list_empty(self, manager: KnowledgeManager) -> None:
        kbs = await manager.list_knowledge_bases("user-1")
        assert kbs == []

    @pytest.mark.asyncio
    async def test_list_after_ingest(self, manager: KnowledgeManager, sample_doc: Document) -> None:
        await manager.ingest(sample_doc, "kb-docs")
        kbs = await manager.list_knowledge_bases("user-1")
        assert len(kbs) == 1
        assert kbs[0]["id"] == "kb-docs"

    @pytest.mark.asyncio
    async def test_list_multiple_kbs(self, manager: KnowledgeManager) -> None:
        doc1 = Document(id="d1", title="D1", content="Content A", doc_type=DocumentType.TEXT)
        doc2 = Document(id="d2", title="D2", content="Content B", doc_type=DocumentType.TEXT)
        await manager.ingest(doc1, "kb-1")
        await manager.ingest(doc2, "kb-2")
        kbs = await manager.list_knowledge_bases("user-1")
        assert len(kbs) == 2
