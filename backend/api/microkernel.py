"""Microkernel API endpoints — system introspection and control."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from core.container import get_container
from microkernel.interrupt_handler import InterruptType

router = APIRouter(prefix="/microkernel", tags=["microkernel"])


def _get_kernel() -> Any:
    """Get the Microkernel from DI container."""
    return get_container().resolve("microkernel")


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """Get the current microkernel status."""
    return dict(_get_kernel().get_status())


@router.get("/services")
async def list_services() -> dict[str, Any]:
    """List all registered services."""
    registry = get_container().resolve("service_registry")
    services = registry.list_all()
    return {
        "count": len(services),
        "services": [svc.to_dict() for svc in services],
    }


@router.get("/health")
async def get_health() -> dict[str, Any]:
    """Get health status of all components."""
    monitor = get_container().resolve("health_monitor")
    return dict(monitor.get_summary())


@router.get("/ipc/stats")
async def get_ipc_stats() -> dict[str, Any]:
    """Get IPC bus statistics."""
    ipc = get_container().resolve("ipc_bus")
    return dict(ipc.get_channel_stats())


@router.get("/processes")
async def list_processes() -> dict[str, Any]:
    """List all supervised processes."""
    supervisor = get_container().resolve("process_supervisor")
    processes = supervisor.list_all()
    return {
        "count": len(processes),
        "processes": [
            {
                "process_id": p.process_id,
                "name": p.name,
                "state": p.state.value,
                "service_id": p.service_id,
                "restart_count": p.restart_count,
            }
            for p in processes
        ],
    }


@router.get("/scheduler")
async def get_scheduler() -> dict[str, Any]:
    """Get resource scheduler state."""
    scheduler = get_container().resolve("resource_scheduler")
    return {
        "usage": scheduler.get_usage(),
        "available": scheduler.get_available().to_dict(),
        "allocations": len(scheduler.list_allocations()),
    }


@router.get("/telemetry")
async def get_telemetry() -> dict[str, Any]:
    """Get telemetry summary."""
    telemetry = get_container().resolve("microkernel_telemetry")
    return dict(telemetry.get_summary())


@router.post("/interrupt")
async def trigger_interrupt(
    interrupt_type: str = "user_stop", target: str = "", reason: str = ""
) -> dict[str, Any]:
    """Trigger an interrupt."""
    _get_kernel()
    try:
        itype = InterruptType(interrupt_type)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid interrupt type: {interrupt_type}"
        ) from None

    handler = get_container().resolve("microkernel")
    request = handler._interrupt_handler.request_interrupt(itype, target=target, reason=reason)
    return {
        "interrupt_id": request.interrupt_id,
        "interrupt_type": request.interrupt_type.value,
        "target_process": request.target_process,
        "reason": request.reason,
        "timestamp": request.timestamp,
    }
