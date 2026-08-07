"""Shared test fixtures for the shared-kernel test suite."""

from sona_shared.health.checks import HealthCheck, HealthCheckResult, HealthStatus


class FakeHealthyCheck(HealthCheck):
    """A health check that always returns healthy."""

    @property
    def name(self) -> str:
        return "fake_healthy"

    async def check(self) -> HealthCheckResult:
        return HealthCheckResult(name=self.name, status=HealthStatus.HEALTHY, latency_ms=1.0)


class FakeUnhealthyCheck(HealthCheck):
    """A health check that always returns unhealthy."""

    @property
    def name(self) -> str:
        return "fake_unhealthy"

    async def check(self) -> HealthCheckResult:
        return HealthCheckResult(
            name=self.name, status=HealthStatus.UNHEALTHY, message="Service down", latency_ms=5.0
        )


class FakeDegradedCheck(HealthCheck):
    """A health check that always returns degraded."""

    @property
    def name(self) -> str:
        return "fake_degraded"

    async def check(self) -> HealthCheckResult:
        return HealthCheckResult(
            name=self.name, status=HealthStatus.DEGRADED, message="Slow", latency_ms=50.0
        )
