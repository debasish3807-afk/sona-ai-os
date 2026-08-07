"""Tests for retry manager.

Tests verify retry logic, backoff calculation, and state tracking.
"""

import pytest
from sona_brain.domain.execution import StepResult, StepState
from sona_brain.infrastructure.retry_manager import RetryConfig, RetryManager
from sona_thalamus.domain.execution_plan import ExecutionStep, ExecutionStepType


def _make_step(step_id: str = "s1", retryable: bool = True) -> ExecutionStep:
    """Create a test step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.LLM_CALL,
        target="model",
        retryable=retryable,
    )


def _make_failed_result(step_id: str = "s1") -> StepResult:
    """Create a failed step result."""
    return StepResult(step_id=step_id, state=StepState.FAILED, error="Error")


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self) -> None:
        """Verify default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay_seconds == 0.5
        assert config.max_delay_seconds == 30.0
        assert config.jitter is True
        assert config.backoff_factor == 2.0

    def test_custom_config(self) -> None:
        """Verify custom configuration."""
        config = RetryConfig(max_retries=5, base_delay_seconds=1.0, jitter=False)
        assert config.max_retries == 5
        assert config.base_delay_seconds == 1.0
        assert config.jitter is False


class TestRetryManager:
    """Tests for RetryManager."""

    def test_should_retry_retryable_step(self) -> None:
        """Retryable step with failed result should be retried."""
        mgr = RetryManager(RetryConfig(max_retries=3))
        step = _make_step(retryable=True)
        result = _make_failed_result()
        assert mgr.should_retry(step, result) is True

    def test_should_not_retry_non_retryable_step(self) -> None:
        """Non-retryable step should not be retried."""
        mgr = RetryManager(RetryConfig(max_retries=3))
        step = _make_step(retryable=False)
        result = _make_failed_result()
        assert mgr.should_retry(step, result) is False

    def test_should_not_retry_completed_step(self) -> None:
        """Completed step should not be retried."""
        mgr = RetryManager(RetryConfig(max_retries=3))
        step = _make_step()
        result = StepResult(step_id="s1", state=StepState.COMPLETED)
        assert mgr.should_retry(step, result) is False

    def test_should_not_retry_after_exhaustion(self) -> None:
        """Should not retry after max retries reached."""
        mgr = RetryManager(RetryConfig(max_retries=2))
        step = _make_step()
        result = _make_failed_result()

        # Record max retries
        mgr.record_attempt("s1", "error 1")
        mgr.record_attempt("s1", "error 2")

        assert mgr.should_retry(step, result) is False

    def test_record_attempt(self) -> None:
        """Record attempt increments count and stores error."""
        mgr = RetryManager(RetryConfig(max_retries=3))
        state = mgr.record_attempt("s1", "first error")
        assert state.attempt_count == 1
        assert state.errors == ["first error"]
        assert state.exhausted is False

    def test_record_attempt_until_exhausted(self) -> None:
        """Recording max attempts marks as exhausted."""
        mgr = RetryManager(RetryConfig(max_retries=2))
        mgr.record_attempt("s1", "error 1")
        state = mgr.record_attempt("s1", "error 2")
        assert state.exhausted is True

    def test_is_exhausted(self) -> None:
        """Check exhaustion state."""
        mgr = RetryManager(RetryConfig(max_retries=1))
        assert mgr.is_exhausted("s1") is False
        mgr.record_attempt("s1", "error")
        assert mgr.is_exhausted("s1") is True

    def test_get_attempt_count(self) -> None:
        """Get current attempt count."""
        mgr = RetryManager()
        assert mgr.get_attempt_count("s1") == 0
        mgr.record_attempt("s1", "error")
        assert mgr.get_attempt_count("s1") == 1

    def test_reset(self) -> None:
        """Reset clears retry state."""
        mgr = RetryManager(RetryConfig(max_retries=1))
        mgr.record_attempt("s1", "error")
        mgr.reset("s1")
        assert mgr.get_attempt_count("s1") == 0
        assert mgr.is_exhausted("s1") is False

    @pytest.mark.asyncio
    async def test_wait_before_retry(self) -> None:
        """Verify wait returns a delay."""
        mgr = RetryManager(RetryConfig(base_delay_seconds=0.001, jitter=False))
        delay = await mgr.wait_before_retry("s1")
        assert delay >= 0.0

    def test_get_retry_state_none(self) -> None:
        """Get retry state for unknown step returns None."""
        mgr = RetryManager()
        assert mgr.get_retry_state("unknown") is None

    def test_get_retry_state_exists(self) -> None:
        """Get retry state after recording."""
        mgr = RetryManager()
        mgr.record_attempt("s1", "err")
        state = mgr.get_retry_state("s1")
        assert state is not None
        assert state.step_id == "s1"

    def test_multiple_steps_tracked_independently(self) -> None:
        """Different steps have independent retry states."""
        mgr = RetryManager(RetryConfig(max_retries=2))
        mgr.record_attempt("s1", "error")
        mgr.record_attempt("s2", "error")
        mgr.record_attempt("s2", "error 2")

        assert mgr.get_attempt_count("s1") == 1
        assert mgr.get_attempt_count("s2") == 2
        assert mgr.is_exhausted("s1") is False
        assert mgr.is_exhausted("s2") is True
