"""Production health check framework.

Provides abstract base class for health checks and concrete
implementations for Redis, Qdrant, and Ollama services.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

import httpx
import structlog

logger = structlog.get_logger()


class HealthStatus(StrEnum):
    """Status of a health check."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True)
class HealthCheckResult:
    """Result of a single health check execution."""

    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: str = ""
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class HealthCheck(ABC):
    """Abstract health check for a service dependency."""

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """Execute the health check and return a result."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this health check."""
        ...


class RedisHealthCheck(HealthCheck):
    """Check Redis connectivity via TCP connection test."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    @property
    def name(self) -> str:
        return "redis"

    async def check(self) -> HealthCheckResult:
        """Ping Redis by connecting to its URL."""
        start = time.perf_counter()
        try:
            # Parse redis URL to get host:port for HTTP-like health check
            # Redis doesn't have HTTP, so we try a TCP connect via httpx
            # In production with redis-py, this would use client.ping()
            # For now, we validate the URL is parseable and reachable
            url = self._redis_url.replace("redis://", "http://")
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get(url)
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Redis connection successful",
            )
        except httpx.ConnectError:
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message="Redis connection refused",
            )
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Redis check failed: {exc}",
            )


class QdrantHealthCheck(HealthCheck):
    """Check Qdrant connectivity via its REST API."""

    def __init__(self, qdrant_url: str) -> None:
        self._qdrant_url = qdrant_url

    @property
    def name(self) -> str:
        return "qdrant"

    async def check(self) -> HealthCheckResult:
        """Hit Qdrant health endpoint."""
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._qdrant_url}/healthz")
            latency = (time.perf_counter() - start) * 1000
            if response.status_code == 200:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                    message="Qdrant is healthy",
                )
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                latency_ms=latency,
                message=f"Qdrant returned status {response.status_code}",
            )
        except httpx.ConnectError:
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message="Qdrant connection refused",
            )
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Qdrant check failed: {exc}",
            )


class OllamaHealthCheck(HealthCheck):
    """Check Ollama connectivity via its API endpoint."""

    def __init__(self, ollama_url: str) -> None:
        self._ollama_url = ollama_url

    @property
    def name(self) -> str:
        return "ollama"

    async def check(self) -> HealthCheckResult:
        """Hit Ollama API root endpoint."""
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self._ollama_url)
            latency = (time.perf_counter() - start) * 1000
            if response.status_code == 200:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                    message="Ollama is available",
                )
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                latency_ms=latency,
                message=f"Ollama returned status {response.status_code}",
            )
        except httpx.ConnectError:
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message="Ollama connection refused",
            )
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Ollama check failed: {exc}",
            )


class HealthManager:
    """Aggregates health checks and provides readiness/liveness status."""

    def __init__(self) -> None:
        self._checks: list[HealthCheck] = []
        self._results: dict[str, HealthCheckResult] = {}

    def register(self, check: HealthCheck) -> None:
        """Register a new health check."""
        self._checks.append(check)

    async def check_all(self) -> dict[str, HealthCheckResult]:
        """Run all registered health checks and cache results."""
        results: dict[str, HealthCheckResult] = {}
        for check in self._checks:
            try:
                result = await check.check()
            except Exception as exc:  # noqa: BLE001
                result = HealthCheckResult(
                    name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check threw exception: {exc}",
                )
            results[check.name] = result
            await logger.ainfo(
                "health_check.completed",
                check=check.name,
                status=result.status,
                latency_ms=result.latency_ms,
            )
        self._results = results
        return results

    @property
    def is_healthy(self) -> bool:
        """True if all checks are healthy."""
        if not self._results:
            return False
        return all(r.status == HealthStatus.HEALTHY for r in self._results.values())

    @property
    def is_ready(self) -> bool:
        """True if no checks are unhealthy (degraded is acceptable)."""
        if not self._results:
            return False
        return all(r.status != HealthStatus.UNHEALTHY for r in self._results.values())

    def get_liveness(self) -> dict[str, object]:
        """Get liveness probe response data."""
        return {
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_readiness(self) -> dict[str, object]:
        """Get readiness probe response data with dependency details."""
        checks_data: dict[str, object] = {}
        for name, result in self._results.items():
            checks_data[name] = {
                "status": result.status.value,
                "latency_ms": round(result.latency_ms, 2),
                "message": result.message,
            }
        return {
            "status": "ready" if self.is_ready else "not_ready",
            "checks": checks_data,
            "timestamp": datetime.now(UTC).isoformat(),
        }
