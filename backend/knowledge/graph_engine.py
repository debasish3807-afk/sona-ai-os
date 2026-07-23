"""Graph Engine — traversal and analysis algorithms."""

from __future__ import annotations

from collections import deque

from knowledge.entity_manager import EntityManager
from knowledge.models import KnowledgeEntity, KnowledgeRelationship
from knowledge.relationship_manager import RelationshipManager


class GraphEngine:
    """Graph construction and analysis algorithms."""

    def __init__(self, entity_mgr: EntityManager, rel_mgr: RelationshipManager) -> None:
        self._entities = entity_mgr
        self._rels = rel_mgr

    def get_node(self, entity_id: str) -> KnowledgeEntity | None:
        try:
            return self._entities.get(entity_id)
        except Exception:
            return None

    def get_edge(self, rel_id: str) -> KnowledgeRelationship | None:
        try:
            return self._rels.get(rel_id)
        except Exception:
            return None

    def get_neighbors(self, entity_id: str) -> list[KnowledgeEntity]:
        rels = self._rels.get_outgoing(entity_id) + self._rels.get_incoming(entity_id)
        neighbor_ids: set[str] = set()
        for r in rels:
            neighbor_ids.add(r.source_id)
            neighbor_ids.add(r.target_id)
        neighbor_ids.discard(entity_id)
        return [self._entities.get(eid) for eid in neighbor_ids if self._entities.exists(eid)]

    def bfs(self, start_id: str, max_depth: int = 5) -> dict[int, list[KnowledgeEntity]]:
        levels: dict[int, list[KnowledgeEntity]] = {}
        visited: set[str] = set()
        q: deque[tuple[str, int]] = deque()
        q.append((start_id, 0))
        visited.add(start_id)
        while q:
            current, depth = q.popleft()
            if depth > max_depth:
                continue
            str_depth = str(depth)
            if str_depth not in levels:
                levels[depth] = []
            try:
                entity = self._entities.get(current)
                if entity:
                    levels.setdefault(depth, []).append(entity)
            except Exception:
                continue
            if depth < max_depth:
                for rel in self._rels.get_outgoing(current):
                    if rel.target_id not in visited:
                        visited.add(rel.target_id)
                        q.append((rel.target_id, depth + 1))
                for rel in self._rels.get_incoming(current):
                    if rel.source_id not in visited:
                        visited.add(rel.source_id)
                        q.append((rel.source_id, depth + 1))
        return levels

    def dfs(self, start_id: str, max_depth: int = 10) -> list[KnowledgeEntity]:
        visited: set[str] = set()
        result: list[KnowledgeEntity] = []

        def _dfs(node_id: str, depth: int) -> None:
            if depth > max_depth or node_id in visited:
                return
            visited.add(node_id)
            try:
                entity = self._entities.get(node_id)
                if entity:
                    result.append(entity)
            except Exception:
                return
            for rel in self._rels.get_outgoing(node_id):
                _dfs(rel.target_id, depth + 1)
            for rel in self._rels.get_incoming(node_id):
                _dfs(rel.source_id, depth + 1)

        _dfs(start_id, 0)
        return result

    def connected_components(self) -> list[list[KnowledgeEntity]]:
        entity_ids = [e.entity_id for e in self._entities.list(limit=100000)]  # type: ignore
        if not entity_ids:
            return []
        visited: set[str] = set()
        components: list[list[KnowledgeEntity]] = []

        def _collect(nid: str, comp: list[KnowledgeEntity]) -> None:
            if nid in visited:
                return
            visited.add(nid)
            try:
                e = self._entities.get(nid)
                if e:
                    comp.append(e)
            except Exception:
                return
            for rel in self._rels.get_outgoing(nid):
                _collect(rel.target_id, comp)
            for rel in self._rels.get_incoming(nid):
                _collect(rel.source_id, comp)

        for eid in entity_ids:
            if eid not in visited:
                comp: list[KnowledgeEntity] = []
                _collect(eid, comp)
                if comp:
                    components.append(comp)
        return components

    def shortest_path(self, start_id: str, end_id: str) -> list[KnowledgeEntity]:
        if start_id == end_id:
            try:
                return [self._entities.get(start_id)]
            except Exception:
                return []
        visited: set[str] = set()
        parent: dict[str, str | None] = {start_id: None}
        q: deque[str] = deque([start_id])
        visited.add(start_id)
        while q:
            current = q.popleft()
            for rel in self._rels.get_outgoing(current):
                if rel.target_id not in visited:
                    visited.add(rel.target_id)
                    parent[rel.target_id] = current
                    q.append(rel.target_id)
                    if rel.target_id == end_id:
                        path: list[KnowledgeEntity] = []
                        node: str | None = end_id
                        while node is not None:
                            try:
                                path.append(self._entities.get(node))
                            except Exception:
                                pass
                            node = parent.get(node)
                        path.reverse()
                        return path
        return []

    def subgraph(self, entity_ids: list[str]) -> dict:
        entities = []
        relationships = []
        for eid in entity_ids:
            try:
                entities.append(self._entities.get(eid))
            except Exception:
                pass
            for rel in self._rels.get_outgoing(eid):
                if rel.target_id in entity_ids:
                    relationships.append(rel)
        return {"entities": entities, "relationships": relationships}

    def stats(self) -> dict[str, int]:
        return {"entities": self._entities.count(), "relationships": self._rels.count()}
