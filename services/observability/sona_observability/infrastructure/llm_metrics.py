"""Pre-defined metrics collector for LLM/AI operations.

Provides standardized metrics for monitoring AI model invocations
including request counts, durations, token usage, and errors.
"""

from __future__ import annotations

from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class LLMMetrics:
    """Collects standard LLM operation metrics.

    Metrics:
        - llm_requests_total: Counter with labels provider, model
        - llm_request_duration_ms: Histogram with labels provider, model
        - llm_tokens_input_total: Counter with labels provider, model
        - llm_tokens_output_total: Counter with labels provider, model
        - llm_errors_total: Counter with labels provider, error_type
    """

    REQUESTS_TOTAL = "llm_requests_total"
    REQUEST_DURATION_MS = "llm_request_duration_ms"
    TOKENS_INPUT_TOTAL = "llm_tokens_input_total"
    TOKENS_OUTPUT_TOTAL = "llm_tokens_output_total"
    ERRORS_TOTAL = "llm_errors_total"

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry

    def record_request(
        self, provider: str, model: str, duration_ms: float, input_tokens: int, output_tokens: int
    ) -> None:
        """Record a completed LLM request.

        Args:
            provider: LLM provider (e.g., "openai", "anthropic").
            model: Model name (e.g., "gpt-4", "claude-3").
            duration_ms: Request duration in milliseconds.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
        """
        tags = {"provider": provider, "model": model}
        self._registry.increment(self.REQUESTS_TOTAL, tags=tags)
        self._registry.histogram(self.REQUEST_DURATION_MS, duration_ms, tags=tags)
        self._registry.increment(self.TOKENS_INPUT_TOTAL, value=float(input_tokens), tags=tags)
        self._registry.increment(self.TOKENS_OUTPUT_TOTAL, value=float(output_tokens), tags=tags)

    def record_error(self, provider: str, error_type: str) -> None:
        """Record an LLM error.

        Args:
            provider: LLM provider.
            error_type: Type of error (e.g., "timeout", "rate_limit").
        """
        tags = {"provider": provider, "error_type": error_type}
        self._registry.increment(self.ERRORS_TOTAL, tags=tags)
