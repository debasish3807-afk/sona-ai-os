"""Data schemas for the knowledge system."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    MARKDOWN = "markdown"
    TXT = "txt"
    HTML = "html"
    URL = "url"


@dataclass
class Document:
    """A knowledge document."""

    title: str
    content: str
    doc_type: DocumentType
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    metadata: dict = field(default_factory=dict)
    chunks: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class Chunk:
    """A chunk of a document."""

    doc_id: str
    content: str
    index: int
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """A search result from the knowledge base."""

    chunk_id: str
    doc_id: str
    content: str
    score: float
    metadata: dict = field(default_factory=dict)


@dataclass
class Citation:
    """A citation reference."""

    source: str
    title: str
    chunk_id: str
    relevance: float
