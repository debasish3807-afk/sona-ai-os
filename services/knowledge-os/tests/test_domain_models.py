"""Unit tests for Knowledge OS domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_knowledge.domain.models import (
    Document,
    DocumentChunk,
    DocumentType,
    RAGQuery,
    RAGResult,
)


class TestDocumentType:
    """Tests for the DocumentType enum."""

    def test_all_types_defined(self) -> None:
        """Verify all expected document types are available."""
        assert DocumentType.PDF == "pdf"
        assert DocumentType.MARKDOWN == "markdown"
        assert DocumentType.TEXT == "text"
        assert DocumentType.HTML == "html"
        assert DocumentType.CODE == "code"
        assert DocumentType.JSON == "json"

    def test_type_count(self) -> None:
        """Verify exactly 6 document types exist."""
        assert len(DocumentType) == 6

    def test_type_is_str_enum(self) -> None:
        """Verify document types are usable as strings."""
        assert str(DocumentType.PDF) == "pdf"
        assert str(DocumentType.MARKDOWN) == "markdown"


class TestDocument:
    """Tests for the Document frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        doc = Document(
            id="doc-001",
            title="Test Document",
            content="Hello world",
            doc_type=DocumentType.TEXT,
        )
        assert doc.id == "doc-001"
        assert doc.title == "Test Document"
        assert doc.content == "Hello world"
        assert doc.doc_type == DocumentType.TEXT

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        doc = Document(
            id="doc-002",
            title="Readme",
            content="# Title",
            doc_type=DocumentType.MARKDOWN,
        )
        assert doc.metadata is None
        assert doc.source_url is None

    def test_with_all_fields(self) -> None:
        """Create with all optional fields."""
        doc = Document(
            id="doc-003",
            title="API Docs",
            content="<html><body>...</body></html>",
            doc_type=DocumentType.HTML,
            metadata={"author": "dev-team", "version": "2.0"},
            source_url="https://docs.example.com/api",
        )
        assert doc.metadata == {"author": "dev-team", "version": "2.0"}
        assert doc.source_url == "https://docs.example.com/api"

    def test_is_frozen(self) -> None:
        """Verify Document is immutable."""
        doc = Document(
            id="doc-001",
            title="Test",
            content="content",
            doc_type=DocumentType.TEXT,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            doc.title = "changed"  # type: ignore[misc]


class TestDocumentChunk:
    """Tests for the DocumentChunk frozen dataclass."""

    def test_creation_with_required_fields(self) -> None:
        """Create chunk with all required fields."""
        chunk = DocumentChunk(
            id="chunk-001",
            document_id="doc-001",
            content="This is a chunk of text.",
            embedding=[0.1, 0.2, 0.3, 0.4],
            chunk_index=0,
        )
        assert chunk.id == "chunk-001"
        assert chunk.document_id == "doc-001"
        assert chunk.content == "This is a chunk of text."
        assert chunk.embedding == [0.1, 0.2, 0.3, 0.4]
        assert chunk.chunk_index == 0

    def test_default_metadata(self) -> None:
        """Verify metadata defaults to None."""
        chunk = DocumentChunk(
            id="chunk-002",
            document_id="doc-001",
            content="Another chunk",
            embedding=[0.5, 0.6],
            chunk_index=1,
        )
        assert chunk.metadata is None

    def test_with_metadata(self) -> None:
        """Create chunk with metadata."""
        chunk = DocumentChunk(
            id="chunk-003",
            document_id="doc-002",
            content="Section content",
            embedding=[0.1] * 1536,
            chunk_index=2,
            metadata={"section": "Introduction"},
        )
        assert chunk.metadata == {"section": "Introduction"}
        assert len(chunk.embedding) == 1536

    def test_is_frozen(self) -> None:
        """Verify DocumentChunk is immutable."""
        chunk = DocumentChunk(
            id="chunk-001",
            document_id="doc-001",
            content="text",
            embedding=[0.1],
            chunk_index=0,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            chunk.content = "changed"  # type: ignore[misc]


class TestRAGQuery:
    """Tests for the RAGQuery frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required query field."""
        query = RAGQuery(query="What is Python?")
        assert query.query == "What is Python?"

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        query = RAGQuery(query="test query")
        assert query.knowledge_base_id is None
        assert query.top_k == 5
        assert query.min_similarity == 0.7
        assert query.rerank is True

    def test_with_all_fields(self) -> None:
        """Create with all fields specified."""
        query = RAGQuery(
            query="How do I deploy?",
            knowledge_base_id="kb-prod-docs",
            top_k=10,
            min_similarity=0.8,
            rerank=False,
        )
        assert query.knowledge_base_id == "kb-prod-docs"
        assert query.top_k == 10
        assert query.min_similarity == 0.8
        assert query.rerank is False

    def test_is_frozen(self) -> None:
        """Verify RAGQuery is immutable."""
        query = RAGQuery(query="test")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            query.query = "changed"  # type: ignore[misc]


class TestRAGResult:
    """Tests for the RAGResult frozen dataclass."""

    def test_creation_with_empty_chunks(self) -> None:
        """Create result with no chunks (no relevant results)."""
        result = RAGResult(
            chunks=[],
            augmented_context="",
            sources=[],
            confidence=0.0,
        )
        assert result.chunks == []
        assert result.augmented_context == ""
        assert result.sources == []
        assert result.confidence == 0.0

    def test_creation_with_chunks(self) -> None:
        """Create result with document chunks."""
        chunk = DocumentChunk(
            id="chunk-001",
            document_id="doc-001",
            content="Python is a programming language.",
            embedding=[0.1, 0.2, 0.3],
            chunk_index=0,
        )
        result = RAGResult(
            chunks=[chunk],
            augmented_context="Context: Python is a programming language.",
            sources=["doc-001"],
            confidence=0.92,
        )
        assert len(result.chunks) == 1
        assert result.chunks[0].content == "Python is a programming language."
        assert result.augmented_context == "Context: Python is a programming language."
        assert result.sources == ["doc-001"]
        assert result.confidence == 0.92

    def test_multiple_sources(self) -> None:
        """Create result with multiple source references."""
        result = RAGResult(
            chunks=[],
            augmented_context="Combined context from multiple docs.",
            sources=["doc-001", "doc-002", "doc-003"],
            confidence=0.85,
        )
        assert len(result.sources) == 3

    def test_is_frozen(self) -> None:
        """Verify RAGResult is immutable."""
        result = RAGResult(
            chunks=[],
            augmented_context="",
            sources=[],
            confidence=0.5,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            result.confidence = 0.9  # type: ignore[misc]
