"""Capability Fabric API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from capabilities.health import HealthMonitor
from capabilities.loader import CapabilityLoader
from capabilities.manager import CapabilityManager
from capabilities.registry import CapabilityRegistry
from capabilities.selector import CapabilitySelector

router = APIRouter(prefix="/capabilities", tags=["capabilities"])

_manager: CapabilityManager | None = None


def get_manager() -> CapabilityManager:
    """Get or create the global CapabilityManager instance."""
    global _manager
    if _manager is None:
        registry = CapabilityRegistry()
        loader = CapabilityLoader()
        health_monitor = HealthMonitor()
        selector = CapabilitySelector()
        _manager = CapabilityManager(
            registry=registry,
            loader=loader,
            health_monitor=health_monitor,
            selector=selector,
        )
    return _manager


@router.get("/")
async def list_capabilities() -> dict[str, Any]:
    """List all registered capabilities."""
    manager = get_manager()
    status = manager.get_status()
    return {"success": True, "capabilities": status["capabilities"], "total": status["total"]}


@router.get("/{capability_id}")
async def get_capability(capability_id: str) -> dict[str, Any]:
    """Get details for a single capability."""
    manager = get_manager()
    schema = manager._registry.get(capability_id)
    if schema is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    return {"success": True, "capability": schema.to_dict()}


@router.get("/health")
async def health_check_all() -> dict[str, Any]:
    """Health check all registered capabilities."""
    manager = get_manager()
    results = await manager._health_monitor.check_all(manager._registry)
    return {
        "success": True,
        "health": {cap_id: status.to_dict() for cap_id, status in results.items()},
    }


@router.get("/graph")
async def dependency_graph() -> dict[str, Any]:
    """Get the capability dependency graph."""
    manager = get_manager()
    from capabilities.dependency_graph import DependencyGraph

    graph = DependencyGraph()
    for schema in manager._registry.list_all():
        graph.add_node(schema.capability_id)
        for dep in schema.dependencies:
            graph.add_edge(schema.capability_id, dep)
    return {"success": True, "graph": graph.to_dict()}


@router.get("/events")
async def recent_events(limit: int = 50) -> dict[str, Any]:
    """Get recent capability events."""
    manager = get_manager()
    events = manager._events[-limit:]
    return {
        "success": True,
        "events": [e.to_dict() for e in events],
        "total": len(events),
    }


@router.post("/reload")
async def reload_capability(capability_id: str) -> dict[str, Any]:
    """Reload a capability by ID."""
    manager = get_manager()
    schema = manager._registry.get(capability_id)
    if schema is None:
        raise HTTPException(status_code=404, detail="Capability not found")

    instance = await manager._loader.reload(capability_id, manager._registry)
    return {
        "success": instance is not None,
        "capability_id": capability_id,
        "reloaded": instance is not None,
    }
