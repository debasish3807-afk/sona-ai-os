"""Unit tests for the HealthReporter infrastructure module.

Tests cover component registration, status updates, overall status
computation, and detailed report generation.
"""

from sona_observability.infrastructure.health_reporter import (
    HealthReporter,
    HealthStatus,
)


class TestHealthStatusEnum:
    """Tests for HealthStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """All expected health statuses exist."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"

    def test_status_count(self) -> None:
        """Exactly 3 health statuses exist."""
        assert len(HealthStatus) == 3


class TestComponentRegistration:
    """Tests for registering health components."""

    def test_register_component(self) -> None:
        """Registered component appears in report."""
        reporter = HealthReporter()
        reporter.register_component("database")
        report = reporter.detailed_report()
        assert any(c["name"] == "database" for c in report["components"])

    def test_registered_component_starts_healthy(self) -> None:
        """Newly registered component starts as healthy."""
        reporter = HealthReporter()
        reporter.register_component("cache")
        report = reporter.detailed_report()
        cache = next(c for c in report["components"] if c["name"] == "cache")
        assert cache["status"] == "healthy"

    def test_register_multiple_components(self) -> None:
        """Multiple components can be registered."""
        reporter = HealthReporter()
        reporter.register_component("database")
        reporter.register_component("cache")
        reporter.register_component("queue")
        report = reporter.detailed_report()
        assert len(report["components"]) == 3


class TestStatusUpdate:
    """Tests for updating component health status."""

    def test_update_to_degraded(self) -> None:
        """Can update component to degraded status."""
        reporter = HealthReporter()
        reporter.register_component("database")
        reporter.update_status("database", HealthStatus.DEGRADED, "High latency")
        report = reporter.detailed_report()
        db = next(c for c in report["components"] if c["name"] == "database")
        assert db["status"] == "degraded"
        assert db["message"] == "High latency"

    def test_update_to_unhealthy(self) -> None:
        """Can update component to unhealthy status."""
        reporter = HealthReporter()
        reporter.register_component("cache")
        reporter.update_status("cache", HealthStatus.UNHEALTHY, "Connection refused")
        report = reporter.detailed_report()
        cache = next(c for c in report["components"] if c["name"] == "cache")
        assert cache["status"] == "unhealthy"

    def test_update_with_details(self) -> None:
        """Can update with additional detail data."""
        reporter = HealthReporter()
        reporter.register_component("database")
        reporter.update_status(
            "database",
            HealthStatus.DEGRADED,
            "Slow queries",
            details={"avg_latency_ms": 500},
        )
        report = reporter.detailed_report()
        db = next(c for c in report["components"] if c["name"] == "database")
        assert db["details"] == {"avg_latency_ms": 500}

    def test_update_back_to_healthy(self) -> None:
        """Can recover component back to healthy."""
        reporter = HealthReporter()
        reporter.register_component("cache")
        reporter.update_status("cache", HealthStatus.UNHEALTHY)
        reporter.update_status("cache", HealthStatus.HEALTHY)
        report = reporter.detailed_report()
        cache = next(c for c in report["components"] if c["name"] == "cache")
        assert cache["status"] == "healthy"


class TestOverallStatus:
    """Tests for overall health status computation."""

    def test_all_healthy(self) -> None:
        """Overall is healthy when all components are healthy."""
        reporter = HealthReporter()
        reporter.register_component("a")
        reporter.register_component("b")
        assert reporter.overall_status == HealthStatus.HEALTHY

    def test_one_degraded(self) -> None:
        """Overall is degraded when any component is degraded."""
        reporter = HealthReporter()
        reporter.register_component("a")
        reporter.register_component("b")
        reporter.update_status("b", HealthStatus.DEGRADED)
        assert reporter.overall_status == HealthStatus.DEGRADED

    def test_one_unhealthy(self) -> None:
        """Overall is unhealthy when any component is unhealthy."""
        reporter = HealthReporter()
        reporter.register_component("a")
        reporter.register_component("b")
        reporter.update_status("b", HealthStatus.UNHEALTHY)
        assert reporter.overall_status == HealthStatus.UNHEALTHY

    def test_unhealthy_takes_precedence_over_degraded(self) -> None:
        """Unhealthy takes precedence over degraded."""
        reporter = HealthReporter()
        reporter.register_component("a")
        reporter.register_component("b")
        reporter.register_component("c")
        reporter.update_status("a", HealthStatus.DEGRADED)
        reporter.update_status("b", HealthStatus.UNHEALTHY)
        assert reporter.overall_status == HealthStatus.UNHEALTHY

    def test_empty_reporter_is_healthy(self) -> None:
        """Empty reporter (no components) is healthy."""
        reporter = HealthReporter()
        assert reporter.overall_status == HealthStatus.HEALTHY


class TestDetailedReport:
    """Tests for detailed report generation."""

    def test_report_has_overall_status(self) -> None:
        """Report includes overall status."""
        reporter = HealthReporter()
        report = reporter.detailed_report()
        assert "status" in report

    def test_report_has_components(self) -> None:
        """Report includes components list."""
        reporter = HealthReporter()
        report = reporter.detailed_report()
        assert "components" in report
        assert isinstance(report["components"], list)

    def test_report_component_fields(self) -> None:
        """Each component has name and status."""
        reporter = HealthReporter()
        reporter.register_component("test-svc")
        report = reporter.detailed_report()
        comp = report["components"][0]
        assert "name" in comp
        assert "status" in comp

    def test_report_includes_message_when_set(self) -> None:
        """Component message is included when set."""
        reporter = HealthReporter()
        reporter.register_component("db")
        reporter.update_status("db", HealthStatus.DEGRADED, "Slow")
        report = reporter.detailed_report()
        comp = report["components"][0]
        assert comp["message"] == "Slow"

    def test_report_excludes_empty_message(self) -> None:
        """Component without message doesn't include message key."""
        reporter = HealthReporter()
        reporter.register_component("db")
        report = reporter.detailed_report()
        comp = report["components"][0]
        assert "message" not in comp
