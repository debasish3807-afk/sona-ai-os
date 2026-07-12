"""Verification Fabric adapter for the runtime layer."""

from __future__ import annotations

from adapters.schemas import RuntimeService, ServiceStatus
from config.logging import get_logger

logger = get_logger(__name__)


class VerificationAdapter:
    """Bridges the Verification Fabric into the runtime."""

    service_id: str = "verification_engine"
    name: str = "Verification Fabric"
    dependencies: list[str] = ["memory_engine", "capability_fabric"]

    def __init__(self) -> None:
        self._status: ServiceStatus = ServiceStatus.REGISTERED
        self._initialized: bool = False

    async def start(self) -> None:
        """Initialize the verification fabric adapter."""
        self._status = ServiceStatus.STARTING
        logger.info("verification_adapter_starting")
        self._initialized = True
        self._status = ServiceStatus.RUNNING
        logger.info("verification_adapter_running")

    async def stop(self) -> None:
        """Shut down the verification fabric adapter."""
        self._status = ServiceStatus.STOPPED
        self._initialized = False
        logger.info("verification_adapter_stopped")

    async def health(self) -> bool:
        """Return health status."""
        return self._status == ServiceStatus.RUNNING and self._initialized

    def get_info(self) -> RuntimeService:
        """Return runtime service descriptor."""
        return RuntimeService(
            service_id=self.service_id,
            name=self.name,
            adapter_type="verification",
            status=self._status,
            priority=60,
            dependencies=list(self.dependencies),
            metadata={"initialized": self._initialized},
        )
