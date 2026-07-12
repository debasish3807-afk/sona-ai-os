"""Memory & Knowledge Engine adapter for the runtime layer."""

from __future__ import annotations

from adapters.schemas import RuntimeService, ServiceStatus
from config.logging import get_logger

logger = get_logger(__name__)


class MemoryAdapter:
    """Bridges the Memory & Knowledge Engine into the runtime."""

    service_id: str = "memory_engine"
    name: str = "Memory & Knowledge Engine"
    dependencies: list[str] = []

    def __init__(self) -> None:
        self._status: ServiceStatus = ServiceStatus.REGISTERED
        self._initialized: bool = False

    async def start(self) -> None:
        """Initialize the memory engine adapter."""
        self._status = ServiceStatus.STARTING
        logger.info("memory_adapter_starting")
        self._initialized = True
        self._status = ServiceStatus.RUNNING
        logger.info("memory_adapter_running")

    async def stop(self) -> None:
        """Shut down the memory engine adapter."""
        self._status = ServiceStatus.STOPPED
        self._initialized = False
        logger.info("memory_adapter_stopped")

    async def health(self) -> bool:
        """Return health status."""
        return self._status == ServiceStatus.RUNNING and self._initialized

    def get_info(self) -> RuntimeService:
        """Return runtime service descriptor."""
        return RuntimeService(
            service_id=self.service_id,
            name=self.name,
            adapter_type="memory",
            status=self._status,
            priority=30,
            dependencies=list(self.dependencies),
            metadata={"initialized": self._initialized},
        )
