"""Tests for the startup validator."""

from conftest import (
    FakeDegradedCheck,
    FakeHealthyCheck,
    FakeUnhealthyCheck,
)

from sona_shared.health.checks import HealthManager
from sona_shared.infra.startup import StartupValidator


class TestStartupValidator:
    """Tests for StartupValidator."""

    async def test_validate_all_healthy(self) -> None:
        """Validation passes when all checks are healthy."""
        manager = HealthManager()
        manager.register(FakeHealthyCheck())
        validator = StartupValidator(manager)
        result = await validator.validate()
        assert result is True

    async def test_validate_with_unhealthy(self) -> None:
        """Validation fails when a check is unhealthy."""
        manager = HealthManager()
        manager.register(FakeUnhealthyCheck())
        validator = StartupValidator(manager)
        result = await validator.validate()
        assert result is False

    async def test_validate_required_service_missing(self) -> None:
        """Validation fails when required service has no check."""
        manager = HealthManager()
        manager.register(FakeHealthyCheck())
        validator = StartupValidator(manager, required_services=["nonexistent"])
        result = await validator.validate()
        assert result is False

    async def test_validate_required_service_unhealthy(self) -> None:
        """Validation fails when required service is unhealthy."""
        manager = HealthManager()
        manager.register(FakeUnhealthyCheck())
        validator = StartupValidator(manager, required_services=["fake_unhealthy"])
        result = await validator.validate()
        assert result is False

    async def test_validate_degraded_is_acceptable(self) -> None:
        """Validation passes when services are degraded but not unhealthy."""
        manager = HealthManager()
        manager.register(FakeDegradedCheck())
        validator = StartupValidator(manager, required_services=["fake_degraded"])
        result = await validator.validate()
        assert result is True

    async def test_wait_for_ready_immediate_success(self) -> None:
        """wait_for_ready returns True on first try if all healthy."""
        manager = HealthManager()
        manager.register(FakeHealthyCheck())
        validator = StartupValidator(manager, max_retries=3, retry_delay=0.01)
        result = await validator.wait_for_ready()
        assert result is True

    async def test_wait_for_ready_all_retries_fail(self) -> None:
        """wait_for_ready returns False after exhausting retries."""
        manager = HealthManager()
        manager.register(FakeUnhealthyCheck())
        validator = StartupValidator(manager, max_retries=2, retry_delay=0.01)
        result = await validator.wait_for_ready()
        assert result is False
