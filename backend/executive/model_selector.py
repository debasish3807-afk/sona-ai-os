"""Executive Intelligence layer — model selection and ranking."""

from __future__ import annotations

from config.logging import get_logger

logger = get_logger(__name__)


class ModelSelector:
    """Selects and ranks AI models based on task requirements."""

    def __init__(self) -> None:
        self._models: dict[str, dict] = {
            "gpt-4o": {
                "reasoning_complexity": 0.95,
                "latency_ms": 300,
                "token_budget": 128000,
                "cost_per_token": 0.00005,
                "context_window": 128000,
                "capability_support": ["code", "reasoning", "analysis", "creative"],
                "health": 1.0,
            },
            "claude-sonnet": {
                "reasoning_complexity": 0.92,
                "latency_ms": 350,
                "token_budget": 200000,
                "cost_per_token": 0.000015,
                "context_window": 200000,
                "capability_support": ["code", "reasoning", "analysis", "creative"],
                "health": 1.0,
            },
            "gemini-pro": {
                "reasoning_complexity": 0.88,
                "latency_ms": 400,
                "token_budget": 1000000,
                "cost_per_token": 0.00001,
                "context_window": 1000000,
                "capability_support": ["code", "reasoning", "multimodal"],
                "health": 0.9,
            },
            "local-llama": {
                "reasoning_complexity": 0.70,
                "latency_ms": 100,
                "token_budget": 32000,
                "cost_per_token": 0.0,
                "context_window": 32000,
                "capability_support": ["code", "reasoning"],
                "health": 1.0,
            },
        }

    def select_model(self, requirements: dict) -> str | None:
        """Select the best model for given requirements."""
        ranked = self.rank_models(requirements)
        if not ranked:
            return None
        return ranked[0][0]

    def rank_models(self, requirements: dict) -> list[tuple[str, float]]:
        """Rank all models by suitability score."""
        results: list[tuple[str, float]] = []
        for model_id in self._models:
            score = self._score_model(model_id, requirements)
            results.append((model_id, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _score_model(self, model_id: str, requirements: dict) -> float:
        """Score a model against task requirements."""
        info = self._models.get(model_id)
        if info is None:
            return 0.0

        reasoning_score = info["reasoning_complexity"]
        latency_score = 1.0 - min(info["latency_ms"] / 1000.0, 1.0)
        token_score = min(info["token_budget"] / 200000.0, 1.0)
        cost_score = 1.0 - min(info["cost_per_token"] * 20000, 1.0)
        context_score = min(info["context_window"] / 200000.0, 1.0)
        health_score = info["health"]

        # Capability match
        required_caps = requirements.get("capabilities", [])
        if required_caps:
            matched = sum(1 for c in required_caps if c in info["capability_support"])
            capability_score = matched / len(required_caps) if required_caps else 1.0
        else:
            capability_score = 1.0

        # Requirement constraints
        min_reasoning = requirements.get("min_reasoning", 0.0)
        if info["reasoning_complexity"] < min_reasoning:
            reasoning_score *= 0.5

        max_latency = requirements.get("max_latency_ms", 1000)
        if info["latency_ms"] > max_latency:
            latency_score *= 0.5

        score = (
            reasoning_score * 0.25
            + latency_score * 0.15
            + token_score * 0.10
            + cost_score * 0.15
            + context_score * 0.10
            + capability_score * 0.15
            + health_score * 0.10
        )
        return float(score)

    def get_available_models(self) -> list[str]:
        """Return list of available model IDs."""
        return [mid for mid, info in self._models.items() if info["health"] > 0.0]
