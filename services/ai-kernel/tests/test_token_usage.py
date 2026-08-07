"""Unit tests for the token usage manager.

Tests verify usage recording, session-level aggregation,
global aggregation, and provider-level aggregation.
"""

import pytest
from sona_ai_kernel.infrastructure.token_usage import TokenUsageManager, UsageRecord


class TestUsageRecord:
    """Tests for UsageRecord dataclass."""

    def test_creation(self) -> None:
        """Verify record is created with all fields."""
        record = UsageRecord(
            provider="ollama",
            model="llama3.2",
            tokens_input=100,
            tokens_output=50,
            latency_ms=200.5,
            session_id="sess-1",
        )
        assert record.provider == "ollama"
        assert record.model == "llama3.2"
        assert record.tokens_input == 100
        assert record.tokens_output == 50
        assert record.latency_ms == 200.5
        assert record.session_id == "sess-1"

    def test_is_frozen(self) -> None:
        """Verify record is immutable."""
        record = UsageRecord(
            provider="p",
            model="m",
            tokens_input=1,
            tokens_output=1,
            latency_ms=1.0,
            session_id="s",
        )
        with pytest.raises((TypeError, AttributeError)):
            record.provider = "changed"  # type: ignore[misc]


class TestTokenUsageManager:
    """Tests for TokenUsageManager."""

    def test_empty_manager(self) -> None:
        """Empty manager returns zero usage."""
        manager = TokenUsageManager()
        total = manager.get_total_usage()
        assert total["tokens_input"] == 0
        assert total["tokens_output"] == 0
        assert total["total"] == 0
        assert total["request_count"] == 0

    def test_record_single(self) -> None:
        """Single record is tracked correctly."""
        manager = TokenUsageManager()
        manager.record(
            UsageRecord(
                provider="ollama",
                model="llama3.2",
                tokens_input=100,
                tokens_output=50,
                latency_ms=200.0,
                session_id="sess-1",
            )
        )
        total = manager.get_total_usage()
        assert total["tokens_input"] == 100
        assert total["tokens_output"] == 50
        assert total["total"] == 150
        assert total["request_count"] == 1

    def test_record_multiple(self) -> None:
        """Multiple records are aggregated correctly."""
        manager = TokenUsageManager()
        manager.record(
            UsageRecord(
                provider="ollama",
                model="llama3.2",
                tokens_input=100,
                tokens_output=50,
                latency_ms=200.0,
                session_id="sess-1",
            )
        )
        manager.record(
            UsageRecord(
                provider="openai",
                model="gpt-4o",
                tokens_input=200,
                tokens_output=100,
                latency_ms=300.0,
                session_id="sess-2",
            )
        )
        total = manager.get_total_usage()
        assert total["tokens_input"] == 300
        assert total["tokens_output"] == 150
        assert total["total"] == 450
        assert total["request_count"] == 2

    def test_session_usage_filters(self) -> None:
        """Session usage returns only matching session records."""
        manager = TokenUsageManager()
        manager.record(
            UsageRecord(
                provider="ollama",
                model="llama3.2",
                tokens_input=100,
                tokens_output=50,
                latency_ms=200.0,
                session_id="sess-1",
            )
        )
        manager.record(
            UsageRecord(
                provider="openai",
                model="gpt-4o",
                tokens_input=200,
                tokens_output=100,
                latency_ms=300.0,
                session_id="sess-2",
            )
        )
        manager.record(
            UsageRecord(
                provider="ollama",
                model="llama3.2",
                tokens_input=50,
                tokens_output=25,
                latency_ms=150.0,
                session_id="sess-1",
            )
        )

        usage = manager.get_session_usage("sess-1")
        assert usage["tokens_input"] == 150
        assert usage["tokens_output"] == 75
        assert usage["total"] == 225

    def test_session_usage_empty_session(self) -> None:
        """Non-existent session returns zero usage."""
        manager = TokenUsageManager()
        manager.record(
            UsageRecord(
                provider="ollama",
                model="m",
                tokens_input=100,
                tokens_output=50,
                latency_ms=200.0,
                session_id="sess-1",
            )
        )
        usage = manager.get_session_usage("nonexistent")
        assert usage["tokens_input"] == 0
        assert usage["tokens_output"] == 0
        assert usage["total"] == 0

    def test_provider_usage(self) -> None:
        """Provider usage returns only matching provider records."""
        manager = TokenUsageManager()
        manager.record(
            UsageRecord(
                provider="ollama",
                model="llama3.2",
                tokens_input=100,
                tokens_output=50,
                latency_ms=200.0,
                session_id="s1",
            )
        )
        manager.record(
            UsageRecord(
                provider="openai",
                model="gpt-4o",
                tokens_input=200,
                tokens_output=100,
                latency_ms=300.0,
                session_id="s1",
            )
        )

        usage = manager.get_provider_usage("ollama")
        assert usage["tokens_input"] == 100
        assert usage["tokens_output"] == 50
        assert usage["total"] == 150

    def test_clear(self) -> None:
        """Clear removes all records."""
        manager = TokenUsageManager()
        manager.record(
            UsageRecord(
                provider="ollama",
                model="m",
                tokens_input=100,
                tokens_output=50,
                latency_ms=200.0,
                session_id="s1",
            )
        )
        manager.clear()
        total = manager.get_total_usage()
        assert total["request_count"] == 0
        assert total["total"] == 0
