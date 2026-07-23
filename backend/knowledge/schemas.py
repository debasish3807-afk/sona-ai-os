"""Knowledge Graph Pydantic schemas for API."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EntityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    entity_type: str = "custom"
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class EntityUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None
    tags: list[str] | None = None


class EntityResponse(BaseModel):
    entity_id: str = ""
    entity_type: str = ""
    name: str = ""
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class RelationshipCreate(BaseModel):
    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    relation_type: str = "related_to"
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipResponse(BaseModel):
    relationship_id: str = ""
    source_id: str = ""
    target_id: str = ""
    relation_type: str = ""
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""


class GraphResponse(BaseModel):
    entities: list[EntityResponse] = Field(default_factory=list)
    relationships: list[RelationshipResponse] = Field(default_factory=list)


class ValidationResponse(BaseModel):
    valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duplicate_entities: int = 0
    invalid_relationships: int = 0
    orphan_nodes: int = 0


class Chunk(BaseModel):
    chunk_id: str = ""
    doc_id: str = ""
    content: str = ""
    index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] = Field(default_factory=list)


class DocumentType(str, Enum):
    TEXT = "text"
    CODE = "code"
    PDF = "pdf"
    IMAGE = "image"
    MARKDOWN = "markdown"
    TXT = "txt"
    HTML = "html"
    JSON = "json"


class Document(BaseModel):
    doc_id: str = ""
    content: str = ""
    doc_type: DocumentType = DocumentType.TEXT
    title: str = ""
    source: str = ""
    created_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunks: list[Chunk] = Field(default_factory=list)


class SearchResult(BaseModel):
    doc_id: str = ""
    content: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunks: list[Chunk] = Field(default_factory=list)


class Citation(BaseModel):
    source_id: str = ""
    text: str = ""
    title: str = ""
    url: str = ""
