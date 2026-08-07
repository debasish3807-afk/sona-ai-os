"""Tests for the health check framework."""

from sona_shared.health.checks import (
    HealthCheck,
    HealthCheckResult,
    HealthManager,
    HealthStatus,
    OllamaHealthCheck,
    QdrantHealthCheck,
    RedisHealthCheck,
)


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_values(self) -> None:
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_create_result(self) -> None:
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            latency_ms=1.5,
            message="OK",
        )
        assert result.name == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms == 1.5
        assert result.message == "OK"
        assert result.checked_at is not None

    def test_defaults(self) -> None:
        result = HealthCheckResult(name="x", status=HealthStatus.UNHEALTHY)
        assert result.latency_ms == 0.0
        assert result.message == ""


class FakeHealthyCheck(HealthCheck):
    """A fake health check that always returns healthy."""

    @property
    def name(self) -> str:
        return "fake_healthy"

    async def check(self) -> HealthCheckResult:
        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            latency_ms=1.0,
            message="OK",
        )


class FakeUnhealthyCheck(HealthCheck):
    """A fake health check that always returns unhealthy."""

    @property
    def name(self) -> str:
        return "fake_unhealthy"

    async def check(self) -> HealthCheckResult:
        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.UNHEALTHY,
            latency_ms=5.0,
            message="Service down",
        )


class FakeDegradedCheck(HealthCheck):
    """A fake health check that always returns degraded."""

    @property
    def name(self) -> str:
        return "fake_degraded"

    async def check(self) -> HealthCheckResult:
        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.DEGRADED,
            latency_ms=3.0,
            message="Slow response",
        )


class TestHealthManager:
    """Tests for HealthManager."""

    async def test_no_checks_is_not_healthy(self) -> None:
        manager = HealthManager()
        assert manager.is_healthy is False
        assert manager.is_ready is False

    async def test_all_healthy(self) -> None:
        manager = HealthManager()
        manager.register(FakeHealthyCheck())
        await manager.check_all()
        assert manager.is_healthy is True
        assert manager.is_ready is True

    async def test_unhealthy_check_makes_not_ready(self) -> None:
        manager = HealthManager()
        manager.register(FakeHealthyCheck())
        manager.register(FakeUnhealthyCheck())
        await manager.check_all()
        assert manager.is_healthy is False
        assert manager.is_ready is False

    async def test_degraded_is_ready_but_not_healthy(self) -> None:
        manager = HealthManager()
        manager.register(FakeHealthyCheck())
        manager.register(FakeDegradedCheck())
        await manager.check_all()
        assert manager.is_healthy is False
        assert manager.is_ready is True

    async def test_get_liveness(self) -> None:
        manager = HealthManager()
        liveness = manager.get_liveness()
        assert liveness["status"] == "alive"
        assert "timestamp" in liveness

    async def test_get_readiness(self) -> None:
        manager = HealthManager()
        manager.register(FakeHealthyCheck())
        await manager.check_all()
        readiness = manager.get_readiness()
        assert readiness["status"] == "ready"
        assert "checks" in readiness
        assert "fake_healthy" in readiness["checks"]

    async def test_check_exception_handled(self) -> None:
        """Check that exceptions in health checks are caught."""

        class ExplodingCheck(HealthCheck):
            @property
            def name(self) -> str:
                return "exploding"

            async def check(self) -> HealthCheckResult:
                raise RuntimeError("boom")

        manager = HealthManager()
        manager.register(ExplodingCheck())
        results = await manager.check_all()
        assert "exploding" in results
        assert results["exploding"].status == HealthStatus.UNHEALTHY


class TestRedisHealthCheck:
    """Tests for RedisHealthCheck."""

    async def test_name(self) -> None:
        check = RedisHealthCheck("redis://localhost:6379/0")
        assert check.name == "redis"

    async def test_unhealthy_on_connection_error(self) -> None:
        """Redis check returns unhealthy when connection fails."""
        check = RedisHealthCheck("redis://nonexistent:9999/0")
        result = await check.check()
        assert result.status == HealthStatus.UNHEALTHY


class TestQdrantHealthCheck:
    """Tests for QdrantHealthCheck."""

    async def test_name(self) -> None:
        check = QdrantHealthCheck("http://localhost:6333")
        assert check.name == "qdrant"

    async def test_unhealthy_on_connection_error(self) -> None:
        """Qdrant check returns unhealthy when connection fails."""
        check = QdrantHealthCheck("http://nonexistent:9999")
        result = await check.check()
        assert result.status == HealthStatus.UNHEALTHY


class TestOllamaHealthCheck:
    """Tests for OllamaHealthCheck."""

    async def test_name(self) -> None:
        check = OllamaHealthCheck("http://localhost:11434")
        assert check.name == "ollama"

    async def test_unhealthy_on_connection_error(self) -> None:
        """Ollama check returns unhealthy when connection fails."""
        check = OllamaHealthCheck("http://nonexistent:9999")
        result = await check.check()
        assert result.status == HealthStatus.UNHEALTHY
