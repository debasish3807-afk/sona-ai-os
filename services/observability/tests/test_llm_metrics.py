"""Unit tests for the LLMMetrics infrastructure module.

Tests cover LLM request recording, token counting, duration tracking,
and error recording with provider/model labels.
"""

from sona_observability.infrastructure.llm_metrics import LLMMetrics
from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class TestLLMRequestRecording:
    """Tests for recording LLM requests."""

    def test_record_request_increments_total(self) -> None:
        """Recording an LLM request increments total counter."""
        registry = MetricsRegistry()
        llm = LLMMetrics(registry)
        llm.record_request("openai", "gpt-4", 500.0, 100, 50)
        assert (
            registry.get_counter(
                "llm_requests_total",
                tags={"provider": "openai", "model": "gpt-4"},
            )
            == 1.0
        )

    def test_record_request_tracks_duration(self) -> None:
        """Recording an LLM request records duration."""
        registry = MetricsRegistry()
        llm = LLMMetrics(registry)
        llm.record_request("anthropic", "claude-3", 750.0, 200, 100)
        values = registry.get_histogram_values(
            "llm_request_duration_ms",
            tags={"provider": "anthropic", "model": "claude-3"},
        )
        assert values == [750.0]

    def test_record_request_tracks_input_tokens(self) -> None:
        """Recording an LLM request tracks input tokens."""
        registry = MetricsRegistry()
        llm = LLMMetrics(registry)
        llm.record_request("openai", "gpt-4", 500.0, 150, 50)
        assert (
            registry.get_counter(
                "llm_tokens_input_total",
                tags={"provider": "openai", "model": "gpt-4"},
            )
            == 150.0
        )

    def test_record_request_tracks_output_tokens(self) -> None:
        """Recording an LLM request tracks output tokens."""
        registry = MetricsRegistry()
        llm = LLMMetrics(registry)
        llm.record_request("openai", "gpt-4", 500.0, 100, 75)
        assert (
            registry.get_counter(
                "llm_tokens_output_total",
                tags={"provider": "openai", "model": "gpt-4"},
            )
            == 75.0
        )

    def test_multiple_requests_accumulate_tokens(self) -> None:
        """Multiple requests accumulate token counts."""
        registry = MetricsRegistry()
        llm = LLMMetrics(registry)
        llm.record_request("openai", "gpt-4", 500.0, 100, 50)
        llm.record_request("openai", "gpt-4", 600.0, 200, 100)
        assert (
            registry.get_counter(
                "llm_tokens_input_total",
                tags={"provider": "openai", "model": "gpt-4"},
            )
            == 300.0
        )
        assert (
            registry.get_counter(
                "llm_tokens_output_total",
                tags={"provider": "openai", "model": "gpt-4"},
            )
            == 150.0
        )

    def test_different_providers_tracked_separately(self) -> None:
        """Different providers are tracked as separate series."""
        registry = MetricsRegistry()
        llm = LLMMetrics(registry)
        llm.record_request("openai", "gpt-4", 500.0, 100, 50)
        llm.record_request("anthropic", "claude-3", 600.0, 200, 100)
        assert (
            registry.get_counter(
                "llm_requests_total",
                tags={"provider": "openai", "model": "gpt-4"},
            )
            == 1.0
        )
        assert (
            registry.get_counter(
                "llm_requests_total",
                tags={"provider": "anthropic", "model": "claude-3"},
            )
            == 1.0
        )


class TestLLMErrorRecording:
    """Tests for recording LLM errors."""

    def test_record_error(self) -> None:
        """Recording an error increments error counter."""
        registry = MetricsRegistry()
        llm = LLMMetrics(registry)
        llm.record_error("openai", "timeout")
        assert (
            registry.get_counter(
                "llm_errors_total",
                tags={"provider": "openai", "error_type": "timeout"},
            )
            == 1.0
        )

    def test_multiple_error_types(self) -> None:
        """Different error types are tracked separately."""
        registry = MetricsRegistry()
        llm = LLMMetrics(registry)
        llm.record_error("openai", "timeout")
        llm.record_error("openai", "rate_limit")
        llm.record_error("openai", "timeout")
        assert (
            registry.get_counter(
                "llm_errors_total",
                tags={"provider": "openai", "error_type": "timeout"},
            )
            == 2.0
        )
        assert (
            registry.get_counter(
                "llm_errors_total",
                tags={"provider": "openai", "error_type": "rate_limit"},
            )
            == 1.0
        )
