"""Model selection logic for THALAMUS routing.

Selects the optimal model for a request based on task classification,
required capabilities, latency requirements, and cost constraints.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.task_classifier import TaskClassification, TaskType

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for a selected model.

    Attributes:
        model_id: The model identifier.
        provider: The provider hosting the model.
        capabilities: List of capability tags.
        max_tokens: Maximum token limit for the model.
        latency_class: Expected latency class (fast, medium, slow).
        cost_per_token: Cost per token in arbitrary units.
    """

    model_id: str
    provider: str
    capabilities: list[str] = field(default_factory=list)
    max_tokens: int = 4096
    latency_class: str = "medium"
    cost_per_token: float = 0.0


# Default model catalog
_DEFAULT_MODELS: dict[str, ModelConfig] = {
    "llama3.2": ModelConfig(
        model_id="llama3.2",
        provider="ollama",
        capabilities=["chat", "general"],
        max_tokens=4096,
        latency_class="fast",
        cost_per_token=0.0,
    ),
    "codellama": ModelConfig(
        model_id="codellama",
        provider="ollama",
        capabilities=["code", "technical"],
        max_tokens=8192,
        latency_class="medium",
        cost_per_token=0.0,
    ),
    "mixtral": ModelConfig(
        model_id="mixtral",
        provider="ollama",
        capabilities=["reasoning", "analytical", "research"],
        max_tokens=32768,
        latency_class="slow",
        cost_per_token=0.0,
    ),
    "gpt-4": ModelConfig(
        model_id="gpt-4",
        provider="openai",
        capabilities=["code", "reasoning", "creative", "research"],
        max_tokens=8192,
        latency_class="medium",
        cost_per_token=0.00003,
    ),
    "gpt-3.5-turbo": ModelConfig(
        model_id="gpt-3.5-turbo",
        provider="openai",
        capabilities=["chat", "general", "fast"],
        max_tokens=4096,
        latency_class="fast",
        cost_per_token=0.000002,
    ),
    "claude-3-sonnet": ModelConfig(
        model_id="claude-3-sonnet",
        provider="anthropic",
        capabilities=["reasoning", "code", "creative", "analytical"],
        max_tokens=200000,
        latency_class="medium",
        cost_per_token=0.000015,
    ),
}

# Task type to required capabilities mapping
_TASK_CAPABILITIES: dict[TaskType, list[str]] = {
    TaskType.SIMPLE: ["chat", "general"],
    TaskType.COMPOSITE: ["reasoning"],
    TaskType.RESEARCH: ["research", "reasoning"],
    TaskType.CREATIVE: ["creative"],
    TaskType.TECHNICAL: ["code", "technical"],
    TaskType.ANALYTICAL: ["analytical", "reasoning"],
}


class ModelSelector:
    """Selects the optimal model based on task requirements.

    Considers task type, required capabilities, latency constraints,
    and cost limits to find the best available model.
    """

    def __init__(
        self,
        models: dict[str, ModelConfig] | None = None,
        default_model: str = "llama3.2",
        default_provider: str = "ollama",
        cost_limit: float | None = None,
    ) -> None:
        """Initialize the model selector.

        Args:
            models: Available model catalog (uses defaults if None).
            default_model: Fallback model ID.
            default_provider: Fallback provider name.
            cost_limit: Optional maximum cost per token limit.
        """
        self._models = _DEFAULT_MODELS if models is None else models
        self._default_model = default_model
        self._default_provider = default_provider
        self._cost_limit = cost_limit

    def select(
        self,
        task: TaskClassification,
        intent: IntentCategory,
        context: dict[str, Any] | None = None,
    ) -> ModelConfig:
        """Select the optimal model for the given task.

        Args:
            task: The classified task information.
            intent: The classified intent category.
            context: Optional context with user preferences.

        Returns:
            ModelConfig for the selected model.
        """
        required_caps = _TASK_CAPABILITIES.get(task.task_type, ["general"])

        # Filter models by capability match
        candidates: list[tuple[str, ModelConfig, int]] = []
        for model_id, config in self._models.items():
            # Apply cost filter
            if self._cost_limit is not None and config.cost_per_token > self._cost_limit:
                continue

            # Count matching capabilities
            match_count = sum(1 for cap in required_caps if cap in config.capabilities)
            if match_count > 0:
                candidates.append((model_id, config, match_count))

        if not candidates:
            # Return default model
            logger.debug(
                "model_selected",
                model=self._default_model,
                reason="no_matching_candidates",
            )
            if self._default_model in self._models:
                return self._models[self._default_model]
            return ModelConfig(
                model_id=self._default_model,
                provider=self._default_provider,
            )

        # Score candidates: capability match + latency preference
        latency_preference = self._get_latency_preference(intent, task)

        def score_model(item: tuple[str, ModelConfig, int]) -> float:
            _, config, match_count = item
            score = float(match_count) * 2.0

            # Latency bonus
            if config.latency_class == latency_preference:
                score += 1.5
            elif config.latency_class == "fast":
                score += 0.5

            # Cost penalty for expensive models on simple tasks
            if task.task_type == TaskType.SIMPLE and config.cost_per_token > 0:
                score -= 1.0

            return score

        # Select best scored candidate
        candidates.sort(key=score_model, reverse=True)
        _, selected_config, _ = candidates[0]

        logger.debug(
            "model_selected",
            model=selected_config.model_id,
            provider=selected_config.provider,
            task_type=str(task.task_type),
            latency_class=selected_config.latency_class,
        )

        return selected_config

    def _get_latency_preference(self, intent: IntentCategory, task: TaskClassification) -> str:
        """Determine preferred latency class."""
        # Chat needs fast response
        if intent == IntentCategory.CHAT and task.task_type == TaskType.SIMPLE:
            return "fast"

        # Code and research can tolerate slower models
        if intent in (IntentCategory.CODE, IntentCategory.RESEARCH):
            return "medium"

        # Complex tasks can use slow but powerful models
        if task.complexity_score > 0.6:
            return "slow"

        return "medium"
