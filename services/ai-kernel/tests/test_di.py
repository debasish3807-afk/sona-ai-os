"""Unit tests for the dependency injection factory.

Tests verify the create_kernel factory produces properly
configured runtime instances with correct provider wiring.
"""

from sona_ai_kernel.infrastructure.di import create_kernel
from sona_ai_kernel.infrastructure.kernel_runtime import AIKernelRuntime
from sona_ai_kernel.infrastructure.providers.base import ProviderConfig
from sona_ai_kernel.infrastructure.retry import RetryConfig


class TestCreateKernel:
    """Tests for the create_kernel factory function."""

    def test_creates_runtime(self) -> None:
        """Factory produces an AIKernelRuntime instance."""
        providers = [
            ProviderConfig(
                name="ollama",
                base_url="http://localhost:11434",
                models=["llama3.2"],
            )
        ]
        kernel = create_kernel(providers)
        assert isinstance(kernel, AIKernelRuntime)

    def test_registers_ollama_provider(self) -> None:
        """Ollama config creates an Ollama provider."""
        providers = [
            ProviderConfig(
                name="ollama",
                base_url="http://localhost:11434",
                models=["llama3.2"],
            )
        ]
        kernel = create_kernel(providers)
        assert kernel._provider_registry.get("ollama") is not None

    def test_registers_openai_provider(self) -> None:
        """OpenAI config creates an OpenAI-compat provider."""
        providers = [
            ProviderConfig(
                name="openai",
                base_url="https://api.openai.com",
                api_key="test-key",
                models=["gpt-4o"],
            )
        ]
        kernel = create_kernel(providers, default_model="gpt-4o", default_provider="openai")
        assert kernel._provider_registry.get("openai") is not None

    def test_registers_multiple_providers(self) -> None:
        """Multiple providers are all registered."""
        providers = [
            ProviderConfig(name="ollama", base_url="http://localhost:11434", models=["llama3.2"]),
            ProviderConfig(name="openai", base_url="https://api.openai.com", models=["gpt-4o"]),
        ]
        kernel = create_kernel(providers)
        assert len(kernel._provider_registry.list_providers()) == 2

    def test_pre_registers_models(self) -> None:
        """Configured models are pre-registered in model registry."""
        providers = [
            ProviderConfig(
                name="ollama",
                base_url="http://localhost:11434",
                models=["llama3.2", "codellama"],
            )
        ]
        kernel = create_kernel(providers)
        assert kernel._model_registry.resolve("llama3.2") == "ollama"
        assert kernel._model_registry.resolve("codellama") == "ollama"

    def test_custom_default_model(self) -> None:
        """Custom default model is used."""
        providers = [
            ProviderConfig(
                name="ollama", base_url="http://localhost:11434", models=["custom-model"]
            )
        ]
        kernel = create_kernel(providers, default_model="custom-model")
        assert kernel._default_model == "custom-model"

    def test_custom_retry_config(self) -> None:
        """Custom retry config is passed through."""
        providers = [ProviderConfig(name="ollama", base_url="http://localhost:11434")]
        retry = RetryConfig(max_retries=5, base_delay=2.0)
        kernel = create_kernel(providers, retry_config=retry)
        assert kernel._retry_config.max_retries == 5
        assert kernel._retry_config.base_delay == 2.0

    def test_unknown_provider_defaults_to_openai_compat(self) -> None:
        """Unknown provider type defaults to OpenAI-compatible."""
        providers = [
            ProviderConfig(name="custom-llm", base_url="http://custom:8080", models=["m1"])
        ]
        kernel = create_kernel(providers)
        assert kernel._provider_registry.get("custom-llm") is not None

    def test_empty_providers_list(self) -> None:
        """Factory works with empty providers list."""
        kernel = create_kernel([])
        assert isinstance(kernel, AIKernelRuntime)
        assert kernel._provider_registry.list_providers() == []
