"""Startup validation and dependency checking.

Validates all required services are available before the application
begins accepting traffic.
"""

import asyncio

import structlog

from sona_shared.health.checks import HealthManager, HealthStatus

logger = structlog.get_logger()


class StartupValidator:
    """Validates all required services are available before accepting traffic.

    Runs health checks with configurable retries and exponential backoff
    to give infrastructure time to become ready.
    """

    def __init__(
        self,
        health_manager: HealthManager,
        required_services: list[str] | None = None,
        max_retries: int = 5,
        retry_delay: float = 2.0,
    ) -> None:
        self._health_manager = health_manager
        self._required_services = required_services or []
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def validate(self) -> bool:
        """Run startup validation once.

        Returns True if all required services are up, or if no required
        services are specified and overall status is ready.
        """
        results = await self._health_manager.check_all()

        if not self._required_services:
            return self._health_manager.is_ready

        for service in self._required_services:
            if service not in results:
                await logger.aerror(
                    "startup.missing_check",
                    service=service,
                    message="Required service has no health check registered",
                )
                return False
            if results[service].status == HealthStatus.UNHEALTHY:
                await logger.aerror(
                    "startup.service_unhealthy",
                    service=service,
                    message=results[service].message,
                )
                return False

        return True

    async def wait_for_ready(self) -> bool:
        """Wait for all services to be ready with exponential backoff retry.

        Returns True if all required services become healthy within the
        retry budget, False otherwise.
        """
        for attempt in range(self._max_retries):
            is_valid = await self.validate()
            if is_valid:
                await logger.ainfo(
                    "startup.ready",
                    attempt=attempt + 1,
                    message="All required services are available",
                )
                return True

            delay = self._retry_delay * (2**attempt)
            await logger.awarning(
                "startup.not_ready",
                attempt=attempt + 1,
                max_retries=self._max_retries,
                retry_in=delay,
            )
            if attempt < self._max_retries - 1:
                await asyncio.sleep(delay)

        await logger.aerror(
            "startup.failed",
            message="Startup validation failed after all retries",
            max_retries=self._max_retries,
        )
        return False
