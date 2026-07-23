"""Entity Manager — CRUD for Knowledge Graph entities."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from knowledge.exceptions import EntityNotFoundError
from knowledge.models import EntityType, KnowledgeEntity


class EntityManager:
    """Manages entity CRUD operations."""

    def __init__(self) -> None:
        self._entities: dict[str, KnowledgeEntity] = {}

    def create(self, entity: KnowledgeEntity) -> str:
        if not entity.entity_id:
            import uuid

            entity.entity_id = str(uuid.uuid4())
        entity.created_at = datetime.now(UTC)
        entity.updated_at = entity.created_at
        self._entities[entity.entity_id] = entity
        return entity.entity_id

    def get(self, entity_id: str) -> KnowledgeEntity:
        entity = self._entities.get(entity_id)
        if not entity:
            raise EntityNotFoundError(f"Entity {entity_id} not found")
        return entity

    def update(self, entity_id: str, **kwargs: Any) -> KnowledgeEntity:
        entity = self.get(entity_id)
        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        entity.updated_at = datetime.now(UTC)
        return entity

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._entities:
            del self._entities[entity_id]
            return True
        return False

    def list(
        self, entity_type: str | None = None, tag: str | None = None, limit: int = 100
    ) -> list[KnowledgeEntity]:  # type: ignore[valid-type,no-any-return]
        results = list(self._entities.values())
        if entity_type:
            try:
                et = EntityType(entity_type)
                results = [e for e in results if e.entity_type == et]
            except ValueError:
                pass
        if tag:
            results = [e for e in results if tag in e.tags]
        return results[:limit]

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._entities

    def count(self) -> int:
        return len(self._entities)

    def search(self, query: str) -> list[KnowledgeEntity]:  # type: ignore
        q = query.lower()
        return [
            e for e in self._entities.values() if q in e.name.lower() or q in e.description.lower()
        ]

    def load(self, entities: dict[str, KnowledgeEntity]) -> None:
        self._entities = dict(entities)
