"""Semantic memory - facts, concepts, and relationships.

This module defines the semantic memory interface which manages factual
knowledge, conceptual relationships, and structured information. Semantic
memory represents "knowing that" - declarative facts and their interconnections.

Unlike episodic memory (which captures events), semantic memory stores
decontextualized knowledge: facts, definitions, relationships, and rules
that have been distilled from experience.

Classes:
    SemanticConfig: Configuration for semantic memory behavior.
    Fact: A structured factual assertion with subject-predicate-object.
    SemanticRelation: A typed relationship between two memory entries.
    SemanticMemory: Abstract interface extending MemoryStore for semantic memory.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .base import MemoryStore


@dataclass(frozen=True, slots=True)
class SemanticConfig:
    """Configuration for semantic memory behavior.

    Controls capacity, knowledge graph features, and relationship management.

    Attributes:
        max_facts: Maximum number of facts to retain.
        enable_graph: Whether to maintain a knowledge graph structure.
        relationship_types: Allowed relationship type labels.
        auto_extract_facts: Whether to auto-extract facts from stored content.
        confidence_threshold: Minimum confidence for fact retention.
        dedup_enabled: Whether to detect and merge duplicate facts.
    """

    max_facts: int = 50000
    enable_graph: bool = True
    relationship_types: list[str] = field(
        default_factory=lambda: [
            "is_a",
            "has_a",
            "part_of",
            "related_to",
            "depends_on",
            "causes",
            "precedes",
            "contradicts",
            "supports",
        ]
    )
    auto_extract_facts: bool = True
    confidence_threshold: float = 0.5
    dedup_enabled: bool = True


@dataclass(slots=True)
class Fact:
    """A structured factual assertion with subject-predicate-object triple.

    Facts represent atomic units of knowledge in the semantic memory system.
    They follow a triple structure enabling graph-based querying and reasoning.

    Attributes:
        fact_id: Unique identifier for this fact (UUID4).
        subject: The subject of the fact (entity or concept).
        predicate: The relationship or property being asserted.
        object: The object of the fact (value or related entity).
        confidence: Confidence score for this fact (0.0-1.0).
        source: Provenance information - where this fact came from.
        verified: Whether this fact has been verified by a user or authoritative source.
        created_at: UTC timestamp when this fact was stored.
        updated_at: UTC timestamp of the most recent modification.
        metadata: Additional fact metadata.
    """

    subject: str
    predicate: str
    object: str
    fact_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    confidence: float = 1.0
    source: str | None = None
    verified: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticRelation:
    """A typed relationship between two memory entries or facts.

    Represents an edge in the knowledge graph connecting two nodes
    with a labeled, weighted relationship.

    Attributes:
        source_id: ID of the source entry/fact.
        target_id: ID of the target entry/fact.
        relation_type: The type label for this relationship.
        weight: Strength of the relationship (0.0-1.0).
        bidirectional: Whether the relationship is bidirectional.
        created_at: UTC timestamp when this relation was established.
        metadata: Additional relationship metadata.
    """

    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    bidirectional: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


class SemanticMemory(MemoryStore):
    """Abstract interface for semantic memory operations.

    Extends the base MemoryStore with fact management, relationship
    tracking, and knowledge graph operations.
    """

    @abstractmethod
    async def store_fact(self, fact: Fact) -> str:
        """Store a new fact in semantic memory.

        Args:
            fact: The fact to store.

        Returns:
            The fact_id of the stored fact.
        """
        ...

    @abstractmethod
    async def get_fact(self, fact_id: str) -> Fact | None:
        """Retrieve a single fact by its ID.

        Args:
            fact_id: The unique identifier of the fact.

        Returns:
            The fact if found, None otherwise.
        """
        ...

    @abstractmethod
    async def query_facts(
        self,
        subject: str | None = None,
        predicate: str | None = None,
        object: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 50,
    ) -> list[Fact]:
        """Query facts by subject, predicate, and/or object patterns.

        Any combination of parameters can be specified; unspecified
        parameters match any value (wildcard).

        Args:
            subject: Optional subject pattern to match.
            predicate: Optional predicate pattern to match.
            object: Optional object pattern to match.
            min_confidence: Minimum confidence threshold.
            limit: Maximum number of facts to return.

        Returns:
            List of matching facts.
        """
        ...

    @abstractmethod
    async def add_relation(self, relation: SemanticRelation) -> None:
        """Add a relationship between two entries or facts.

        Args:
            relation: The semantic relation to add.
        """
        ...

    @abstractmethod
    async def get_relations(
        self, entry_id: str, relation_type: str | None = None
    ) -> list[SemanticRelation]:
        """Get all relations involving a specific entry.

        Args:
            entry_id: The entry ID to get relations for.
            relation_type: Optional filter for specific relation types.

        Returns:
            List of relations where the entry is source or target.
        """
        ...

    @abstractmethod
    async def get_knowledge_subgraph(self, entry_id: str, depth: int = 2) -> dict[str, Any]:
        """Get a subgraph of the knowledge graph centered on an entry.

        Traverses relationships up to the specified depth and returns
        the connected subgraph as a dictionary.

        Args:
            entry_id: The center node for subgraph extraction.
            depth: Maximum traversal depth from the center node.

        Returns:
            Dictionary representation of the subgraph with keys:
                - nodes: List of node entries.
                - edges: List of relation edges.
                - center: The center entry_id.
                - depth: The actual depth reached.
        """
        ...
