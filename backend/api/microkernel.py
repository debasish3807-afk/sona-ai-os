"""Microkernel API endpoints — system introspection and control."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from microkernel.health_monitor import HealthMonitor
from microkernel.intent_sanitizer import IntentSanitizer
from microkernel.interrupt_handler import InterruptHandler, InterruptType
from microkernel.ipc_bus import IPCBus
from microkernel.kernel_core import Microkernel
from microkernel.process_supervisor import ProcessSupervisor
from microkernel.resource_scheduler import ResourceScheduler
from microkernel.sandbox_manager import SandboxManager
from microkernel.service_registry import ServiceRegistry
from microkernel.telemetry import MicrokernelTelemetry

router = APIRouter(prefix="/microkernel", tags=["microkernel"])

_kernel: Microkernel | None = None


def get_kernel() -> Microkernel:
    """Get or create the global Microkernel instance."""
    global _kernel
    if _kernel is None:
        _kernel = Microkernel(
            ipc_bus=IPCBus(),
            service_registry=ServiceRegistry(),
            sandbox_manager=SandboxManager(),
            process_supervisor=ProcessSupervisor(),
            resource_scheduler=ResourceScheduler(),
            intent_sanitizer=IntentSanitizer(),
            interrupt_handler=InterruptHandler(),
            health_monitor=HealthMonitor(),
            telemetry=MicrokernelTelemetry(),
        )
    return _kernel


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """Get the current microkernel status."""
    kernel = get_kernel()
    return kernel.get_status()


@router.get("/services")
async def list_services() -> dict[str, Any]:
    """List all registered services."""
    kernel = get_kernel()
    services = kernel._service_registry.list_all()
    return {
        "count": len(services),
        "services": [svc.to_dict() for svc in services],
    }


@router.get("/health")
async def get_health() -> dict[str, Any]:
    """Get health status of all components."""
    kernel = get_kernel()
    return kernel._health_monitor.get_summary()


@router.get("/ipc/stats")
async def get_ipc_stats() -> dict[str, Any]:
    """Get IPC bus statistics."""
    kernel = get_kernel()
    return kernel._ipc_bus.get_channel_stats()


@router.get("/processes")
async def list_processes() -> dict[str, Any]:
    """List all supervised processes."""
    kernel = get_kernel()
    processes = kernel._process_supervisor.list_all()
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
    kernel = get_kernel()
    return {
        "usage": kernel._resource_scheduler.get_usage(),
        "available": kernel._resource_scheduler.get_available().to_dict(),
        "allocations": len(kernel._resource_scheduler.list_allocations()),
    }


@router.get("/telemetry")
async def get_telemetry() -> dict[str, Any]:
    """Get telemetry summary."""
    kernel = get_kernel()
    return kernel._telemetry.get_summary()


@router.post("/interrupt")
async def trigger_interrupt(
    interrupt_type: str = "user_stop", target: str = "", reason: str = ""
) -> dict[str, Any]:
    """Trigger an interrupt."""
    kernel = get_kernel()
    try:
        itype = InterruptType(interrupt_type)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid interrupt type: {interrupt_type}"
        ) from None

    request = kernel._interrupt_handler.request_interrupt(itype, target=target, reason=reason)
    return {
        "interrupt_id": request.interrupt_id,
        "interrupt_type": request.interrupt_type.value,
        "target_process": request.target_process,
        "reason": request.reason,
        "timestamp": request.timestamp,
    }
