"""Meta Reasoning Engine adapter for the runtime layer."""

from __future__ import annotations

from adapters.schemas import RuntimeService, ServiceStatus
from config.logging import get_logger

logger = get_logger(__name__)


class MetaReasoningAdapter:
    """Bridges the Meta Reasoning subsystem into the runtime."""

    service_id: str = "meta_reasoner"
    name: str = "Meta Reasoning Engine"
    dependencies: list[str] = ["executive_brain"]

    def __init__(self) -> None:
        self._status: ServiceStatus = ServiceStatus.REGISTERED
        self._initialized: bool = False

    async def start(self) -> None:
        """Initialize the meta reasoning adapter."""
        self._status = ServiceStatus.STARTING
        logger.info("meta_reasoning_adapter_starting")
        self._initialized = True
        self._status = ServiceStatus.RUNNING
        logger.info("meta_reasoning_adapter_running")

    async def stop(self) -> None:
        """Shut down the meta reasoning adapter."""
        self._status = ServiceStatus.STOPPED
        self._initialized = False
        logger.info("meta_reasoning_adapter_stopped")

    async def health(self) -> bool:
        """Return health status."""
        return self._status == ServiceStatus.RUNNING and self._initialized

    def get_info(self) -> RuntimeService:
        """Return runtime service descriptor."""
        return RuntimeService(
            service_id=self.service_id,
            name=self.name,
            adapter_type="meta_reasoning",
            status=self._status,
            priority=20,
            dependencies=list(self.dependencies),
            metadata={"initialized": self._initialized},
        )
