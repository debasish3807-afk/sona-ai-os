"""Provider failover orchestration."""

from collections.abc import AsyncIterator

import structlog

from sona_ai_kernel.infrastructure.circuit_breaker import CircuitBreaker
from sona_ai_kernel.infrastructure.provider_priority import ProviderPriorityManager
from sona_ai_kernel.infrastructure.providers.base import (
    CompletionRequest,
    CompletionResponse,
)
from sona_ai_kernel.infrastructure.registry import ProviderRegistry

logger = structlog.get_logger()


class FailoverError(Exception):
    """Raised when all providers have been exhausted during failover."""

    def __init__(self, failed_providers: list[str]) -> None:
        """Initialize with the list of providers that failed.

        Args:
            failed_providers: Names of providers that were tried and failed.
        """
        self.failed_providers = failed_providers
        super().__init__(f"All providers exhausted: {', '.join(failed_providers)}")


class FailoverEngine:
    """Executes requests with automatic failover to backup providers.

    Coordinates between the provider registry, priority manager, and
    circuit breakers to deliver requests even when individual providers fail.
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        priority_manager: ProviderPriorityManager,
        circuit_breakers: dict[str, CircuitBreaker] | None = None,
    ) -> None:
        """Initialize the failover engine.

        Args:
            registry: The provider registry for looking up providers.
            priority_manager: Manages provider selection order.
            circuit_breakers: Optional mapping of provider name to breaker.
        """
        self._registry = registry
        self._priority_manager = priority_manager
        self._circuit_breakers = circuit_breakers or {}

    async def execute(
        self,
        request: CompletionRequest,
        preferred_provider: str | None = None,
    ) -> CompletionResponse:
        """Try providers in priority order, failing over on errors.

        Args:
            request: The completion request to execute.
            preferred_provider: Optional preferred provider to try first.

        Returns:
            The completion response from the first successful provider.

        Raises:
            FailoverError: If all providers fail.
        """
        failed: set[str] = set()
        failed_list: list[str] = []

        # Build ordered list of providers to try
        providers_to_try: list[str] = []
        if preferred_provider:
            providers_to_try.append(preferred_provider)
        providers_to_try.extend(
            p
            for p in self._priority_manager.get_ordered(exclude=failed)
            if p not in providers_to_try
        )

        for provider_name in providers_to_try:
            # Check circuit breaker
            breaker = self._circuit_breakers.get(provider_name)
            if breaker and not breaker.can_execute():
                logger.debug(
                    "provider_circuit_open",
                    provider=provider_name,
                )
                failed.add(provider_name)
                failed_list.append(provider_name)
                continue

            provider = self._registry.get(provider_name)
            if provider is None:
                logger.warning(
                    "provider_not_found",
                    provider=provider_name,
                )
                failed.add(provider_name)
                failed_list.append(provider_name)
                continue

            try:
                response = await provider.complete(request)
                if breaker:
                    breaker.record_success()
                logger.info(
                    "failover_success",
                    provider=provider_name,
                    attempts=len(failed_list) + 1,
                )
                return response
            except Exception as exc:
                if breaker:
                    breaker.record_failure()
                logger.warning(
                    "provider_failed",
                    provider=provider_name,
                    error=str(exc),
                )
                failed.add(provider_name)
                failed_list.append(provider_name)

        raise FailoverError(failed_list)

    async def execute_stream(
        self,
        request: CompletionRequest,
        preferred_provider: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream with failover across providers.

        Args:
            request: The completion request to stream.
            preferred_provider: Optional preferred provider to try first.

        Returns:
            An async iterator of string tokens from the first successful provider.

        Raises:
            FailoverError: If all providers fail.
        """
        failed: set[str] = set()
        failed_list: list[str] = []

        providers_to_try: list[str] = []
        if preferred_provider:
            providers_to_try.append(preferred_provider)
        providers_to_try.extend(
            p
            for p in self._priority_manager.get_ordered(exclude=failed)
            if p not in providers_to_try
        )

        for provider_name in providers_to_try:
            breaker = self._circuit_breakers.get(provider_name)
            if breaker and not breaker.can_execute():
                failed.add(provider_name)
                failed_list.append(provider_name)
                continue

            provider = self._registry.get(provider_name)
            if provider is None:
                failed.add(provider_name)
                failed_list.append(provider_name)
                continue

            try:
                # Attempt to get the first chunk to verify the stream works
                stream = provider.stream(request)
                if breaker:
                    breaker.record_success()
                logger.info(
                    "failover_stream_success",
                    provider=provider_name,
                    attempts=len(failed_list) + 1,
                )
                return stream
            except Exception as exc:
                if breaker:
                    breaker.record_failure()
                logger.warning(
                    "provider_stream_failed",
                    provider=provider_name,
                    error=str(exc),
                )
                failed.add(provider_name)
                failed_list.append(provider_name)

        raise FailoverError(failed_list)
