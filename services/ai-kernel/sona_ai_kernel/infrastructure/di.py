"""Factory for assembling the AI Kernel with all dependencies.

Provides a factory function that wires up all infrastructure components
into a ready-to-use AIKernelRuntime instance.
"""

import structlog

from sona_ai_kernel.infrastructure.kernel_runtime import AIKernelRuntime
from sona_ai_kernel.infrastructure.providers.base import ProviderConfig
from sona_ai_kernel.infrastructure.providers.ollama import OllamaProvider
from sona_ai_kernel.infrastructure.providers.openai_compat import OpenAICompatProvider
from sona_ai_kernel.infrastructure.registry import ModelRegistry, ProviderRegistry
from sona_ai_kernel.infrastructure.retry import RetryConfig
from sona_ai_kernel.infrastructure.token_usage import TokenUsageManager

logger = structlog.get_logger()


def create_kernel(
    providers: list[ProviderConfig],
    default_model: str = "llama3.2",
    default_provider: str = "ollama",
    retry_config: RetryConfig | None = None,
) -> AIKernelRuntime:
    """Factory function to create a fully-wired AI Kernel.

    Creates and registers all configured providers, sets up the model
    registry, token manager, and assembles the complete runtime.

    Args:
        providers: List of provider configurations to register.
        default_model: Default model ID to use when none specified.
        default_provider: Default provider to use when model can't be resolved.
        retry_config: Optional retry configuration override.

    Returns:
        A fully configured AIKernelRuntime ready for use.
    """
    provider_registry = ProviderRegistry()
    token_manager = TokenUsageManager()

    for config in providers:
        provider = _create_provider(config)
        if provider is not None:
            provider_registry.register(provider)

    model_registry = ModelRegistry(provider_registry)

    # Pre-register configured models
    for config in providers:
        for model_id in config.models:
            model_registry.register_model(model_id, config.name)

    kernel = AIKernelRuntime(
        provider_registry=provider_registry,
        model_registry=model_registry,
        token_manager=token_manager,
        default_model=default_model,
        default_provider=default_provider,
        retry_config=retry_config,
    )

    logger.info(
        "kernel_created",
        providers=provider_registry.list_providers(),
        default_model=default_model,
        default_provider=default_provider,
    )

    return kernel


def _create_provider(config: ProviderConfig) -> OllamaProvider | OpenAICompatProvider | None:
    """Create a provider instance based on configuration.

    Determines the provider type from the name and creates the
    appropriate adapter instance.

    Args:
        config: Provider configuration.

    Returns:
        A provider instance, or None if the type is unknown.
    """
    name = config.name.lower()

    if name == "ollama":
        return OllamaProvider(config)
    if name in ("openai", "openai_compat", "openai-compat", "vllm", "litellm"):
        return OpenAICompatProvider(config)
    # Default to OpenAI-compatible for unknown providers
    logger.info(
        "unknown_provider_type_using_openai_compat",
        provider=config.name,
    )
    return OpenAICompatProvider(config)
