"""Tests for execution state manager.

Tests verify state transitions, ready-step queries, and thread safety.
"""

import pytest

from sona_brain.domain.execution import ExecutionState, StepState
from sona_brain.infrastructure.state_manager import ExecutionStateManager
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


def _make_plan(steps: list[ExecutionStep]) -> ExecutionPlan:
    """Helper to create a test plan."""
    return ExecutionPlan(
        plan_id="test-plan",
        intent="test",
        steps=steps,
        model_id="test-model",
        provider="test-provider",
    )


def _make_step(
    step_id: str,
    depends_on: list[str] | None = None,
) -> ExecutionStep:
    """Helper to create a test step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.LLM_CALL,
        target="test-model",
        depends_on=depends_on or [],
    )


class TestExecutionStateManager:
    """Tests for ExecutionStateManager."""

    def test_initial_state_is_created(self) -> None:
        """Verify initial execution state is CREATED."""
        plan = _make_plan([_make_step("s1")])
        mgr = ExecutionStateManager(plan)
        assert mgr.context.state == ExecutionState.CREATED

    def test_all_steps_initialized_as_pending(self) -> None:
        """Verify all steps start as PENDING."""
        plan = _make_plan([_make_step("s1"), _make_step("s2")])
        mgr = ExecutionStateManager(plan)
        assert mgr.context.step_results["s1"].state == StepState.PENDING
        assert mgr.context.step_results["s2"].state == StepState.PENDING

    @pytest.mark.asyncio
    async def test_start_execution(self) -> None:
        """Verify start_execution transitions to RUNNING."""
        plan = _make_plan([_make_step("s1")])
        mgr = ExecutionStateManager(plan)
        await mgr.start_execution()
        assert mgr.context.state == ExecutionState.RUNNING

    @pytest.mark.asyncio
    async def test_mark_step_running(self) -> None:
        """Verify marking a step as running."""
        plan = _make_plan([_make_step("s1")])
        mgr = ExecutionStateManager(plan)
        await mgr.mark_step_running("s1")
        assert mgr.context.step_results["s1"].state == StepState.RUNNING
        assert mgr.context.step_results["s1"].started_at is not None

    @pytest.mark.asyncio
    async def test_mark_step_completed(self) -> None:
        """Verify marking a step as completed."""
        plan = _make_plan([_make_step("s1")])
        mgr = ExecutionStateManager(plan)
        await mgr.mark_step_completed("s1", output={"data": "value"}, latency_ms=100.0)
        result = mgr.context.step_results["s1"]
        assert result.state == StepState.COMPLETED
        assert result.output == {"data": "value"}
        assert result.latency_ms == 100.0
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_mark_step_failed(self) -> None:
        """Verify marking a step as failed."""
        plan = _make_plan([_make_step("s1")])
        mgr = ExecutionStateManager(plan)
        await mgr.mark_step_failed("s1", error="Timeout", latency_ms=30000.0)
        result = mgr.context.step_results["s1"]
        assert result.state == StepState.FAILED
        assert result.error == "Timeout"
        assert "Timeout" in mgr.context.errors[0]

    @pytest.mark.asyncio
    async def test_mark_step_retrying(self) -> None:
        """Verify marking a step as retrying increments count."""
        plan = _make_plan([_make_step("s1")])
        mgr = ExecutionStateManager(plan)
        await mgr.mark_step_retrying("s1")
        assert mgr.context.step_results["s1"].state == StepState.RETRYING
        assert mgr.context.step_results["s1"].retry_count == 1

    @pytest.mark.asyncio
    async def test_complete_execution(self) -> None:
        """Verify completing execution."""
        plan = _make_plan([_make_step("s1")])
        mgr = ExecutionStateManager(plan)
        await mgr.complete_execution(final_output="done")
        assert mgr.context.state == ExecutionState.COMPLETED
        assert mgr.context.final_output == "done"
        assert mgr.context.completed_at is not None

    @pytest.mark.asyncio
    async def test_fail_execution(self) -> None:
        """Verify failing execution."""
        plan = _make_plan([_make_step("s1")])
        mgr = ExecutionStateManager(plan)
        await mgr.fail_execution("Fatal error")
        assert mgr.context.state == ExecutionState.FAILED
        assert "Fatal error" in mgr.context.errors

    def test_get_ready_steps_no_deps(self) -> None:
        """Steps with no dependencies are immediately ready."""
        plan = _make_plan([_make_step("s1"), _make_step("s2")])
        mgr = ExecutionStateManager(plan)
        ready = mgr.get_ready_steps()
        assert len(ready) == 2

    def test_get_ready_steps_with_deps(self) -> None:
        """Steps with unmet dependencies are not ready."""
        plan = _make_plan(
            [
                _make_step("s1"),
                _make_step("s2", depends_on=["s1"]),
            ]
        )
        mgr = ExecutionStateManager(plan)
        ready = mgr.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].step_id == "s1"

    @pytest.mark.asyncio
    async def test_get_ready_steps_after_completion(self) -> None:
        """Dependent steps become ready after deps complete."""
        plan = _make_plan(
            [
                _make_step("s1"),
                _make_step("s2", depends_on=["s1"]),
            ]
        )
        mgr = ExecutionStateManager(plan)
        await mgr.mark_step_completed("s1", output="done")
        ready = mgr.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].step_id == "s2"

    @pytest.mark.asyncio
    async def test_is_complete(self) -> None:
        """Verify is_complete returns True when all steps are terminal."""
        plan = _make_plan([_make_step("s1"), _make_step("s2")])
        mgr = ExecutionStateManager(plan)
        assert mgr.is_complete() is False
        await mgr.mark_step_completed("s1")
        assert mgr.is_complete() is False
        await mgr.mark_step_completed("s2")
        assert mgr.is_complete() is True

    def test_get_completed_count(self) -> None:
        """Verify completed count tracking."""
        plan = _make_plan([_make_step("s1"), _make_step("s2")])
        mgr = ExecutionStateManager(plan)
        assert mgr.get_completed_count() == 0

    @pytest.mark.asyncio
    async def test_mark_replanning(self) -> None:
        """Verify replanning state transition."""
        plan = _make_plan([_make_step("s1")])
        mgr = ExecutionStateManager(plan)
        await mgr.mark_replanning()
        assert mgr.context.state == ExecutionState.REPLANNING
