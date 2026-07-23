"""Tests for Production Foundation — Phase 30.1."""

from production.config_loader import ConfigLoader
from production.health import HealthService
from production.system_info import SystemInfoService


class TestConfigLoader:
    def test_load_without_env(self):
        loader = ConfigLoader()
        result = loader.load()
        assert result.success is False  # JWT_SECRET not set
        assert any("JWT_SECRET" in e for e in result.errors)


class TestHealthService:
    def test_initial_state(self):
        h = HealthService()
        result = h.check()
        assert result.healthy  # no components = healthy by default
        assert result.status == "healthy"

    def test_register_and_report(self):
        h = HealthService()
        h.register("api")
        h.register("database", ["api"])
        h.report_healthy("api")
        h.report_healthy("database")
        result = h.check()
        assert result.healthy
        assert result.components["api"] is True

    def test_unhealthy_component(self):
        h = HealthService()
        h.register("db")
        h.report_unhealthy("db", "Connection refused")
        result = h.check()
        assert not result.healthy
        assert result.status == "degraded"
        assert result.details["db"]["message"] == "Connection refused"

    def test_uptime(self):
        import time

        h = HealthService()
        time.sleep(0.01)
        result = h.check()
        assert result.uptime_seconds > 0.0

    def test_component_details(self):
        h = HealthService()
        h.register("cache", ["api"])
        h.report_healthy("cache")
        result = h.check()
        assert "cache" in result.details
        assert result.details["cache"]["dependencies"] == ["api"]


class TestSystemInfoService:
    def test_get_info(self):
        info = SystemInfoService().get_info()
        assert "os" in info
        assert "python" in info
        assert "process" in info
        assert info["os"]["system"]  # should be "Linux", "Darwin", or "Windows"

    def test_get_version(self):
        info = SystemInfoService().get_version_info()
        assert "app_name" in info
        assert "app_version" in info
        assert "python_version" in info
