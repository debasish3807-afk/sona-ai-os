"""Token usage tracking across providers and models."""

from __future__ import annotations

from dataclasses import dataclass

from ai.schemas import TokenUsage
from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class _UsageEntry:
    """Internal tracking entry."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    request_count: int = 0


class TokenTracker:
    """Tracks token usage across providers and models."""

    def __init__(self) -> None:
        self._by_provider: dict[str, _UsageEntry] = {}
        self._by_model: dict[str, _UsageEntry] = {}
        self._total = _UsageEntry()

    def record(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float = 0.0,
    ) -> None:
        """Record token usage for a request."""
        total = prompt_tokens + completion_tokens

        self._total.prompt_tokens += prompt_tokens
        self._total.completion_tokens += completion_tokens
        self._total.total_tokens += total
        self._total.cost_usd += cost
        self._total.request_count += 1

        if provider not in self._by_provider:
            self._by_provider[provider] = _UsageEntry()
        entry = self._by_provider[provider]
        entry.prompt_tokens += prompt_tokens
        entry.completion_tokens += completion_tokens
        entry.total_tokens += total
        entry.cost_usd += cost
        entry.request_count += 1

        if model not in self._by_model:
            self._by_model[model] = _UsageEntry()
        entry = self._by_model[model]
        entry.prompt_tokens += prompt_tokens
        entry.completion_tokens += completion_tokens
        entry.total_tokens += total
        entry.cost_usd += cost
        entry.request_count += 1

    def get_total(self) -> TokenUsage:
        """Get total token usage across all providers."""
        return TokenUsage(
            prompt_tokens=self._total.prompt_tokens,
            completion_tokens=self._total.completion_tokens,
            total_tokens=self._total.total_tokens,
            cost_usd=self._total.cost_usd,
        )

    def get_by_provider(self, provider: str) -> TokenUsage:
        """Get token usage for a specific provider."""
        entry = self._by_provider.get(provider, _UsageEntry())
        return TokenUsage(
            prompt_tokens=entry.prompt_tokens,
            completion_tokens=entry.completion_tokens,
            total_tokens=entry.total_tokens,
            cost_usd=entry.cost_usd,
        )

    def get_by_model(self, model: str) -> TokenUsage:
        """Get token usage for a specific model."""
        entry = self._by_model.get(model, _UsageEntry())
        return TokenUsage(
            prompt_tokens=entry.prompt_tokens,
            completion_tokens=entry.completion_tokens,
            total_tokens=entry.total_tokens,
            cost_usd=entry.cost_usd,
        )

    def reset(self) -> None:
        """Reset all tracked usage."""
        self._by_provider.clear()
        self._by_model.clear()
        self._total = _UsageEntry()
