"""Unit tests for CircuitBreaker."""

import time

from sona_mcp.infrastructure.circuit_breaker import (
    CircuitBreakerRegistry,
    CircuitState,
    ToolCircuitBreaker,
)


class TestToolCircuitBreakerStates:
    def test_initial_state_closed(self) -> None:
        cb = ToolCircuitBreaker("tool1")
        assert cb.state == CircuitState.CLOSED

    def test_can_execute_when_closed(self) -> None:
        cb = ToolCircuitBreaker("tool1")
        assert cb.can_execute() is True

    def test_opens_after_threshold(self) -> None:
        cb = ToolCircuitBreaker("tool1", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_cannot_execute_when_open(self) -> None:
        cb = ToolCircuitBreaker("tool1", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.can_execute() is False

    def test_half_open_after_timeout(self) -> None:
        cb = ToolCircuitBreaker("tool1", failure_threshold=1, recovery_timeout=0.001)
        cb.record_failure()
        # With a very short recovery timeout, sleep to ensure we pass it
        time.sleep(0.01)
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_allows_execution(self) -> None:
        cb = ToolCircuitBreaker("tool1", failure_threshold=1, recovery_timeout=0.001)
        cb.record_failure()
        time.sleep(0.01)
        assert cb.can_execute() is True


class TestToolCircuitBreakerRecovery:
    def test_success_closes_from_half_open(self) -> None:
        cb = ToolCircuitBreaker(
            "tool1", failure_threshold=1, recovery_timeout=0.001, success_threshold=1
        )
        cb.record_failure()
        time.sleep(0.01)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_failure_in_half_open_reopens(self) -> None:
        cb = ToolCircuitBreaker("tool1", failure_threshold=1, recovery_timeout=0.001)
        cb.record_failure()
        time.sleep(0.01)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_multiple_successes_needed(self) -> None:
        cb = ToolCircuitBreaker(
            "tool1", failure_threshold=1, recovery_timeout=0.001, success_threshold=3
        )
        cb.record_failure()
        time.sleep(0.01)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_success_resets_failure_count(self) -> None:
        cb = ToolCircuitBreaker("tool1", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED


class TestToolCircuitBreakerReset:
    def test_reset_clears_state(self) -> None:
        cb = ToolCircuitBreaker("tool1", failure_threshold=1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_reset_allows_execution(self) -> None:
        cb = ToolCircuitBreaker("tool1", failure_threshold=1)
        cb.record_failure()
        cb.reset()
        assert cb.can_execute() is True


class TestToolCircuitBreakerCounters:
    def test_total_failures(self) -> None:
        cb = ToolCircuitBreaker("tool1", failure_threshold=10)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.total_failures == 3

    def test_total_successes(self) -> None:
        cb = ToolCircuitBreaker("tool1")
        cb.record_success()
        cb.record_success()
        assert cb.total_successes == 2


class TestCircuitBreakerRegistry:
    def test_get_creates_breaker(self) -> None:
        reg = CircuitBreakerRegistry()
        breaker = reg.get_breaker("tool1")
        assert breaker is not None
        assert breaker.tool_name == "tool1"

    def test_get_returns_same_breaker(self) -> None:
        reg = CircuitBreakerRegistry()
        b1 = reg.get_breaker("tool1")
        b2 = reg.get_breaker("tool1")
        assert b1 is b2

    def test_can_execute(self) -> None:
        reg = CircuitBreakerRegistry(failure_threshold=2)
        assert reg.can_execute("tool1") is True
        reg.record_failure("tool1")
        reg.record_failure("tool1")
        assert reg.can_execute("tool1") is False

    def test_record_success(self) -> None:
        reg = CircuitBreakerRegistry()
        reg.record_success("tool1")
        assert reg.get_state("tool1") == CircuitState.CLOSED

    def test_get_state(self) -> None:
        reg = CircuitBreakerRegistry(failure_threshold=1)
        reg.record_failure("tool1")
        assert reg.get_state("tool1") == CircuitState.OPEN

    def test_reset_single(self) -> None:
        reg = CircuitBreakerRegistry(failure_threshold=1)
        reg.record_failure("tool1")
        reg.reset("tool1")
        assert reg.get_state("tool1") == CircuitState.CLOSED

    def test_reset_all(self) -> None:
        reg = CircuitBreakerRegistry(failure_threshold=1)
        reg.record_failure("t1")
        reg.record_failure("t2")
        reg.reset_all()
        assert reg.get_state("t1") == CircuitState.CLOSED
        assert reg.get_state("t2") == CircuitState.CLOSED

    def test_breaker_count(self) -> None:
        reg = CircuitBreakerRegistry()
        reg.get_breaker("t1")
        reg.get_breaker("t2")
        assert reg.breaker_count == 2
