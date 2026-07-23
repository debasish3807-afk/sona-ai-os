"""Relationship Manager — CRUD for graph relationships."""

from __future__ import annotations

from datetime import UTC, datetime

from knowledge.exceptions import (
    EntityNotFoundError,
    RelationshipNotFoundError,
)
from knowledge.models import KnowledgeRelationship


class RelationshipManager:
    """Manages relationship CRUD operations."""

    def __init__(self, entity_exists_fn=None) -> None:
        self._relationships: dict[str, KnowledgeRelationship] = {}
        self._out_edges: dict[str, set[str]] = {}
        self._in_edges: dict[str, set[str]] = {}
        self._entity_exists = entity_exists_fn or (lambda _: True)

    def set_entity_checker(self, fn) -> None:
        self._entity_exists = fn

    def create(self, rel: KnowledgeRelationship) -> str:
        if not self._entity_exists(rel.source_id):
            raise EntityNotFoundError(f"Source entity {rel.source_id} not found")
        if not self._entity_exists(rel.target_id):
            raise EntityNotFoundError(f"Target entity {rel.target_id} not found")
        if not rel.relationship_id:
            import uuid

            rel.relationship_id = str(uuid.uuid4())
        rel.created_at = datetime.now(UTC)
        self._relationships[rel.relationship_id] = rel
        self._out_edges.setdefault(rel.source_id, set()).add(rel.relationship_id)
        self._in_edges.setdefault(rel.target_id, set()).add(rel.relationship_id)
        return rel.relationship_id

    def get(self, rel_id: str) -> KnowledgeRelationship:
        rel = self._relationships.get(rel_id)
        if not rel:
            raise RelationshipNotFoundError(f"Relationship {rel_id} not found")
        return rel

    def delete(self, rel_id: str) -> bool:
        rel = self._relationships.get(rel_id)
        if not rel:
            return False
        self._out_edges.get(rel.source_id, set()).discard(rel_id)
        self._in_edges.get(rel.target_id, set()).discard(rel_id)
        del self._relationships[rel_id]
        return True

    def get_outgoing(self, entity_id: str) -> list[KnowledgeRelationship]:
        rel_ids = self._out_edges.get(entity_id, set())
        return [self._relationships[rid] for rid in rel_ids if rid in self._relationships]

    def get_incoming(self, entity_id: str) -> list[KnowledgeRelationship]:
        rel_ids = self._in_edges.get(entity_id, set())
        return [self._relationships[rid] for rid in rel_ids if rid in self._relationships]

    def count(self) -> int:
        return len(self._relationships)

    def list(self) -> list[KnowledgeRelationship]:  # type: ignore[valid-type,no-any-return]
        return list(self._relationships.values())

    def search(self, entity_id: str) -> list[KnowledgeRelationship]:  # type: ignore
        return self.get_outgoing(entity_id) + self.get_incoming(entity_id)

    def load(self, rels: dict[str, KnowledgeRelationship]) -> None:
        self._relationships = dict(rels)
