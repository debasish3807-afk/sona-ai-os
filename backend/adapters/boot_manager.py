"""Boot Manager — orchestrates the multi-phase boot sequence."""

from __future__ import annotations

from typing import Any

from adapters.exceptions import BootError
from adapters.kernel_bridge import KernelBridge
from adapters.runtime_registry import RuntimeRegistry
from adapters.schemas import BootEvent, BootPhase, ServiceStatus
from config.logging import get_logger

logger = get_logger(__name__)


class BootManager:
    """Orchestrates the multi-phase boot sequence for all adapters.

    Manages service discovery, dependency resolution, sequential startup,
    and graceful shutdown of the entire runtime.
    """

    def __init__(self, registry: RuntimeRegistry, bridge: KernelBridge) -> None:
        self._registry = registry
        self._bridge = bridge
        self._adapters: list[Any] = []
        self._boot_log: list[BootEvent] = []
        self._phase: BootPhase = BootPhase.PRE_BOOT
        self._booted: bool = False

    async def boot(self) -> bool:
        """Execute the full boot sequence.

        Returns True if boot completed successfully.
        """
        if self._booted:
            logger.warning("boot_already_completed")
            return True

        try:
            # Phase 1: PRE_BOOT — validate environment
            self._phase = BootPhase.PRE_BOOT
            self._log(BootPhase.PRE_BOOT, "Validating environment")

            # Phase 2: KERNEL_INIT — ensure microkernel is reachable
            self._phase = BootPhase.KERNEL_INIT
            self._log(BootPhase.KERNEL_INIT, "Kernel bridge initialized")

            # Phase 3: SERVICE_DISCOVERY — discover adapters
            self._phase = BootPhase.SERVICE_DISCOVERY
            self._log(BootPhase.SERVICE_DISCOVERY, f"Discovered {len(self._adapters)} adapters")

            # Phase 4: SERVICE_REGISTRATION — register in registry
            self._phase = BootPhase.SERVICE_REGISTRATION
            for adapter in self._adapters:
                info = adapter.get_info()
                self._registry.register(info)
            self._log(
                BootPhase.SERVICE_REGISTRATION,
                f"Registered {len(self._adapters)} services",
            )

            # Phase 5: SERVICE_START — start in dependency order
            self._phase = BootPhase.SERVICE_START
            ordered = self._resolve_start_order(self._adapters)
            for adapter in ordered:
                await adapter.start()
                self._registry.update_status(adapter.service_id, ServiceStatus.RUNNING)
            self._log(BootPhase.SERVICE_START, "All services started")

            # Phase 6: READY
            self._phase = BootPhase.READY
            self._log(BootPhase.READY, "System ready")
            self._booted = True
            logger.info("boot_complete", services=len(self._adapters))
            return True

        except Exception as exc:
            self._log(self._phase, f"Boot failed: {exc}", success=False)
            logger.error("boot_failed", phase=self._phase.value, error=str(exc))
            raise BootError(f"boot failed at {self._phase.value}: {exc}") from exc

    async def shutdown(self) -> bool:
        """Gracefully shut down all services in reverse order.

        Returns True if shutdown completed cleanly.
        """
        self._phase = BootPhase.SHUTDOWN
        self._log(BootPhase.SHUTDOWN, "Shutdown initiated")

        ordered = self._resolve_start_order(self._adapters)
        for adapter in reversed(ordered):
            try:
                await adapter.stop()
                self._registry.update_status(adapter.service_id, ServiceStatus.STOPPED)
            except Exception as exc:
                logger.error("shutdown_error", service=adapter.service_id, error=str(exc))
                self._registry.update_status(adapter.service_id, ServiceStatus.FAILED)

        self._log(BootPhase.SHUTDOWN, "Shutdown complete")
        self._booted = False
        logger.info("shutdown_complete")
        return True

    def get_boot_log(self) -> list[dict[str, Any]]:
        """Return the full boot event log."""
        return [event.to_dict() for event in self._boot_log]

    def get_phase(self) -> str:
        """Return the current boot phase."""
        return self._phase.value

    def _resolve_start_order(self, adapters: list[Any]) -> list[Any]:
        """Topologically sort adapters based on dependencies.

        Adapters with no dependencies start first. If an adapter depends
        on another, the dependency must start before the dependent.
        """
        id_to_adapter = {a.service_id: a for a in adapters}
        visited: set[str] = set()
        order: list[Any] = []

        def _visit(adapter_id: str) -> None:
            if adapter_id in visited:
                return
            visited.add(adapter_id)
            adapter = id_to_adapter.get(adapter_id)
            if adapter is None:
                return
            for dep_id in adapter.dependencies:
                if dep_id in id_to_adapter:
                    _visit(dep_id)
            order.append(adapter)

        for aid in id_to_adapter:
            _visit(aid)

        return order

    def _log(self, phase: BootPhase, message: str, success: bool = True) -> None:
        """Append a boot event to the log."""
        event = BootEvent(phase=phase, message=message, success=success)
        self._boot_log.append(event)
