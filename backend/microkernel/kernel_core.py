"""Kernel Core — the central microkernel orchestrator."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from microkernel.events import MicrokernelEvent, MicrokernelEventType
from microkernel.exceptions import MicrokernelError
from microkernel.health_monitor import HealthMonitor
from microkernel.intent_sanitizer import IntentSanitizer
from microkernel.interrupt_handler import InterruptHandler
from microkernel.ipc_bus import IPCBus
from microkernel.kernel_state import MicrokernelState
from microkernel.process_supervisor import ProcessSupervisor
from microkernel.resource_scheduler import ResourceScheduler
from microkernel.sandbox_manager import SandboxManager
from microkernel.schemas import IPCMessage, KernelStatus, ServiceInfo
from microkernel.service_registry import ServiceRegistry
from microkernel.telemetry import MicrokernelTelemetry

logger = get_logger(__name__)


class Microkernel:
    """Central microkernel orchestrator.

    Coordinates all subsystems: IPC, service registry, sandboxing,
    process supervision, scheduling, security, interrupts, health,
    and telemetry.
    """

    def __init__(
        self,
        ipc_bus: IPCBus,
        service_registry: ServiceRegistry,
        sandbox_manager: SandboxManager,
        process_supervisor: ProcessSupervisor,
        resource_scheduler: ResourceScheduler,
        intent_sanitizer: IntentSanitizer,
        interrupt_handler: InterruptHandler,
        health_monitor: HealthMonitor,
        telemetry: MicrokernelTelemetry,
    ) -> None:
        self._ipc_bus = ipc_bus
        self._service_registry = service_registry
        self._sandbox_manager = sandbox_manager
        self._process_supervisor = process_supervisor
        self._resource_scheduler = resource_scheduler
        self._intent_sanitizer = intent_sanitizer
        self._interrupt_handler = interrupt_handler
        self._health_monitor = health_monitor
        self._telemetry = telemetry
        self._state = MicrokernelState()
        self._events: list[MicrokernelEvent] = []

    @property
    def state(self) -> MicrokernelState:
        """Access the kernel state."""
        return self._state

    async def start(self) -> None:
        """Start the microkernel and all subsystems."""
        if not self._state.transition(KernelStatus.STARTING):
            raise MicrokernelError("cannot start kernel", component="kernel_core")

        # Register health components
        self._health_monitor.register_component("ipc_bus")
        self._health_monitor.register_component("service_registry")
        self._health_monitor.register_component("sandbox_manager")
        self._health_monitor.register_component("process_supervisor")
        self._health_monitor.register_component("resource_scheduler")

        self._state.transition(KernelStatus.READY)
        self._state.transition(KernelStatus.RUNNING)
        self._emit(MicrokernelEventType.KERNEL_STARTED, "kernel_core", {"status": "running"})
        self._telemetry.increment("kernel_starts")
        logger.info("microkernel_started")

    async def stop(self) -> None:
        """Stop the microkernel gracefully."""
        if not self._state.transition(KernelStatus.SHUTTING_DOWN):
            raise MicrokernelError("cannot stop kernel", component="kernel_core")

        stopped = self._process_supervisor.graceful_shutdown_all()
        self._telemetry.record("processes_stopped", float(stopped), "count", "kernel_core")

        self._state.transition(KernelStatus.STOPPED)
        self._emit(
            MicrokernelEventType.KERNEL_STOPPED, "kernel_core", {"processes_stopped": stopped}
        )
        self._telemetry.increment("kernel_stops")
        logger.info("microkernel_stopped", processes_stopped=stopped)

    async def process_message(self, message: IPCMessage) -> IPCMessage | None:
        """Route a message through the IPC bus."""
        self._state._messages_processed += 1
        self._telemetry.increment("messages_processed")

        success = await self._ipc_bus.send(message)
        if not success:
            self._emit(
                MicrokernelEventType.IPC_MESSAGE_SENT,
                "kernel_core",
                {"message_id": message.message_id, "success": False},
            )
            return None

        self._emit(
            MicrokernelEventType.IPC_MESSAGE_SENT,
            "kernel_core",
            {"message_id": message.message_id, "success": True},
        )
        return message

    def register_service(self, info: ServiceInfo) -> bool:
        """Register a service with the kernel."""
        success = self._service_registry.register(info)
        if success:
            self._state._services_count += 1
            self._emit(
                MicrokernelEventType.WORKER_REGISTERED,
                "kernel_core",
                {"service_id": info.service_id, "name": info.name},
            )
            self._telemetry.increment("services_registered")
        return success

    def get_status(self) -> dict[str, Any]:
        """Get the full kernel status report."""
        return {
            "state": self._state.to_dict(),
            "services": self._service_registry.count,
            "processes": len(self._process_supervisor.list_all()),
            "sandboxes": self._sandbox_manager.count,
            "ipc": self._ipc_bus.get_channel_stats(),
            "health": self._health_monitor.get_summary(),
            "telemetry": self._telemetry.get_summary(),
            "events_count": len(self._events),
        }

    def _emit(self, event_type: MicrokernelEventType, source: str, data: dict[str, Any]) -> None:
        """Emit a kernel event."""
        event = MicrokernelEvent(event_type=event_type, source=source, data=data)
        self._events.append(event)
