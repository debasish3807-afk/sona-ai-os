"""Unit tests for the provider and model registries.

Tests verify provider registration, lookup, health checking,
model resolution, and refresh operations.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest

from sona_ai_kernel.infrastructure.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProviderBase,
    ProviderConfig,
    ProviderHealth,
)
from sona_ai_kernel.infrastructure.registry import ModelRegistry, ProviderRegistry


class FakeProvider(LLMProviderBase):
    """Fake provider for testing registry operations."""

    def __init__(
        self, name: str = "fake", healthy: bool = True, models: list[str] | None = None
    ) -> None:
        config = ProviderConfig(name=name, base_url="http://localhost")
        super().__init__(config)
        self._healthy = healthy
        self._models = models or ["model-1", "model-2"]
        self._health = ProviderHealth(healthy=healthy)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            content="fake response",
            model=request.model,
            tokens_input=10,
            tokens_output=5,
        )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        async def _gen() -> AsyncIterator[str]:
            yield "fake"

        return _gen()

    async def check_health(self) -> ProviderHealth:
        self._health = ProviderHealth(
            healthy=self._healthy,
            last_check=datetime.now(UTC),
            latency_ms=10.0,
        )
        return self._health

    async def list_models(self) -> list[str]:
        return self._models


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def test_empty_registry(self) -> None:
        """Empty registry returns empty lists."""
        registry = ProviderRegistry()
        assert registry.list_providers() == []
        assert registry.list_healthy() == []

    def test_register_provider(self) -> None:
        """Register a provider and retrieve it by name."""
        registry = ProviderRegistry()
        provider = FakeProvider(name="test-provider")
        registry.register(provider)
        assert "test-provider" in registry.list_providers()
        assert registry.get("test-provider") is provider

    def test_get_nonexistent(self) -> None:
        """Getting a non-existent provider returns None."""
        registry = ProviderRegistry()
        assert registry.get("nonexistent") is None

    def test_list_healthy_filters(self) -> None:
        """list_healthy only returns providers with healthy status."""
        registry = ProviderRegistry()
        registry.register(FakeProvider(name="healthy-1", healthy=True))
        registry.register(FakeProvider(name="unhealthy-1", healthy=False))
        registry.register(FakeProvider(name="healthy-2", healthy=True))

        healthy = registry.list_healthy()
        assert "healthy-1" in healthy
        assert "healthy-2" in healthy
        assert "unhealthy-1" not in healthy

    def test_multiple_providers(self) -> None:
        """Multiple providers can be registered."""
        registry = ProviderRegistry()
        registry.register(FakeProvider(name="provider-a"))
        registry.register(FakeProvider(name="provider-b"))
        assert len(registry.list_providers()) == 2

    @pytest.mark.asyncio
    async def test_check_all_health(self) -> None:
        """check_all_health queries all providers."""
        registry = ProviderRegistry()
        registry.register(FakeProvider(name="p1", healthy=True))
        registry.register(FakeProvider(name="p2", healthy=False))

        results = await registry.check_all_health()
        assert results["p1"].healthy is True
        assert results["p2"].healthy is False


class TestModelRegistry:
    """Tests for ModelRegistry."""

    def test_empty_model_registry(self) -> None:
        """Empty model registry returns empty list."""
        provider_registry = ProviderRegistry()
        model_registry = ModelRegistry(provider_registry)
        assert model_registry.list_models() == []

    def test_resolve_unregistered(self) -> None:
        """Resolving an unregistered model returns None."""
        provider_registry = ProviderRegistry()
        model_registry = ModelRegistry(provider_registry)
        assert model_registry.resolve("unknown-model") is None

    def test_manual_register(self) -> None:
        """Manually registered models can be resolved."""
        provider_registry = ProviderRegistry()
        model_registry = ModelRegistry(provider_registry)
        model_registry.register_model("llama3.2", "ollama")
        assert model_registry.resolve("llama3.2") == "ollama"

    def test_list_models(self) -> None:
        """list_models returns all registered model IDs."""
        provider_registry = ProviderRegistry()
        model_registry = ModelRegistry(provider_registry)
        model_registry.register_model("model-a", "provider-a")
        model_registry.register_model("model-b", "provider-b")
        models = model_registry.list_models()
        assert "model-a" in models
        assert "model-b" in models

    @pytest.mark.asyncio
    async def test_refresh_discovers_models(self) -> None:
        """Refresh discovers models from all providers."""
        provider_registry = ProviderRegistry()
        provider_registry.register(FakeProvider(name="p1", models=["model-x", "model-y"]))
        provider_registry.register(FakeProvider(name="p2", models=["model-z"]))

        model_registry = ModelRegistry(provider_registry)
        await model_registry.refresh()

        assert model_registry.resolve("model-x") == "p1"
        assert model_registry.resolve("model-y") == "p1"
        assert model_registry.resolve("model-z") == "p2"
        assert len(model_registry.list_models()) == 3

    @pytest.mark.asyncio
    async def test_refresh_clears_old_mappings(self) -> None:
        """Refresh clears existing mappings before repopulating."""
        provider_registry = ProviderRegistry()
        model_registry = ModelRegistry(provider_registry)
        model_registry.register_model("stale-model", "old-provider")

        provider_registry.register(FakeProvider(name="p1", models=["new-model"]))
        await model_registry.refresh()

        assert model_registry.resolve("stale-model") is None
        assert model_registry.resolve("new-model") == "p1"
