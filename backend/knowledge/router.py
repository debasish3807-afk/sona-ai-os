"""Knowledge Graph REST API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from knowledge.exceptions import EntityNotFoundError
from knowledge.schemas import (
    EntityCreate,
    EntityResponse,
    EntityUpdate,
    GraphResponse,
    RelationshipCreate,
    RelationshipResponse,
    ValidationResponse,
)
from knowledge.services import KnowledgeGraphService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

_service = KnowledgeGraphService()


def _entity_to_response(e) -> EntityResponse:
    return EntityResponse(
        entity_id=e.entity_id,
        entity_type=e.entity_type.value,
        name=e.name,
        description=e.description,
        metadata=e.metadata,
        tags=e.tags,
        created_at=e.created_at.isoformat(),
        updated_at=e.updated_at.isoformat(),
    )


def _rel_to_response(r) -> RelationshipResponse:
    return RelationshipResponse(
        relationship_id=r.relationship_id,
        source_id=r.source_id,
        target_id=r.target_id,
        relation_type=r.relation_type.value,
        weight=r.weight,
        metadata=r.metadata,
        created_at=r.created_at.isoformat(),
    )


@router.get("/entities", response_model=list[EntityResponse])
async def list_entities(entity_type: str | None = None, tag: str | None = None, limit: int = 100):
    return [
        _entity_to_response(e)
        for e in _service.entities.list(entity_type=entity_type, tag=tag, limit=limit)
    ]


@router.post("/entities", response_model=EntityResponse, status_code=201)
async def create_entity(body: EntityCreate):
    from knowledge.models import EntityType, KnowledgeEntity

    etype = EntityType.CUSTOM
    try:
        etype = EntityType(body.entity_type)
    except ValueError:
        raise HTTPException(400, f"Invalid entity type: {body.entity_type}") from None
    entity = KnowledgeEntity(
        name=body.name,
        entity_type=etype,
        description=body.description,
        metadata=body.metadata,
        tags=body.tags,
    )
    _service.entities.create(entity)
    return _entity_to_response(entity)


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: str):
    try:
        return _entity_to_response(_service.entities.get(entity_id))
    except EntityNotFoundError:
        raise HTTPException(404, f"Entity {entity_id} not found") from None


@router.put("/entities/{entity_id}", response_model=EntityResponse)
async def update_entity(entity_id: str, body: EntityUpdate):
    try:
        kwargs = body.model_dump(exclude_none=True)
        entity = _service.entities.update(entity_id, **kwargs)
        return _entity_to_response(entity)
    except EntityNotFoundError:
        raise HTTPException(404, f"Entity {entity_id} not found") from None


@router.delete("/entities/{entity_id}")
async def delete_entity(entity_id: str):
    if not _service.entities.delete(entity_id):
        raise HTTPException(404, f"Entity {entity_id} not found") from None
    return {"status": "deleted", "entity_id": entity_id}


@router.post("/relationships", response_model=RelationshipResponse, status_code=201)
async def create_relationship(body: RelationshipCreate):
    from knowledge.models import KnowledgeRelationship, RelationType

    try:
        rtype = RelationType(body.relation_type)
    except ValueError:
        raise HTTPException(400, f"Invalid relation type: {body.relation_type}") from None
    rel = KnowledgeRelationship(
        source_id=body.source_id,
        target_id=body.target_id,
        relation_type=rtype,
        weight=body.weight,
        metadata=body.metadata,
    )
    try:
        rid = _service.relationships.create(rel)
        return _rel_to_response(_service.relationships.get(rid))
    except Exception as exc:
        raise HTTPException(400, str(exc)) from None


@router.get("/graph", response_model=GraphResponse)
async def get_graph(entity_type: str | None = None, limit: int = 200):
    entities = _service.entities.list(entity_type=entity_type, limit=limit)
    rels = _service.relationships.list()
    return GraphResponse(
        entities=[_entity_to_response(e) for e in entities],
        relationships=[_rel_to_response(r) for r in rels],
    )


@router.get("/search")
async def search_graph(q: str = "", entity_type: str | None = None):
    results = _service.query.search_text(q)
    if entity_type:
        results = [r for r in results if r.entity_type.value == entity_type]
    return {"results": [_entity_to_response(r) for r in results], "count": len(results)}


@router.get("/stats")
async def graph_stats():
    return _service.query.stats()


@router.get("/validate", response_model=ValidationResponse)
async def validate_graph():
    result = _service.validator.validate()
    return ValidationResponse(
        valid=result.valid,
        errors=result.errors,
        warnings=result.warnings,
        duplicate_entities=result.duplicate_entities,
        invalid_relationships=result.invalid_relationships,
        orphan_nodes=result.orphan_nodes,
    )


@router.get("/traverse/{entity_id}")
async def traverse(entity_id: str, mode: str = "bfs", depth: int = 5):
    try:
        if mode == "dfs":
            nodes = _service.graph.dfs(entity_id, max_depth=depth)
            return {"entities": [_entity_to_response(e) for e in nodes], "mode": mode}
        levels = _service.graph.bfs(entity_id, max_depth=depth)
        flat: list = []
        for level in sorted(levels.keys()):
            flat.extend(levels[level])
        return {
            "entities": [_entity_to_response(e) for e in flat],
            "mode": mode,
            "levels": list(levels.keys()),
        }
    except Exception as exc:
        raise HTTPException(400, str(exc)) from None


@router.get("/path")
async def shortest_path(start: str, end: str):
    path = _service.graph.shortest_path(start, end)
    return {"path": [_entity_to_response(e) for e in path], "length": len(path)}
