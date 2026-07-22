"""Memory Engine API — CRUD, search, import/export, and statistics."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    memory_type: str = "conversation"
    scope: str = "session"
    session_id: str = ""
    user_id: str = ""
    importance_score: float = 0.5
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryUpdateRequest(BaseModel):
    content: str | None = None
    importance_score: float | None = None
    pinned: bool | None = None
    metadata: dict[str, Any] | None = None


class MemoryResponse(BaseModel):
    entry_id: str
    content: str
    memory_type: str
    scope: str
    session_id: str
    user_id: str
    importance_score: float
    tags: list[str]
    metadata: dict[str, Any]
    created_at: float
    accessed_at: float
    pinned: bool


_MEMORY_STORE = None


async def _get_store():
    global _MEMORY_STORE
    if _MEMORY_STORE is None:
        from memory.persistent_store import PersistentMemoryStore

        _MEMORY_STORE = PersistentMemoryStore(
            db_path=__import__("os").environ.get("MEMORY_DB_PATH", "sona_memory.db")
        )
        await _MEMORY_STORE.initialize()
    return _MEMORY_STORE


def _to_response(e) -> MemoryResponse:
    return MemoryResponse(
        entry_id=e.entry_id,
        content=e.content,
        memory_type=e.memory_type.value,
        scope=e.scope.value,
        session_id=e.session_id or "",
        user_id=e.user_id or "",
        importance_score=e.importance_score,
        tags=[t.name for t in e.tags],
        metadata=e.metadata,
        created_at=e.created_at.timestamp()
        if hasattr(e.created_at, "timestamp")
        else float(e.created_at),
        accessed_at=e.accessed_at.timestamp()
        if hasattr(e.accessed_at, "timestamp")
        else float(e.accessed_at),
        pinned=e.pinned,
    )


@router.post("/store", response_model=MemoryResponse, status_code=201)
async def store_memory(body: MemoryCreateRequest):
    store = await _get_store()
    from memory.types import MemoryEntry, MemoryScope, MemoryTag, MemoryType

    entry = MemoryEntry(
        content=body.content,
        memory_type=MemoryType(body.memory_type),
        scope=MemoryScope(body.scope),
        session_id=body.session_id,
        user_id=body.user_id,
        importance_score=body.importance_score,
        tags=[MemoryTag(name=t) for t in body.tags],
        metadata=body.metadata,
    )
    eid = await store.store(entry)
    stored = await store.get(eid)
    if stored is None:
        raise HTTPException(status_code=500, detail="Failed to store memory")
    return _to_response(stored)


@router.get("/get/{entry_id}", response_model=MemoryResponse)
async def get_memory(entry_id: str):
    store = await _get_store()
    entry = await store.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return _to_response(entry)


@router.patch("/update/{entry_id}", response_model=MemoryResponse)
async def update_memory(entry_id: str, body: MemoryUpdateRequest):
    store = await _get_store()
    kwargs = {k: v for k, v in body.model_dump(exclude_none=True).items() if v is not None}
    if not kwargs:
        entry = await store.get(entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        return _to_response(entry)
    updated = await store.update(entry_id, **kwargs)
    if updated is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return _to_response(updated)


@router.delete("/delete/{entry_id}")
async def delete_memory(entry_id: str):
    store = await _get_store()
    deleted = await store.delete(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", "entry_id": entry_id}


@router.get("/list", response_model=dict)
async def list_memories(
    memory_type: str | None = Query(None),
    scope: str | None = Query(None),
    user_id: str | None = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
):
    store = await _get_store()
    entries = await store.list_memories(
        memory_type=memory_type, scope=scope, user_id=user_id, limit=limit, offset=offset
    )
    total = await store.count(memory_type=memory_type)
    return {
        "entries": [_to_response(e) for e in entries],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/search", response_model=dict)
async def search_memories(q: str = Query(..., min_length=1), top_k: int = Query(10, le=100)):
    store = await _get_store()
    results = await store.search(q, top_k=top_k)
    return {"entries": [_to_response(r.entry) for r in results], "count": len(results)}


@router.post("/import")
async def import_memories(file_path: str):
    store = await _get_store()
    count = await store.import_json(file_path)
    return {"imported": count, "file": file_path}


@router.post("/export")
async def export_memories(file_path: str, memory_type: str | None = Query(None)):
    store = await _get_store()
    filters = {}
    if memory_type:
        filters["memory_type"] = memory_type
    count = await store.export_json(file_path, **filters)
    return {"exported": count, "file": file_path}


@router.get("/stats", response_model=dict)
async def memory_stats():
    store = await _get_store()
    stats = await store.get_stats()
    return {
        "total_entries": stats.total_entries,
        "entries_by_type": {
            k.value if hasattr(k, "value") else k: v for k, v in stats.by_type.items()
        },
        "pinned_count": stats.pinned_count,
        "expired_count": stats.expired_count,
    }
