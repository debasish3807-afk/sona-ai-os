"""Knowledge Graph — entity-relationship graph for structured knowledge.

Provides a production-grade graph abstraction integrating with:
- Memory Engine (auto-index memories as entities)
- RAG subsystem (enrich chunks with graph context)
- Multi-Agent system (agent-accessible graph queries)
- Automation workflows (create/update entities via automation)
- Workspace (projects, files, tasks in the graph)
"""

from knowledge.entity_manager import EntityManager
from knowledge.exceptions import (
    EntityNotFoundError,
    GraphConsistencyError,
    InvalidRelationshipError,
    KnowledgeGraphError,
    RelationshipNotFoundError,
)
from knowledge.graph_engine import GraphEngine
from knowledge.graph_query import GraphQueryService
from knowledge.graph_validator import GraphValidator
from knowledge.knowledge_engine import KnowledgeEngine
from knowledge.models import EntityType, KnowledgeEntity, KnowledgeRelationship, RelationType
from knowledge.relationship_manager import RelationshipManager
from knowledge.services import KnowledgeGraphService

__all__ = [
    "EntityManager",
    "EntityNotFoundError",
    "EntityType",
    "GraphConsistencyError",
    "GraphEngine",
    "GraphQueryService",
    "GraphValidator",
    "InvalidRelationshipError",
    "KnowledgeEntity",
    "KnowledgeGraphError",
    "KnowledgeEngine",
    "KnowledgeGraphService",
    "KnowledgeRelationship",
    "EntityType",
    "RelationType",
    "RelationshipManager",
    "RelationshipNotFoundError",
]
