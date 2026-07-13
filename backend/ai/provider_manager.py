"""Provider manager for registering and accessing AI providers."""

from __future__ import annotations

from ai.base_provider import BaseAIProvider
from ai.schemas import ProviderStatus
from config.logging import get_logger

logger = get_logger(__name__)


class ProviderManager:
    """Manages registration and access to AI providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseAIProvider] = {}
        self._default: str | None = None

    def register(self, provider: BaseAIProvider) -> None:
        """Register a provider instance."""
        self._providers[provider.name] = provider
        if self._default is None:
            self._default = provider.name
        logger.info("provider_registered", name=provider.name)

    def get(self, name: str) -> BaseAIProvider | None:
        """Get a provider by name."""
        return self._providers.get(name)

    def get_default(self) -> BaseAIProvider | None:
        """Get the default provider."""
        if self._default is None:
            return None
        return self._providers.get(self._default)

    def set_default(self, name: str) -> bool:
        """Set the default provider by name."""
        if name not in self._providers:
            return False
        self._default = name
        return True

    def list_all(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    def list_healthy(self) -> list[str]:
        """List providers with healthy status."""
        return [
            name
            for name, provider in self._providers.items()
            if provider.get_status() == ProviderStatus.HEALTHY
        ]

    async def health_check_all(self) -> dict[str, ProviderStatus]:
        """Run health checks on all providers."""
        results: dict[str, ProviderStatus] = {}
        for name, provider in self._providers.items():
            try:
                healthy = await provider.health_check()
                results[name] = ProviderStatus.HEALTHY if healthy else ProviderStatus.UNAVAILABLE
            except Exception:
                results[name] = ProviderStatus.UNAVAILABLE
        return results

    def get_stats(self) -> dict:
        """Get statistics about registered providers."""
        return {
            "total_providers": len(self._providers),
            "default_provider": self._default,
            "providers": {
                name: {
                    "status": provider.get_status().value,
                    "models": provider.available_models,
                    "requests": provider._request_count,
                    "errors": provider._error_count,
                }
                for name, provider in self._providers.items()
            },
        }
