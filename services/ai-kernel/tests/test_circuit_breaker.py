"""Unit tests for the circuit breaker module.

Tests verify state transitions, failure threshold, recovery timeout,
and half-open behavior.
"""

import time

from sona_ai_kernel.infrastructure.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig defaults."""

    def test_default_values(self) -> None:
        """Verify default configuration values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 30.0
        assert config.success_threshold == 2
        assert config.half_open_max_calls == 1

    def test_custom_values(self) -> None:
        """Verify custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=10.0,
            success_threshold=1,
            half_open_max_calls=2,
        )
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 10.0
        assert config.success_threshold == 1
        assert config.half_open_max_calls == 2


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    def test_initial_state_is_closed(self) -> None:
        """Circuit starts in CLOSED state."""
        cb = CircuitBreaker("test_provider")
        assert cb.state == CircuitState.CLOSED

    def test_can_execute_when_closed(self) -> None:
        """Requests allowed when circuit is CLOSED."""
        cb = CircuitBreaker("test_provider")
        assert cb.can_execute() is True

    def test_opens_after_failure_threshold(self) -> None:
        """Circuit opens after reaching failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test_provider", config)

        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

    def test_blocks_execution_when_open(self) -> None:
        """Requests blocked when circuit is OPEN."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test_provider", config)

        cb.record_failure()
        cb.record_failure()

        assert cb.can_execute() is False

    def test_transitions_to_half_open_after_recovery_timeout(self) -> None:
        """Circuit transitions from OPEN to HALF_OPEN after recovery timeout."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1.0)
        cb = CircuitBreaker("test_provider", config)

        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Simulate time passage
        cb._last_failure_time = time.time() - 2.0
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_allows_limited_calls(self) -> None:
        """HALF_OPEN state allows limited concurrent calls."""
        config = CircuitBreakerConfig(
            failure_threshold=2, recovery_timeout=0.0, half_open_max_calls=1
        )
        cb = CircuitBreaker("test_provider", config)

        cb.record_failure()
        cb.record_failure()

        # Should be half-open now since recovery_timeout is 0
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.can_execute() is True

    def test_closes_after_success_threshold_in_half_open(self) -> None:
        """Circuit closes after reaching success threshold in HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.0,
            success_threshold=2,
        )
        cb = CircuitBreaker("test_provider", config)

        cb.record_failure()
        cb.record_failure()

        # Trigger half-open check
        _ = cb.state  # transitions to HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN  # not yet

        cb.record_success()
        assert cb.state == CircuitState.CLOSED  # now closed

    def test_reopens_on_failure_in_half_open(self) -> None:
        """Circuit reopens if a failure occurs in HALF_OPEN state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.0,
        )
        cb = CircuitBreaker("test_provider", config)

        cb.record_failure()
        cb.record_failure()

        # Trigger half-open
        _ = cb.state

        cb.record_failure()
        assert cb._state == CircuitState.OPEN

    def test_success_resets_failure_count_in_closed(self) -> None:
        """Success in CLOSED state resets the failure counter."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test_provider", config)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Resets counter

        # One more failure should NOT open the circuit
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

    def test_reset_returns_to_closed(self) -> None:
        """Reset returns circuit to initial CLOSED state."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test_provider", config)

        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_name_is_preserved(self) -> None:
        """Circuit breaker preserves the provider name."""
        cb = CircuitBreaker("my_provider")
        assert cb.name == "my_provider"
