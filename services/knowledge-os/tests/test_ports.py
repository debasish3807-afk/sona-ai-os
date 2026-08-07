"""Unit tests for Knowledge OS abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest
from sona_knowledge.application.ports import DocumentProcessorPort, KnowledgeBasePort
from sona_knowledge.domain.models import (
    Document,
    DocumentChunk,
    DocumentType,
    RAGQuery,
    RAGResult,
)


class TestKnowledgeBasePort:
    """Tests for the KnowledgeBasePort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify KnowledgeBasePort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            KnowledgeBasePort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = KnowledgeBasePort.__abstractmethods__
        assert "ingest" in abstract_methods
        assert "query" in abstract_methods
        assert "list_knowledge_bases" in abstract_methods
        assert "delete_document" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteKnowledgeBase(KnowledgeBasePort):
            async def ingest(self, document: Document, kb_id: str) -> str:
                return document.id

            async def query(self, rag_query: RAGQuery) -> RAGResult:
                return RAGResult(
                    chunks=[],
                    augmented_context="",
                    sources=[],
                    confidence=0.0,
                )

            async def list_knowledge_bases(self, user_id: str) -> list[dict]:
                return []

            async def delete_document(self, document_id: str) -> bool:
                return True

        kb = ConcreteKnowledgeBase()
        assert isinstance(kb, KnowledgeBasePort)

    @pytest.mark.asyncio
    async def test_ingest_returns_document_id(self) -> None:
        """Test that a concrete ingest() returns a document ID string."""

        class MockKnowledgeBase(KnowledgeBasePort):
            async def ingest(self, document: Document, kb_id: str) -> str:
                return f"{kb_id}/{document.id}"

            async def query(self, rag_query: RAGQuery) -> RAGResult:
                return RAGResult(chunks=[], augmented_context="", sources=[], confidence=0.0)

            async def list_knowledge_bases(self, user_id: str) -> list[dict]:
                return []

            async def delete_document(self, document_id: str) -> bool:
                return True

        kb = MockKnowledgeBase()
        doc = Document(
            id="doc-123",
            title="Test Doc",
            content="Hello world",
            doc_type=DocumentType.TEXT,
        )
        result = await kb.ingest(doc, "kb-main")
        assert result == "kb-main/doc-123"

    @pytest.mark.asyncio
    async def test_query_returns_rag_result(self) -> None:
        """Test that a concrete query() returns a RAGResult."""

        class MockKnowledgeBase(KnowledgeBasePort):
            async def ingest(self, document: Document, kb_id: str) -> str:
                return document.id

            async def query(self, rag_query: RAGQuery) -> RAGResult:
                chunk = DocumentChunk(
                    id="chunk-1",
                    document_id="doc-1",
                    content="Relevant content",
                    embedding=[0.1, 0.2],
                    chunk_index=0,
                )
                return RAGResult(
                    chunks=[chunk],
                    augmented_context=f"Context for: {rag_query.query}",
                    sources=["doc-1"],
                    confidence=0.9,
                )

            async def list_knowledge_bases(self, user_id: str) -> list[dict]:
                return []

            async def delete_document(self, document_id: str) -> bool:
                return True

        kb = MockKnowledgeBase()
        query = RAGQuery(query="What is AI?", top_k=3)
        result = await kb.query(query)
        assert isinstance(result, RAGResult)
        assert len(result.chunks) == 1
        assert result.confidence == 0.9
        assert "What is AI?" in result.augmented_context

    @pytest.mark.asyncio
    async def test_list_knowledge_bases(self) -> None:
        """Test that list_knowledge_bases returns a list of dicts."""

        class MockKnowledgeBase(KnowledgeBasePort):
            async def ingest(self, document: Document, kb_id: str) -> str:
                return document.id

            async def query(self, rag_query: RAGQuery) -> RAGResult:
                return RAGResult(chunks=[], augmented_context="", sources=[], confidence=0.0)

            async def list_knowledge_bases(self, user_id: str) -> list[dict]:
                return [
                    {"id": "kb-1", "name": "Docs", "user_id": user_id},
                    {"id": "kb-2", "name": "Research", "user_id": user_id},
                ]

            async def delete_document(self, document_id: str) -> bool:
                return True

        kb = MockKnowledgeBase()
        bases = await kb.list_knowledge_bases("user-42")
        assert len(bases) == 2
        assert all(b["user_id"] == "user-42" for b in bases)

    @pytest.mark.asyncio
    async def test_delete_document(self) -> None:
        """Test that delete_document returns a boolean."""

        class MockKnowledgeBase(KnowledgeBasePort):
            async def ingest(self, document: Document, kb_id: str) -> str:
                return document.id

            async def query(self, rag_query: RAGQuery) -> RAGResult:
                return RAGResult(chunks=[], augmented_context="", sources=[], confidence=0.0)

            async def list_knowledge_bases(self, user_id: str) -> list[dict]:
                return []

            async def delete_document(self, document_id: str) -> bool:
                return document_id == "doc-exists"

        kb = MockKnowledgeBase()
        assert await kb.delete_document("doc-exists") is True
        assert await kb.delete_document("doc-missing") is False


class TestDocumentProcessorPort:
    """Tests for the DocumentProcessorPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify DocumentProcessorPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DocumentProcessorPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = DocumentProcessorPort.__abstractmethods__
        assert "process" in abstract_methods
        assert "extract_text" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteProcessor(DocumentProcessorPort):
            async def process(self, document: Document) -> list[DocumentChunk]:
                return []

            async def extract_text(self, raw_content: bytes, doc_type: DocumentType) -> str:
                return ""

        processor = ConcreteProcessor()
        assert isinstance(processor, DocumentProcessorPort)

    @pytest.mark.asyncio
    async def test_process_returns_chunks(self) -> None:
        """Test that a concrete process() returns a list of DocumentChunk."""

        class MockProcessor(DocumentProcessorPort):
            async def process(self, document: Document) -> list[DocumentChunk]:
                return [
                    DocumentChunk(
                        id=f"{document.id}-chunk-0",
                        document_id=document.id,
                        content=document.content[:50],
                        embedding=[0.1, 0.2, 0.3],
                        chunk_index=0,
                    ),
                ]

            async def extract_text(self, raw_content: bytes, doc_type: DocumentType) -> str:
                return raw_content.decode("utf-8")

        processor = MockProcessor()
        doc = Document(
            id="doc-abc",
            title="Test",
            content="A longer document content for chunking purposes.",
            doc_type=DocumentType.TEXT,
        )
        chunks = await processor.process(doc)
        assert len(chunks) == 1
        assert chunks[0].document_id == "doc-abc"
        assert chunks[0].chunk_index == 0
        assert isinstance(chunks[0], DocumentChunk)

    @pytest.mark.asyncio
    async def test_extract_text_returns_string(self) -> None:
        """Test that extract_text returns a decoded string."""

        class MockProcessor(DocumentProcessorPort):
            async def process(self, document: Document) -> list[DocumentChunk]:
                return []

            async def extract_text(self, raw_content: bytes, doc_type: DocumentType) -> str:
                return raw_content.decode("utf-8")

        processor = MockProcessor()
        raw = b"Hello, this is raw text content."
        text = await processor.extract_text(raw, DocumentType.TEXT)
        assert text == "Hello, this is raw text content."
        assert isinstance(text, str)
