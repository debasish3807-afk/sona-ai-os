"""Knowledge Graph exceptions."""


class KnowledgeGraphError(Exception):
    """Base exception for knowledge graph errors."""


class EntityNotFoundError(KnowledgeGraphError):
    """Raised when an entity is not found."""


class RelationshipNotFoundError(KnowledgeGraphError):
    """Raised when a relationship is not found."""


class InvalidRelationshipError(KnowledgeGraphError):
    """Raised when a relationship references a non-existent entity."""


class GraphConsistencyError(KnowledgeGraphError):
    """Raised when the graph has consistency issues."""
