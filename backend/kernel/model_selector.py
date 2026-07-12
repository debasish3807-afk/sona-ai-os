"""Model selection interface.

Defines the contract for intelligent model routing and selection
based on task requirements, availability, cost, and performance.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ModelCapability(str, Enum):
    """Capabilities that a model may support."""

    CHAT = "chat"
    COMPLETION = "completion"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    EMBEDDINGS = "embeddings"
    LONG_CONTEXT = "long_context"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"


class SelectionStrategy(str, Enum):
    """Strategy for model selection."""

    BEST_MATCH = "best_match"
    COST_OPTIMIZED = "cost_optimized"
    SPEED_OPTIMIZED = "speed_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    ROUND_ROBIN = "round_robin"
    FALLBACK_CHAIN = "fallback_chain"


@dataclass
class ModelProfile:
    """Profile describing a model's characteristics.

    Attributes:
        model_id: Unique model identifier.
        provider_id: Provider that serves this model.
        name: Human-readable model name.
        capabilities: Set of supported capabilities.
        max_context_tokens: Maximum context window size.
        max_output_tokens: Maximum output token limit.
        cost_per_input_token: Cost per input token in USD.
        cost_per_output_token: Cost per output token in USD.
        avg_latency_ms: Average response latency.
        quality_score: Quality rating (0-1).
        is_available: Whether the model is currently available.
        rate_limit_rpm: Requests per minute limit.
        metadata: Additional model metadata.
    """

    model_id: str
    provider_id: str
    name: str
    capabilities: List[ModelCapability] = field(default_factory=list)
    max_context_tokens: int = 8192
    max_output_tokens: int = 4096
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    avg_latency_ms: float = 0.0
    quality_score: float = 0.5
    is_available: bool = True
    rate_limit_rpm: int = 60
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_capability(self, capability: ModelCapability) -> bool:
        """Check if the model supports a specific capability."""
        return capability in self.capabilities


@dataclass
class SelectionCriteria:
    """Criteria for model selection.

    Attributes:
        required_capabilities: Capabilities the model must support.
        preferred_capabilities: Nice-to-have capabilities.
        min_context_tokens: Minimum required context window.
        max_cost_per_token: Maximum acceptable cost per token.
        max_latency_ms: Maximum acceptable latency.
        min_quality_score: Minimum quality threshold.
        preferred_providers: Preferred provider IDs.
        excluded_models: Models to exclude from selection.
        strategy: Selection strategy to apply.
        metadata: Additional selection context.
    """

    required_capabilities: List[ModelCapability] = field(default_factory=list)
    preferred_capabilities: List[ModelCapability] = field(default_factory=list)
    min_context_tokens: int = 0
    max_cost_per_token: Optional[float] = None
    max_latency_ms: Optional[float] = None
    min_quality_score: float = 0.0
    preferred_providers: List[str] = field(default_factory=list)
    excluded_models: List[str] = field(default_factory=list)
    strategy: SelectionStrategy = SelectionStrategy.BEST_MATCH
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SelectionResult:
    """Result of a model selection decision.

    Attributes:
        selected_model: The chosen model profile.
        fallback_models: Ordered list of fallback options.
        reason: Explanation of the selection decision.
        score: Selection confidence score (0-1).
        metadata: Additional selection metadata.
    """

    selected_model: ModelProfile
    fallback_models: List[ModelProfile] = field(default_factory=list)
    reason: str = ""
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelSelector(ABC):
    """Abstract interface for model selection.

    Implements intelligent routing of tasks to the most appropriate
    model based on requirements, cost, and performance criteria.
    """

    @abstractmethod
    async def select(
        self,
        criteria: SelectionCriteria,
    ) -> Optional[SelectionResult]:
        """Select the best model for the given criteria.

        Evaluates available models against the selection criteria
        and returns the optimal choice with fallback options.

        Args:
            criteria: Selection requirements and preferences.

        Returns:
            SelectionResult with chosen model, or None if no match.
        """
        ...

    @abstractmethod
    async def register_model(self, profile: ModelProfile) -> None:
        """Register a model profile for selection consideration.

        Args:
            profile: The model profile to register.

        Raises:
            ValueError: If a model with the same ID is registered.
        """
        ...

    @abstractmethod
    async def unregister_model(self, model_id: str) -> bool:
        """Remove a model from the selection pool.

        Args:
            model_id: The model to remove.

        Returns:
            True if the model was found and removed.
        """
        ...

    @abstractmethod
    async def update_availability(
        self,
        model_id: str,
        is_available: bool,
    ) -> None:
        """Update a model's availability status.

        Args:
            model_id: The model to update.
            is_available: New availability state.
        """
        ...

    @abstractmethod
    async def update_metrics(
        self,
        model_id: str,
        latency_ms: Optional[float] = None,
        quality_score: Optional[float] = None,
    ) -> None:
        """Update model performance metrics.

        Args:
            model_id: The model to update.
            latency_ms: New average latency measurement.
            quality_score: Updated quality score.
        """
        ...

    @abstractmethod
    async def get_available_models(
        self,
        capability: Optional[ModelCapability] = None,
    ) -> List[ModelProfile]:
        """Get all currently available models.

        Args:
            capability: Optional filter by required capability.

        Returns:
            List of available model profiles.
        """
        ...

    @abstractmethod
    async def get_model(self, model_id: str) -> Optional[ModelProfile]:
        """Get a specific model profile.

        Args:
            model_id: The model identifier.

        Returns:
            ModelProfile or None if not found.
        """
        ...
