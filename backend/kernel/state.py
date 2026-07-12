"""Kernel state management.

Manages the global state of the AI kernel including operational
status, resource utilization, and runtime metrics.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class KernelStatus(str, Enum):
    """Overall kernel operational status."""

    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ResourceMetrics:
    """Resource utilization metrics.

    Attributes:
        active_sessions: Number of active sessions.
        active_tasks: Number of tasks currently executing.
        pending_tasks: Number of tasks waiting in queue.
        total_requests: Cumulative requests processed.
        total_tokens_used: Cumulative token consumption.
        avg_latency_ms: Average response latency.
        error_rate: Error rate as a ratio (0-1).
        uptime_seconds: Kernel uptime in seconds.
    """

    active_sessions: int = 0
    active_tasks: int = 0
    pending_tasks: int = 0
    total_requests: int = 0
    total_tokens_used: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    uptime_seconds: float = 0.0


@dataclass
class ProviderStatus:
    """Status of a registered provider.

    Attributes:
        provider_id: Provider identifier.
        name: Human-readable name.
        is_available: Whether the provider is reachable.
        models_available: Number of available models.
        current_rpm: Current requests per minute.
        rate_limit_rpm: Rate limit ceiling.
        last_health_check: Timestamp of last health check.
        error_count: Recent error count.
    """

    provider_id: str
    name: str
    is_available: bool = True
    models_available: int = 0
    current_rpm: int = 0
    rate_limit_rpm: int = 60
    last_health_check: datetime | None = None
    error_count: int = 0


@dataclass
class KernelState:
    """Complete snapshot of kernel state.

    Attributes:
        status: Overall kernel status.
        metrics: Resource utilization metrics.
        providers: Status of all registered providers.
        started_at: Kernel start timestamp.
        last_updated: Last state update timestamp.
        version: Kernel version string.
        metadata: Additional state metadata.
    """

    status: KernelStatus = KernelStatus.STOPPED
    metrics: ResourceMetrics = field(default_factory=ResourceMetrics)
    providers: list[ProviderStatus] = field(default_factory=list)
    started_at: datetime | None = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: str = "0.1.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_operational(self) -> bool:
        """Check if the kernel is in an operational state."""
        return self.status in (
            KernelStatus.READY,
            KernelStatus.PROCESSING,
            KernelStatus.DEGRADED,
        )

    @property
    def is_accepting_requests(self) -> bool:
        """Check if the kernel can accept new requests."""
        return self.status in (
            KernelStatus.READY,
            KernelStatus.PROCESSING,
        )


class StateManager(ABC):
    """Abstract interface for kernel state management.

    Provides read and write access to the kernel's operational
    state, metrics, and provider status.
    """

    @abstractmethod
    async def get_state(self) -> KernelState:
        """Get the current kernel state snapshot.

        Returns:
            Current KernelState.
        """
        ...

    @abstractmethod
    async def set_status(self, status: KernelStatus) -> None:
        """Update the kernel operational status.

        Args:
            status: New kernel status.
        """
        ...

    @abstractmethod
    async def update_metrics(self, metrics: ResourceMetrics) -> None:
        """Update resource utilization metrics.

        Args:
            metrics: Updated metrics snapshot.
        """
        ...

    @abstractmethod
    async def record_request(
        self,
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        success: bool = True,
    ) -> None:
        """Record a completed request for metrics tracking.

        Args:
            tokens_used: Tokens consumed by the request.
            latency_ms: Request latency in milliseconds.
            success: Whether the request succeeded.
        """
        ...

    @abstractmethod
    async def update_provider_status(
        self,
        provider_status: ProviderStatus,
    ) -> None:
        """Update the status of a registered provider.

        Args:
            provider_status: Updated provider status.
        """
        ...

    @abstractmethod
    async def get_provider_status(
        self,
        provider_id: str,
    ) -> ProviderStatus | None:
        """Get the status of a specific provider.

        Args:
            provider_id: The provider identifier.

        Returns:
            ProviderStatus or None if not found.
        """
        ...

    @abstractmethod
    async def reset_metrics(self) -> None:
        """Reset all metrics counters to zero."""
        ...
