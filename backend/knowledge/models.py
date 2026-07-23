"""Knowledge Graph data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class EntityType(str, Enum):
    PEOPLE = "people"
    PROJECT = "project"
    FILE = "file"
    CONVERSATION = "conversation"
    TASK = "task"
    DOCUMENT = "document"
    CODE_SYMBOL = "code_symbol"
    CUSTOM = "custom"


class RelationType(str, Enum):
    REFERENCES = "references"
    BELONGS_TO = "belongs_to"
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    CREATED_BY = "created_by"
    UPDATED_BY = "updated_by"
    CONTAINS = "contains"
    USES = "uses"


@dataclass
class KnowledgeEntity:
    entity_id: str = ""
    entity_type: EntityType = EntityType.CUSTOM
    name: str = ""
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = "manual"


@dataclass
class KnowledgeRelationship:
    relationship_id: str = ""
    source_id: str = ""
    target_id: str = ""
    relation_type: RelationType = RelationType.RELATED_TO
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
