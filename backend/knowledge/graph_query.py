"""Graph Query — search and retrieval service."""

from __future__ import annotations

from knowledge.entity_manager import EntityManager
from knowledge.graph_engine import GraphEngine
from knowledge.models import KnowledgeEntity, KnowledgeRelationship, RelationType
from knowledge.relationship_manager import RelationshipManager


class GraphQueryService:
    """Query service for graph entities and relationships."""

    def __init__(
        self, entity_mgr: EntityManager, rel_mgr: RelationshipManager, engine: GraphEngine
    ) -> None:
        self._entities = entity_mgr
        self._rels = rel_mgr
        self._engine = engine

    def search_by_id(self, entity_id: str) -> KnowledgeEntity | None:
        try:
            return self._entities.get(entity_id)
        except Exception:
            return None

    def search_by_type(self, entity_type: str) -> list[KnowledgeEntity]:
        return self._entities.list(entity_type=entity_type, limit=100000)  # type: ignore

    def search_by_tag(self, tag: str) -> list[KnowledgeEntity]:
        return self._entities.list(tag=tag, limit=100000)  # type: ignore

    def search_by_metadata(self, key: str, value: str) -> list[KnowledgeEntity]:
        return [
            e
            for e in self._entities.list(limit=100000)  # type: ignore
            if key in e.metadata and str(e.metadata[key]) == value
        ]

    def search_text(self, query: str) -> list[KnowledgeEntity]:
        return self._entities.search(query)

    def get_neighbors(self, entity_id: str) -> list[KnowledgeEntity]:
        return self._engine.get_neighbors(entity_id)

    def get_relationships(self, entity_id: str) -> list[KnowledgeRelationship]:
        return self._rels.search(entity_id)

    def get_outgoing_relationships(
        self, entity_id: str, rtype: str | None = None
    ) -> list[KnowledgeRelationship]:
        rels = self._rels.get_outgoing(entity_id)
        if rtype:
            try:
                rt = RelationType(rtype)
                return [r for r in rels if r.relation_type == rt]
            except ValueError:
                return []
        return rels

    def get_incoming_relationships(
        self, entity_id: str, rtype: str | None = None
    ) -> list[KnowledgeRelationship]:
        rels = self._rels.get_incoming(entity_id)
        if rtype:
            try:
                rt = RelationType(rtype)
                return [r for r in rels if r.relation_type == rt]
            except ValueError:
                return []
        return rels

    def stats(self) -> dict[str, int]:
        return self._engine.stats()
