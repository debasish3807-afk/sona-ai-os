"""Tests for workspace indexing domain models."""

from dataclasses import FrozenInstanceError

import pytest

from sona_research.domain.workspace_models import (
    DocumentFormat,
    IndexedDocument,
    WorkspaceDocument,
)


class TestDocumentFormat:
    def test_all_formats_defined(self) -> None:
        assert DocumentFormat.MARKDOWN == "markdown"
        assert DocumentFormat.PDF == "pdf"
        assert DocumentFormat.DOCX == "docx"
        assert DocumentFormat.TEXT == "text"
        assert DocumentFormat.SOURCE_CODE == "source_code"
        assert DocumentFormat.JSON == "json"
        assert DocumentFormat.YAML == "yaml"

    def test_format_count(self) -> None:
        assert len(DocumentFormat) == 7

    def test_is_str_enum(self) -> None:
        assert str(DocumentFormat.MARKDOWN) == "markdown"


class TestWorkspaceDocument:
    def test_creation_minimal(self) -> None:
        doc = WorkspaceDocument(
            path="/docs/readme.md",
            title="Readme",
            content="# Hello",
            format=DocumentFormat.MARKDOWN,
        )
        assert doc.path == "/docs/readme.md"
        assert doc.title == "Readme"
        assert doc.content == "# Hello"
        assert doc.format == DocumentFormat.MARKDOWN

    def test_creation_full(self) -> None:
        doc = WorkspaceDocument(
            path="/src/main.py",
            title="Main Module",
            content="import sys",
            format=DocumentFormat.SOURCE_CODE,
            size_bytes=1024,
            last_modified="2024-01-01T00:00:00Z",
            metadata={"language": "python"},
        )
        assert doc.size_bytes == 1024
        assert doc.last_modified == "2024-01-01T00:00:00Z"
        assert doc.metadata == {"language": "python"}

    def test_defaults(self) -> None:
        doc = WorkspaceDocument(path="/a", title="A", content="c", format=DocumentFormat.TEXT)
        assert doc.size_bytes == 0
        assert doc.last_modified == ""
        assert doc.metadata == {}

    def test_is_frozen(self) -> None:
        doc = WorkspaceDocument(path="/a", title="A", content="c", format=DocumentFormat.TEXT)
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            doc.path = "/b"  # type: ignore[misc]

    def test_empty_content(self) -> None:
        doc = WorkspaceDocument(
            path="/empty.txt", title="Empty", content="", format=DocumentFormat.TEXT
        )
        assert doc.content == ""

    def test_large_metadata(self) -> None:
        meta = {f"key_{i}": f"value_{i}" for i in range(50)}
        doc = WorkspaceDocument(
            path="/meta.json",
            title="Meta",
            content="{}",
            format=DocumentFormat.JSON,
            metadata=meta,
        )
        assert len(doc.metadata) == 50


class TestIndexedDocument:
    def test_creation_minimal(self) -> None:
        doc = IndexedDocument(
            doc_id="abc123",
            path="/docs/readme.md",
            title="Readme",
            format=DocumentFormat.MARKDOWN,
        )
        assert doc.doc_id == "abc123"
        assert doc.path == "/docs/readme.md"

    def test_creation_full(self) -> None:
        doc = IndexedDocument(
            doc_id="def456",
            path="/src/module.py",
            title="Module",
            format=DocumentFormat.SOURCE_CODE,
            chunk_count=5,
            indexed_at="2024-01-01T12:00:00Z",
            metadata={"lines": 200},
        )
        assert doc.chunk_count == 5
        assert doc.indexed_at == "2024-01-01T12:00:00Z"
        assert doc.metadata == {"lines": 200}

    def test_defaults(self) -> None:
        doc = IndexedDocument(doc_id="x", path="/a", title="A", format=DocumentFormat.TEXT)
        assert doc.chunk_count == 0
        assert doc.indexed_at == ""
        assert doc.metadata == {}

    def test_is_frozen(self) -> None:
        doc = IndexedDocument(doc_id="x", path="/a", title="A", format=DocumentFormat.TEXT)
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            doc.doc_id = "y"  # type: ignore[misc]

    def test_multiple_chunks(self) -> None:
        doc = IndexedDocument(
            doc_id="multi",
            path="/big.md",
            title="Big",
            format=DocumentFormat.MARKDOWN,
            chunk_count=100,
        )
        assert doc.chunk_count == 100
