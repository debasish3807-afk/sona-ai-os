"""Knowledge Graph Service — integration hub for Memory, RAG, Agents, Automation."""

from __future__ import annotations

from typing import Any

from knowledge.entity_manager import EntityManager
from knowledge.graph_engine import GraphEngine
from knowledge.graph_query import GraphQueryService
from knowledge.graph_validator import GraphValidator
from knowledge.models import EntityType, KnowledgeEntity, KnowledgeRelationship, RelationType
from knowledge.relationship_manager import RelationshipManager


class KnowledgeGraphService:
    """Unified service integrating knowledge graph with other subsystems."""

    def __init__(self) -> None:
        self._entity_mgr = EntityManager()
        self._rel_mgr = RelationshipManager(entity_exists_fn=self._entity_mgr.exists)
        self._engine = GraphEngine(self._entity_mgr, self._rel_mgr)
        self._query = GraphQueryService(self._entity_mgr, self._rel_mgr, self._engine)
        self._validator = GraphValidator(self._entity_mgr, self._rel_mgr)

    @property
    def entities(self) -> EntityManager:
        return self._entity_mgr

    @property
    def relationships(self) -> RelationshipManager:
        return self._rel_mgr

    @property
    def graph(self) -> GraphEngine:
        return self._engine

    @property
    def query(self) -> GraphQueryService:
        return self._query

    @property
    def validator(self) -> GraphValidator:
        return self._validator

    def index_memory(
        self, memory_content: str, memory_id: str, memory_type: str = "conversation"
    ) -> str:
        entity = KnowledgeEntity(
            entity_id=memory_id,
            entity_type=EntityType.CONVERSATION,
            name=f"Memory: {memory_content[:60]}",
            description=memory_content[:500],
            source="memory_engine",
        )
        return self._entity_mgr.create(entity)

    def index_document(
        self, doc_id: str, title: str, content: str, tags: list[str] | None = None
    ) -> str:
        entity = KnowledgeEntity(
            entity_id=doc_id,
            entity_type=EntityType.DOCUMENT,
            name=title,
            description=content[:500],
            tags=tags or [],
            source="rag",
        )
        return self._entity_mgr.create(entity)

    def create_project_entity(self, project_id: str, name: str, description: str = "") -> str:
        return self._entity_mgr.create(
            KnowledgeEntity(
                entity_id=project_id,
                entity_type=EntityType.PROJECT,
                name=name,
                description=description,
                tags=["project"],
                source="workspace",
            )
        )

    def create_file_entity(self, file_id: str, name: str, path: str) -> str:
        return self._entity_mgr.create(
            KnowledgeEntity(
                entity_id=file_id,
                entity_type=EntityType.FILE,
                name=name,
                description=path,
                tags=["file"],
                metadata={"path": path},
                source="workspace",
            )
        )

    def create_task_entity(self, task_id: str, name: str, description: str = "") -> str:
        return self._entity_mgr.create(
            KnowledgeEntity(
                entity_id=task_id,
                entity_type=EntityType.TASK,
                name=name,
                description=description,
                tags=["task"],
                source="workspace",
            )
        )

    def get_context_for_agent(self, entity_id: str) -> dict[str, Any]:
        entity = self._entity_mgr.get(entity_id) if self._entity_mgr.exists(entity_id) else None
        neighbors = self._engine.get_neighbors(entity_id) if entity else []
        return {
            "entity": {
                "id": entity.entity_id,
                "name": entity.name,
                "type": entity.entity_type.value,
            }
            if entity
            else None,
            "neighbors": [{"id": e.entity_id, "name": e.name} for e in neighbors],
            "context_size": len(neighbors),
        }

    def execute_query(self, query_type: str, params: dict[str, Any]) -> dict[str, Any]:
        if query_type == "search":
            results = self._query.search_text(params.get("query", ""))
            return {
                "results": [
                    {"id": e.entity_id, "name": e.name, "type": e.entity_type.value}
                    for e in results
                ]
            }
        if query_type == "create_entity":
            eid = self._entity_mgr.create(
                KnowledgeEntity(
                    name=params.get("name", ""),
                    entity_type=EntityType(params.get("type", "custom")),
                    description=params.get("description", ""),
                    tags=params.get("tags", []),
                    metadata=params.get("metadata", {}),
                )
            )
            return {"entity_id": eid}
        if query_type == "create_relationship":
            rid = self._rel_mgr.create(
                KnowledgeRelationship(
                    source_id=params["source_id"],
                    target_id=params["target_id"],
                    relation_type=RelationType(params.get("type", "related_to")),
                    weight=params.get("weight", 1.0),
                )
            )
            return {"relationship_id": rid}
        return {"error": f"Unknown query type: {query_type}"}
