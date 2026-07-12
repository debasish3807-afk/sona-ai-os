"""Health monitoring system for AI providers.

Tracks provider health status, manages health checks, and provides
circuit-breaker functionality to avoid sending requests to unhealthy
providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from providers.types import ProviderID


class HealthState(str, Enum):
    """Health state of a provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    CIRCUIT_OPEN = "circuit_open"


class CircuitState(str, Enum):
    """Circuit breaker state."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior.

    Attributes:
        failure_threshold: Failures before opening circuit.
        success_threshold: Successes in half-open before closing.
        timeout_seconds: Seconds before transitioning open -> half-open.
        half_open_max_requests: Max requests in half-open state.
    """

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 60.0
    half_open_max_requests: int = 1


@dataclass
class HealthCheckResult:
    """Result of a single health check.

    Attributes:
        provider_id: The provider that was checked.
        state: Resulting health state.
        latency_ms: Health check latency.
        message: Human-readable status message.
        checked_at: Timestamp of the check.
        details: Additional health check details.
    """

    provider_id: ProviderID
    state: HealthState
    latency_ms: float = 0.0
    message: str = ""
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderHealthStatus:
    """Comprehensive health status for a provider.

    Attributes:
        provider_id: Provider identifier.
        state: Current health state.
        circuit_state: Current circuit breaker state.
        consecutive_failures: Number of consecutive failures.
        consecutive_successes: Number of consecutive successes.
        total_requests: Total requests tracked.
        total_failures: Total failures tracked.
        avg_latency_ms: Average response latency.
        last_check: Last health check result.
        last_success: Timestamp of last successful request.
        last_failure: Timestamp of last failed request.
        metadata: Additional status metadata.
    """

    provider_id: ProviderID
    state: HealthState = HealthState.UNKNOWN
    circuit_state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_requests: int = 0
    total_failures: int = 0
    avg_latency_ms: float = 0.0
    last_check: HealthCheckResult | None = None
    last_success: datetime | None = None
    last_failure: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """Check if the provider is available for requests."""
        return (
            self.state in (HealthState.HEALTHY, HealthState.DEGRADED)
            and self.circuit_state != CircuitState.OPEN
        )

    @property
    def error_rate(self) -> float:
        """Calculate the error rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests


class HealthMonitor(ABC):
    """Abstract interface for provider health monitoring.

    Tracks provider health, manages circuit breakers, and provides
    availability information for provider selection.
    """

    @abstractmethod
    async def check_health(self, provider_id: ProviderID) -> HealthCheckResult:
        """Perform a health check on a specific provider.

        Args:
            provider_id: The provider to check.

        Returns:
            HealthCheckResult with status details.
        """
        ...

    @abstractmethod
    async def check_all(self) -> dict[ProviderID, HealthCheckResult]:
        """Perform health checks on all registered providers.

        Returns:
            Mapping of provider IDs to their health check results.
        """
        ...

    @abstractmethod
    async def record_success(self, provider_id: ProviderID, latency_ms: float) -> None:
        """Record a successful request to a provider.

        Args:
            provider_id: The provider that succeeded.
            latency_ms: Request latency in milliseconds.
        """
        ...

    @abstractmethod
    async def record_failure(self, provider_id: ProviderID, error: Exception | None = None) -> None:
        """Record a failed request to a provider.

        May trigger circuit breaker state transitions.

        Args:
            provider_id: The provider that failed.
            error: Optional exception that caused the failure.
        """
        ...

    @abstractmethod
    async def get_status(self, provider_id: ProviderID) -> ProviderHealthStatus | None:
        """Get the current health status of a provider.

        Args:
            provider_id: The provider to query.

        Returns:
            ProviderHealthStatus or None if not tracked.
        """
        ...

    @abstractmethod
    async def get_all_statuses(self) -> dict[ProviderID, ProviderHealthStatus]:
        """Get health statuses for all tracked providers.

        Returns:
            Mapping of provider IDs to their health statuses.
        """
        ...

    @abstractmethod
    async def get_available_providers(self) -> list[ProviderID]:
        """Get list of providers currently available for requests.

        Only returns providers with healthy/degraded state and
        closed/half-open circuit breakers.

        Returns:
            List of available provider IDs.
        """
        ...

    @abstractmethod
    async def is_available(self, provider_id: ProviderID) -> bool:
        """Check if a specific provider is available.

        Args:
            provider_id: The provider to check.

        Returns:
            True if the provider is available for requests.
        """
        ...

    @abstractmethod
    async def reset(self, provider_id: ProviderID) -> None:
        """Reset health tracking for a provider.

        Clears all metrics and resets circuit breaker.

        Args:
            provider_id: The provider to reset.
        """
        ...
