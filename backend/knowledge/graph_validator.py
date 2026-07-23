"""Graph Validator — consistency and integrity checks."""

from __future__ import annotations

from dataclasses import dataclass, field

from knowledge.entity_manager import EntityManager
from knowledge.relationship_manager import RelationshipManager


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duplicate_entities: int = 0
    invalid_relationships: int = 0
    orphan_nodes: int = 0
    circular_refs: int = 0


class GraphValidator:
    """Validates graph structure for consistency."""

    def __init__(self, entity_mgr: EntityManager, rel_mgr: RelationshipManager) -> None:
        self._entities = entity_mgr
        self._rels = rel_mgr

    def validate(self) -> ValidationResult:
        result = ValidationResult()
        entity_ids = set()
        entity_name_map: dict[str, list[str]] = {}
        for e in self._entities.list(limit=100000):  # type: ignore
            entity_ids.add(e.entity_id)
            entity_name_map.setdefault(e.name.lower(), []).append(e.entity_id)

        for name, ids in entity_name_map.items():
            if len(ids) > 1:
                result.duplicate_entities += 1
                result.warnings.append(f"Duplicate entity name: '{name}' (ids: {ids})")

        all_related_ids: set[str] = set()
        for rel in self._rels.list():
            if rel.source_id not in entity_ids:
                result.invalid_relationships += 1
                result.errors.append(
                    f"Relationship {rel.relationship_id}: source {rel.source_id} not found"
                )
            if rel.target_id not in entity_ids:
                result.invalid_relationships += 1
                result.errors.append(
                    f"Relationship {rel.relationship_id}: target {rel.target_id} not found"
                )
            all_related_ids.add(rel.source_id)
            all_related_ids.add(rel.target_id)

        orphans = entity_ids - all_related_ids
        if orphans:
            result.orphan_nodes = len(orphans)
            result.warnings.append(f"{len(orphans)} orphan nodes found")

        result.valid = len(result.errors) == 0
        return result

    def has_circular_reference(self, start_id: str) -> bool:
        visited: set[str] = set()
        stack: set[str] = set()

        def _dfs(node: str) -> bool:
            if node in stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            stack.add(node)
            for rel in self._rels.get_outgoing(node):
                if rel.source_id == rel.target_id:
                    continue
                if _dfs(rel.target_id):
                    return True
            stack.discard(node)
            return False

        return _dfs(start_id)
