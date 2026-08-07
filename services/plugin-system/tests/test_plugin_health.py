"""Tests for the plugin health checker."""

import pytest

from sona_plugins.infrastructure.plugin_health import (
    HealthStatus,
    PluginHealthChecker,
)


@pytest.fixture
def checker() -> PluginHealthChecker:
    hc = PluginHealthChecker(unhealthy_threshold=3)
    hc.register("plugin-a")
    hc.register("plugin-b")
    return hc


class TestPluginHealthIndividual:
    """Tests for individual health checks."""

    @pytest.mark.asyncio
    async def test_healthy_check(self, checker: PluginHealthChecker) -> None:
        result = await checker.check("plugin-a", healthy=True, message="OK")
        assert result.status == HealthStatus.HEALTHY
        assert result.plugin_id == "plugin-a"

    @pytest.mark.asyncio
    async def test_single_failure_is_degraded(self, checker: PluginHealthChecker) -> None:
        result = await checker.check("plugin-a", healthy=False, message="Error")
        assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_multiple_failures_becomes_unhealthy(self, checker: PluginHealthChecker) -> None:
        await checker.check("plugin-a", healthy=False)
        await checker.check("plugin-a", healthy=False)
        result = await checker.check("plugin-a", healthy=False)
        assert result.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_recovery_resets_failures(self, checker: PluginHealthChecker) -> None:
        await checker.check("plugin-a", healthy=False)
        await checker.check("plugin-a", healthy=False)
        result = await checker.check("plugin-a", healthy=True)
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_get_status(self, checker: PluginHealthChecker) -> None:
        await checker.check("plugin-a", healthy=True)
        assert checker.get_status("plugin-a") == HealthStatus.HEALTHY

    def test_get_status_unknown(self, checker: PluginHealthChecker) -> None:
        assert checker.get_status("plugin-a") == HealthStatus.UNKNOWN

    @pytest.mark.asyncio
    async def test_get_last_check(self, checker: PluginHealthChecker) -> None:
        await checker.check("plugin-a", healthy=True, message="OK")
        last = checker.get_last_check("plugin-a")
        assert last is not None
        assert last.message == "OK"

    def test_get_last_check_none(self, checker: PluginHealthChecker) -> None:
        assert checker.get_last_check("plugin-a") is None


class TestPluginHealthAggregate:
    """Tests for aggregate health."""

    @pytest.mark.asyncio
    async def test_all_healthy(self, checker: PluginHealthChecker) -> None:
        await checker.check("plugin-a", healthy=True)
        await checker.check("plugin-b", healthy=True)
        agg = checker.get_aggregate_health()
        assert agg.status == HealthStatus.HEALTHY
        assert agg.healthy == 2
        assert agg.unhealthy == 0

    @pytest.mark.asyncio
    async def test_one_degraded(self, checker: PluginHealthChecker) -> None:
        await checker.check("plugin-a", healthy=True)
        await checker.check("plugin-b", healthy=False)
        agg = checker.get_aggregate_health()
        assert agg.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_one_unhealthy(self, checker: PluginHealthChecker) -> None:
        await checker.check("plugin-a", healthy=True)
        for _ in range(3):
            await checker.check("plugin-b", healthy=False)
        agg = checker.get_aggregate_health()
        assert agg.status == HealthStatus.UNHEALTHY
        assert agg.unhealthy == 1

    def test_all_unknown(self, checker: PluginHealthChecker) -> None:
        agg = checker.get_aggregate_health()
        assert agg.status == HealthStatus.UNKNOWN
        assert agg.unknown == 2
        assert agg.total == 2


class TestPluginHealthManagement:
    """Tests for manual health management."""

    def test_mark_healthy(self, checker: PluginHealthChecker) -> None:
        checker.mark_healthy("plugin-a")
        assert checker.get_status("plugin-a") == HealthStatus.HEALTHY

    def test_mark_unhealthy(self, checker: PluginHealthChecker) -> None:
        checker.mark_unhealthy("plugin-a", reason="forced")
        assert checker.get_status("plugin-a") == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_get_unhealthy_plugins(self, checker: PluginHealthChecker) -> None:
        for _ in range(3):
            await checker.check("plugin-a", healthy=False)
        unhealthy = checker.get_unhealthy_plugins()
        assert "plugin-a" in unhealthy

    def test_unregister(self, checker: PluginHealthChecker) -> None:
        checker.unregister("plugin-a")
        assert checker.get_status("plugin-a") == HealthStatus.UNKNOWN

    def test_register_and_unregister(self, checker: PluginHealthChecker) -> None:
        checker.register("plugin-c")
        assert checker.get_status("plugin-c") == HealthStatus.UNKNOWN
        checker.unregister("plugin-c")
        assert checker.get_status("plugin-c") == HealthStatus.UNKNOWN
