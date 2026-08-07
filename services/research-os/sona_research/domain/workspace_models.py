"""Workspace indexing domain models."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DocumentFormat(StrEnum):
    """Supported document formats for workspace indexing."""

    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    TEXT = "text"
    SOURCE_CODE = "source_code"
    JSON = "json"
    YAML = "yaml"


@dataclass(frozen=True)
class WorkspaceDocument:
    """A document found in the workspace."""

    path: str
    title: str
    content: str
    format: DocumentFormat
    size_bytes: int = 0
    last_modified: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IndexedDocument:
    """A document that has been indexed into the knowledge system."""

    doc_id: str
    path: str
    title: str
    format: DocumentFormat
    chunk_count: int = 0
    indexed_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
