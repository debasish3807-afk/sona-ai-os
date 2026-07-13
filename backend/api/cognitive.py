"""Cognitive Kernel API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from core.container import get_container

router = APIRouter(prefix="/kernel", tags=["kernel"])


def _get_kernel() -> Any:
    """Get CognitiveKernel from DI container."""
    return get_container().resolve("cognitive_kernel")


@router.get("/status")
async def kernel_status() -> dict[str, Any]:
    return dict(_get_kernel().get_status())


@router.get("/metrics")
async def kernel_metrics() -> dict[str, Any]:
    return {"success": True, "metrics": _get_kernel().metrics.to_dict()}


@router.get("/world")
async def kernel_world() -> dict[str, Any]:
    return {"success": True, "world": _get_kernel().world.to_dict()}


@router.get("/events")
async def kernel_events(limit: int = 50) -> dict[str, Any]:
    events = _get_kernel().event_bus.get_history(limit=limit)
    return {"success": True, "events": events, "total": len(events)}


@router.get("/health")
async def kernel_health() -> dict[str, Any]:
    k = _get_kernel()
    engine_health = await k.registry.health_check_all()
    return {
        "success": True,
        "kernel_state": k.state.value,
        "engines": engine_health,
        "healthy": k.state.value in ("ready", "processing"),
    }
