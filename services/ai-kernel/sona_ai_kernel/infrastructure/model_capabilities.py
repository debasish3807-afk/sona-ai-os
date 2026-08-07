"""Model capability registry for intelligent model selection."""

from dataclasses import dataclass
from enum import StrEnum

import structlog

logger = structlog.get_logger()


class ModelCapability(StrEnum):
    """Supported model capabilities for capability-based routing."""

    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    LONG_CONTEXT = "long_context"
    EMBEDDING = "embedding"
    FAST = "fast"
    MULTILINGUAL = "multilingual"


@dataclass(frozen=True)
class ModelProfile:
    """Profile describing a model's capabilities and characteristics.

    Attributes:
        model_id: Unique model identifier (e.g. "gpt-4o").
        provider: The provider hosting this model.
        capabilities: Set of capabilities this model supports.
        context_window: Maximum input context window in tokens.
        max_output_tokens: Maximum output tokens the model can generate.
        cost_per_input_token: Cost per input token in USD.
        cost_per_output_token: Cost per output token in USD.
        avg_latency_ms: Average observed latency in milliseconds.
    """

    model_id: str
    provider: str
    capabilities: frozenset[ModelCapability]
    context_window: int = 4096
    max_output_tokens: int = 4096
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    avg_latency_ms: float = 0.0


class ModelCapabilityRegistry:
    """Registry for model capabilities and intelligent selection.

    Allows registering models with their capability profiles and provides
    methods for finding models by capability, cost, or latency.
    """

    def __init__(self) -> None:
        """Initialize an empty capability registry."""
        self._models: dict[str, ModelProfile] = {}

    def register(self, profile: ModelProfile) -> None:
        """Register a model profile.

        Args:
            profile: The model profile to register.
        """
        self._models[profile.model_id] = profile
        logger.info(
            "model_registered",
            model_id=profile.model_id,
            provider=profile.provider,
            capabilities=list(profile.capabilities),
        )

    def get(self, model_id: str) -> ModelProfile | None:
        """Get a model profile by ID.

        Args:
            model_id: The model identifier to look up.

        Returns:
            The model profile, or None if not found.
        """
        return self._models.get(model_id)

    def find_by_capability(self, *capabilities: ModelCapability) -> list[ModelProfile]:
        """Find all models with the specified capabilities.

        Args:
            capabilities: One or more capabilities to require.

        Returns:
            List of model profiles that have ALL specified capabilities.
        """
        required = frozenset(capabilities)
        return [
            profile for profile in self._models.values() if required.issubset(profile.capabilities)
        ]

    def find_cheapest(self, *capabilities: ModelCapability) -> ModelProfile | None:
        """Find the cheapest model with the specified capabilities.

        Uses the sum of input and output cost per token for comparison.

        Args:
            capabilities: Capabilities to require.

        Returns:
            The cheapest matching model, or None if no match.
        """
        matches = self.find_by_capability(*capabilities)
        if not matches:
            return None
        return min(
            matches,
            key=lambda p: p.cost_per_input_token + p.cost_per_output_token,
        )

    def find_fastest(self, *capabilities: ModelCapability) -> ModelProfile | None:
        """Find the fastest model with the specified capabilities.

        Uses average latency for comparison.

        Args:
            capabilities: Capabilities to require.

        Returns:
            The fastest matching model, or None if no match.
        """
        matches = self.find_by_capability(*capabilities)
        if not matches:
            return None
        return min(matches, key=lambda p: p.avg_latency_ms)

    def list_all(self) -> list[ModelProfile]:
        """List all registered model profiles.

        Returns:
            List of all model profiles in the registry.
        """
        return list(self._models.values())
