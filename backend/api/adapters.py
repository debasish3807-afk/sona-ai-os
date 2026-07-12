"""Runtime integration API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/runtime", tags=["runtime"])

# Lazy-initialized globals
_boot_manager: Any = None
_persistence: Any = None


def _get_boot_manager() -> Any:
    """Lazy-initialize the boot manager singleton."""
    global _boot_manager
    if _boot_manager is None:
        from adapters.boot_manager import BootManager
        from adapters.capability_adapter import CapabilityAdapter
        from adapters.executive_adapter import ExecutiveAdapter
        from adapters.kernel_bridge import KernelBridge
        from adapters.memory_adapter import MemoryAdapter
        from adapters.meta_reasoning_adapter import MetaReasoningAdapter
        from adapters.provider_adapter import ProviderAdapter
        from adapters.runtime_registry import RuntimeRegistry
        from adapters.verification_adapter import VerificationAdapter
        from microkernel import (
            HealthMonitor,
            IntentSanitizer,
            InterruptHandler,
            IPCBus,
            Microkernel,
            MicrokernelTelemetry,
            ProcessSupervisor,
            ResourceScheduler,
            SandboxManager,
            ServiceRegistry,
        )

        mk = Microkernel(
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
        registry = RuntimeRegistry()
        bridge = KernelBridge(mk)
        bm = BootManager(registry=registry, bridge=bridge)
        bm._adapters = [
            ExecutiveAdapter(),
            MetaReasoningAdapter(),
            MemoryAdapter(),
            CapabilityAdapter(),
            VerificationAdapter(),
            ProviderAdapter(),
        ]
        _boot_manager = bm
    return _boot_manager


def _get_persistence() -> Any:
    """Lazy-initialize the persistence manager."""
    global _persistence
    if _persistence is None:
        from adapters.persistence import PersistenceManager

        _persistence = PersistenceManager()
    return _persistence


@router.get("/status")
async def get_runtime_status() -> dict[str, Any]:
    """Return current boot phase and services summary."""
    bm = _get_boot_manager()
    return {
        "phase": bm.get_phase(),
        "services": bm._registry.get_status_summary(),
    }


@router.get("/services")
async def get_runtime_services() -> dict[str, Any]:
    """Return all registered runtime services."""
    bm = _get_boot_manager()
    services = bm._registry.list_all()
    return {"services": [s.to_dict() for s in services]}


@router.get("/boot-log")
async def get_boot_log() -> dict[str, Any]:
    """Return the boot sequence event log."""
    bm = _get_boot_manager()
    return {"boot_log": bm.get_boot_log()}


@router.get("/health")
async def get_runtime_health() -> dict[str, Any]:
    """Return aggregated system health from the kernel bridge."""
    bm = _get_boot_manager()
    return {"health": bm._bridge.get_system_health()}


@router.post("/checkpoint")
async def create_checkpoint(state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a persistence checkpoint."""
    pm = _get_persistence()
    await pm.initialize()
    checkpoint_state = state if state is not None else {"phase": _get_boot_manager().get_phase()}
    record_id = await pm.checkpoint(checkpoint_state)
    return {"record_id": record_id, "status": "checkpoint_created"}
