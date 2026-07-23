"""Knowledge Graph — entity-relation graph for structured memory."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GraphEntity:
    id: str = ""
    name: str = ""
    type: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0


@dataclass
class GraphRelation:
    id: str = ""
    source_id: str = ""
    target_id: str = ""
    relation_type: str = ""
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0


@dataclass
class GraphQuery:
    entity_type: str | None = None
    relation_type: str | None = None
    limit: int = 50
    min_weight: float = 0.0


class KnowledgeGraph:
    """In-memory knowledge graph with entities, relations, and traversal."""

    def __init__(self) -> None:
        self._entities: dict[str, GraphEntity] = {}
        self._relations: dict[str, GraphRelation] = {}
        self._out_edges: dict[str, set[str]] = {}
        self._in_edges: dict[str, set[str]] = {}

    def add_entity(
        self, name: str, etype: str = "", properties: dict[str, Any] | None = None
    ) -> GraphEntity:
        eid = str(uuid.uuid4())
        entity = GraphEntity(
            id=eid, name=name, type=etype, properties=properties or {}, created_at=time.time()
        )
        self._entities[eid] = entity
        return entity

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        rtype: str = "related_to",
        weight: float = 1.0,
        properties: dict[str, Any] | None = None,
    ) -> GraphRelation:
        rid = str(uuid.uuid4())
        rel = GraphRelation(
            id=rid,
            source_id=source_id,
            target_id=target_id,
            relation_type=rtype,
            weight=weight,
            properties=properties or {},
            created_at=time.time(),
        )
        self._relations[rid] = rel
        self._out_edges.setdefault(source_id, set()).add(rid)
        self._in_edges.setdefault(target_id, set()).add(rid)
        return rel

    def get_entity(self, entity_id: str) -> GraphEntity | None:
        return self._entities.get(entity_id)

    def search_entities(self, query: str, limit: int = 20) -> list[GraphEntity]:
        q = query.lower()
        results = [e for e in self._entities.values() if q in e.name.lower() or q in e.type.lower()]
        return sorted(results, key=lambda e: e.created_at, reverse=True)[:limit]

    def get_relations(self, entity_id: str) -> list[GraphRelation]:
        rel_ids = self._out_edges.get(entity_id, set()) | self._in_edges.get(entity_id, set())
        return [self._relations[rid] for rid in rel_ids if rid in self._relations]

    def traverse(self, entity_id: str, depth: int = 2) -> list[dict[str, Any]]:
        visited: set[str] = set()
        results: list[dict[str, Any]] = []

        def _dfs(eid: str, d: int) -> None:
            if eid in visited or d > depth:
                return
            visited.add(eid)
            entity = self._entities.get(eid)
            if entity:
                results.append(
                    {
                        "entity": {"id": entity.id, "name": entity.name, "type": entity.type},
                        "depth": d,
                    }
                )
            for rel_id in self._out_edges.get(eid, set()):
                rel = self._relations.get(rel_id)
                if rel:
                    _dfs(rel.target_id, d + 1)
            for rel_id in self._in_edges.get(eid, set()):
                rel = self._relations.get(rel_id)
                if rel:
                    _dfs(rel.source_id, d + 1)

        _dfs(entity_id, 0)
        return results

    def get_stats(self) -> dict[str, Any]:
        return {
            "entities": len(self._entities),
            "relations": len(self._relations),
            "entity_types": len({e.type for e in self._entities.values()}),
            "relation_types": len({r.relation_type for r in self._relations.values()}),
        }

    def clear(self) -> None:
        self._entities.clear()
        self._relations.clear()
        self._out_edges.clear()
        self._in_edges.clear()
