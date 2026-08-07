"""Provider and model registry for managing available LLM backends.

Provides a centralized registry for LLM providers and a model-to-provider
mapping that enables model routing and discovery.
"""

import structlog

from sona_ai_kernel.infrastructure.providers.base import LLMProviderBase, ProviderHealth

logger = structlog.get_logger()


class ProviderRegistry:
    """Registry managing all configured LLM providers.

    Maintains a dictionary of registered providers and provides
    operations for querying health, listing, and retrieval.
    """

    def __init__(self) -> None:
        """Initialize an empty provider registry."""
        self._providers: dict[str, LLMProviderBase] = {}

    def register(self, provider: LLMProviderBase) -> None:
        """Register a provider in the registry.

        Args:
            provider: The LLM provider instance to register.
        """
        self._providers[provider.name] = provider
        logger.info("provider_registered", provider=provider.name)

    def get(self, name: str) -> LLMProviderBase | None:
        """Get a provider by name.

        Args:
            name: The provider's unique name.

        Returns:
            The provider instance, or None if not found.
        """
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """List all registered provider names.

        Returns:
            A list of provider name strings.
        """
        return list(self._providers.keys())

    def list_healthy(self) -> list[str]:
        """List names of all providers currently reporting healthy.

        Returns:
            A list of healthy provider name strings.
        """
        return [name for name, provider in self._providers.items() if provider.health.healthy]

    async def check_all_health(self) -> dict[str, ProviderHealth]:
        """Check health of all registered providers.

        Returns:
            A dictionary mapping provider names to their health status.
        """
        results: dict[str, ProviderHealth] = {}
        for name, provider in self._providers.items():
            health = await provider.check_health()
            results[name] = health
            logger.info(
                "provider_health_checked",
                provider=name,
                healthy=health.healthy,
                latency_ms=health.latency_ms,
            )
        return results


class ModelRegistry:
    """Registry mapping model IDs to their hosting providers.

    Maintains a model-to-provider lookup table that is refreshed
    by querying all registered providers for their available models.
    """

    def __init__(self, provider_registry: ProviderRegistry) -> None:
        """Initialize the model registry.

        Args:
            provider_registry: The provider registry to query for models.
        """
        self._provider_registry = provider_registry
        self._model_map: dict[str, str] = {}  # model_id -> provider_name

    async def refresh(self) -> None:
        """Refresh the model map by querying all providers.

        Iterates through all registered providers, queries their
        available models, and updates the internal mapping.
        """
        self._model_map.clear()
        for provider_name in self._provider_registry.list_providers():
            provider = self._provider_registry.get(provider_name)
            if provider is None:
                continue
            try:
                models = await provider.list_models()
                for model_id in models:
                    self._model_map[model_id] = provider_name
                logger.info(
                    "models_discovered",
                    provider=provider_name,
                    count=len(models),
                )
            except Exception as exc:
                logger.warning(
                    "model_discovery_failed",
                    provider=provider_name,
                    error=str(exc),
                )

    def resolve(self, model_id: str) -> str | None:
        """Resolve a model ID to its provider name.

        Args:
            model_id: The model identifier to look up.

        Returns:
            The provider name hosting the model, or None if not found.
        """
        return self._model_map.get(model_id)

    def list_models(self) -> list[str]:
        """List all known model IDs across all providers.

        Returns:
            A list of model identifier strings.
        """
        return list(self._model_map.keys())

    def register_model(self, model_id: str, provider_name: str) -> None:
        """Manually register a model-to-provider mapping.

        Args:
            model_id: The model identifier.
            provider_name: The provider that hosts this model.
        """
        self._model_map[model_id] = provider_name
