"""Executive Intelligence layer — provider selection and ranking."""

from __future__ import annotations

from config.logging import get_logger

logger = get_logger(__name__)


class ProviderSelector:
    """Selects and ranks AI providers based on requirements."""

    def __init__(self) -> None:
        self._providers: dict[str, dict] = {
            "openai": {
                "availability": 0.99,
                "latency_ms": 200,
                "success_rate": 0.97,
                "health": 1.0,
                "cost_per_token": 0.00003,
                "rate_limit": 10000,
            },
            "anthropic": {
                "availability": 0.98,
                "latency_ms": 250,
                "success_rate": 0.98,
                "health": 1.0,
                "cost_per_token": 0.000025,
                "rate_limit": 8000,
            },
            "google": {
                "availability": 0.97,
                "latency_ms": 300,
                "success_rate": 0.95,
                "health": 0.9,
                "cost_per_token": 0.00002,
                "rate_limit": 12000,
            },
            "local": {
                "availability": 1.0,
                "latency_ms": 50,
                "success_rate": 0.90,
                "health": 1.0,
                "cost_per_token": 0.0,
                "rate_limit": 100000,
            },
        }

    def select_provider(self, requirements: dict) -> str | None:
        """Select the best provider for given requirements."""
        ranked = self.rank_providers(requirements)
        if not ranked:
            return None
        return ranked[0][0]

    def rank_providers(self, requirements: dict) -> list[tuple[str, float]]:
        """Rank all providers by suitability score."""
        results: list[tuple[str, float]] = []
        for provider_id in self._providers:
            score = self._score_provider(provider_id, requirements)
            results.append((provider_id, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _score_provider(self, provider_id: str, requirements: dict) -> float:
        """Score a provider against requirements."""
        info = self._providers.get(provider_id)
        if info is None:
            return 0.0

        availability_score = info["availability"]
        latency_score = 1.0 - min(info["latency_ms"] / 1000.0, 1.0)
        success_score = info["success_rate"]
        health_score = info["health"]
        cost_score = 1.0 - min(info["cost_per_token"] * 10000, 1.0)
        rate_score = min(info["rate_limit"] / 10000.0, 1.0)

        # Apply requirement weights
        max_latency = requirements.get("max_latency_ms", 1000)
        if info["latency_ms"] > max_latency:
            latency_score *= 0.5

        min_availability = requirements.get("min_availability", 0.9)
        if info["availability"] < min_availability:
            availability_score *= 0.5

        score = (
            availability_score * 0.20
            + latency_score * 0.20
            + success_score * 0.25
            + health_score * 0.15
            + cost_score * 0.10
            + rate_score * 0.10
        )
        return float(score)

    def get_available_providers(self) -> list[str]:
        """Return list of available provider IDs."""
        return [pid for pid, info in self._providers.items() if info["health"] > 0.0]
