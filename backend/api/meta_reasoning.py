"""Meta Reasoning & Self Reflection API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from core.container import get_container

router = APIRouter(prefix="/meta-reasoning", tags=["meta-reasoning"])


def _get_reasoner() -> Any:
    """Get MetaReasoner from DI container."""
    return get_container().resolve("meta_reasoner")


@router.get("/status")
async def meta_status() -> dict[str, Any]:
    """Get meta-reasoning engine status."""
    return {"success": True, "status": _get_reasoner().get_status()}


@router.post("/reason")
async def reason(body: dict[str, Any]) -> dict[str, Any]:
    """Run meta-reasoning on a plan."""
    reasoner = _get_reasoner()
    plan = body.get("plan", {})
    goal = body.get("goal", {})
    context = body.get("context", {})
    try:
        result = await reasoner.reason(plan, goal, context)
        return {"success": True, "result": result.to_dict()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/trace")
async def get_trace() -> dict[str, Any]:
    """Get reasoning trace."""
    reasoner = _get_reasoner()
    return {"success": True, "trace": reasoner._trace.to_dict()}


@router.get("/events")
async def get_events(limit: int = 50) -> dict[str, Any]:
    """Get recent meta-reasoning events."""
    reasoner = _get_reasoner()
    events = [e.to_dict() for e in reasoner._events[-limit:]]
    return {"success": True, "events": events, "total": len(events)}


@router.get("/memory")
async def get_memory() -> dict[str, Any]:
    """Get reasoning memory stats."""
    reasoner = _get_reasoner()
    return {"success": True, "stats": reasoner._reasoning_memory.stats()}
