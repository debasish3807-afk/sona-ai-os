"""Tests for Brain OS execution domain models.

Tests verify StepResult, ExecutionContext, StepState, and ExecutionState
are correctly defined and behave as expected.
"""

from datetime import UTC, datetime

from sona_brain.domain.execution import (
    ExecutionContext,
    ExecutionState,
    StepResult,
    StepState,
)


class TestStepState:
    """Tests for StepState enum."""

    def test_all_states_defined(self) -> None:
        """Verify all expected step states exist."""
        assert StepState.PENDING == "pending"
        assert StepState.RUNNING == "running"
        assert StepState.COMPLETED == "completed"
        assert StepState.FAILED == "failed"
        assert StepState.SKIPPED == "skipped"
        assert StepState.CANCELLED == "cancelled"
        assert StepState.RETRYING == "retrying"

    def test_state_count(self) -> None:
        """Verify the number of states."""
        assert len(StepState) == 7

    def test_is_str_enum(self) -> None:
        """Verify StepState values are strings."""
        for state in StepState:
            assert isinstance(state, str)
            assert state.value == state


class TestExecutionState:
    """Tests for ExecutionState enum."""

    def test_all_states_defined(self) -> None:
        """Verify all expected execution states exist."""
        assert ExecutionState.CREATED == "created"
        assert ExecutionState.RUNNING == "running"
        assert ExecutionState.COMPLETED == "completed"
        assert ExecutionState.FAILED == "failed"
        assert ExecutionState.CANCELLED == "cancelled"
        assert ExecutionState.REPLANNING == "replanning"

    def test_state_count(self) -> None:
        """Verify the number of execution states."""
        assert len(ExecutionState) == 6


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_minimal_creation(self) -> None:
        """Create StepResult with minimal fields."""
        result = StepResult(step_id="step-1", state=StepState.PENDING)
        assert result.step_id == "step-1"
        assert result.state == StepState.PENDING
        assert result.output is None
        assert result.error is None
        assert result.latency_ms == 0.0
        assert result.retry_count == 0

    def test_completed_result(self) -> None:
        """Create a completed step result with output."""
        now = datetime.now(UTC)
        result = StepResult(
            step_id="step-2",
            state=StepState.COMPLETED,
            output={"content": "hello"},
            latency_ms=150.5,
            started_at=now,
            completed_at=now,
        )
        assert result.state == StepState.COMPLETED
        assert result.output == {"content": "hello"}
        assert result.latency_ms == 150.5

    def test_failed_result(self) -> None:
        """Create a failed step result with error."""
        result = StepResult(
            step_id="step-3",
            state=StepState.FAILED,
            error="Timeout exceeded",
            latency_ms=30000.0,
            retry_count=2,
        )
        assert result.state == StepState.FAILED
        assert result.error == "Timeout exceeded"
        assert result.retry_count == 2

    def test_mutability(self) -> None:
        """Verify StepResult is mutable (non-frozen dataclass)."""
        result = StepResult(step_id="step-1", state=StepState.PENDING)
        result.state = StepState.RUNNING
        assert result.state == StepState.RUNNING


class TestExecutionContext:
    """Tests for ExecutionContext dataclass."""

    def test_minimal_creation(self) -> None:
        """Create ExecutionContext with plan_id only."""
        ctx = ExecutionContext(plan_id="plan-1")
        assert ctx.plan_id == "plan-1"
        assert ctx.state == ExecutionState.CREATED
        assert ctx.step_results == {}
        assert ctx.final_output == ""
        assert ctx.total_latency_ms == 0.0
        assert ctx.total_tokens_in == 0
        assert ctx.total_tokens_out == 0
        assert ctx.errors == []

    def test_created_at_is_set(self) -> None:
        """Verify created_at is automatically set."""
        ctx = ExecutionContext(plan_id="plan-1")
        assert ctx.created_at is not None
        assert ctx.created_at.tzinfo is not None

    def test_completed_at_initially_none(self) -> None:
        """Verify completed_at starts as None."""
        ctx = ExecutionContext(plan_id="plan-1")
        assert ctx.completed_at is None

    def test_state_transitions(self) -> None:
        """Verify state can be updated."""
        ctx = ExecutionContext(plan_id="plan-1")
        ctx.state = ExecutionState.RUNNING
        assert ctx.state == ExecutionState.RUNNING
        ctx.state = ExecutionState.COMPLETED
        assert ctx.state == ExecutionState.COMPLETED

    def test_step_results_tracking(self) -> None:
        """Verify step results can be tracked."""
        ctx = ExecutionContext(plan_id="plan-1")
        ctx.step_results["s1"] = StepResult(step_id="s1", state=StepState.COMPLETED)
        ctx.step_results["s2"] = StepResult(step_id="s2", state=StepState.FAILED)
        assert len(ctx.step_results) == 2
        assert ctx.step_results["s1"].state == StepState.COMPLETED

    def test_errors_accumulate(self) -> None:
        """Verify errors can be accumulated."""
        ctx = ExecutionContext(plan_id="plan-1")
        ctx.errors.append("Error 1")
        ctx.errors.append("Error 2")
        assert len(ctx.errors) == 2

    def test_metadata_storage(self) -> None:
        """Verify metadata can store arbitrary data."""
        ctx = ExecutionContext(plan_id="plan-1")
        ctx.metadata["key"] = "value"
        ctx.metadata["nested"] = {"a": 1}
        assert ctx.metadata["key"] == "value"
