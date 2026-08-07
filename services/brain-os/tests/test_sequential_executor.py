"""Tests for sequential executor.

Tests verify ordered execution, dependency respect, and failure stopping.
"""

import pytest
from sona_brain.domain.execution import StepState
from sona_brain.infrastructure.retry_manager import RetryConfig, RetryManager
from sona_brain.infrastructure.sequential_executor import SequentialExecutor
from sona_brain.infrastructure.state_manager import ExecutionStateManager
from sona_brain.infrastructure.step_executor import StepExecutor
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


def _make_step(
    step_id: str,
    depends_on: list[str] | None = None,
    retryable: bool = True,
) -> ExecutionStep:
    """Create a test step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.LLM_CALL,
        target="test-model",
        params={"prompt": f"step {step_id}", "max_tokens_in": 10, "max_tokens_out": 5},
        depends_on=depends_on or [],
        retryable=retryable,
    )


def _make_plan(steps: list[ExecutionStep]) -> ExecutionPlan:
    """Create a test plan."""
    return ExecutionPlan(
        plan_id="test-plan",
        intent="test",
        steps=steps,
        model_id="test-model",
        provider="test-provider",
    )


class TestSequentialExecutor:
    """Tests for SequentialExecutor."""

    @pytest.mark.asyncio
    async def test_execute_single_step(self) -> None:
        """Execute a single step successfully."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = SequentialExecutor(step_exec, retry_mgr)

        steps = [_make_step("s1")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute(steps, state_mgr)
        assert len(results) == 1
        assert results[0].state == StepState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_multiple_steps_in_order(self) -> None:
        """Execute multiple independent steps in order."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = SequentialExecutor(step_exec, retry_mgr)

        steps = [_make_step("s1"), _make_step("s2"), _make_step("s3")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute(steps, state_mgr)
        assert len(results) == 3
        assert all(r.state == StepState.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_respects_dependency_order(self) -> None:
        """Steps with dependencies execute after their deps."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = SequentialExecutor(step_exec, retry_mgr)

        # s2 depends on s1, s3 depends on s2
        steps = [
            _make_step("s3", depends_on=["s2"]),
            _make_step("s1"),
            _make_step("s2", depends_on=["s1"]),
        ]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute(steps, state_mgr)
        # Should execute in order: s1, s2, s3
        assert results[0].step_id == "s1"
        assert results[1].step_id == "s2"
        assert results[2].step_id == "s3"

    @pytest.mark.asyncio
    async def test_stops_on_failure(self) -> None:
        """Execution stops when a step fails."""
        from unittest.mock import patch

        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = SequentialExecutor(step_exec, retry_mgr)

        steps = [_make_step("s1"), _make_step("s2"), _make_step("s3")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        # Make s2 fail
        original_execute = step_exec.execute_step

        async def failing_execute(step, context=None):
            if step.step_id == "s2":
                from sona_brain.domain.execution import StepResult

                return StepResult(step_id="s2", state=StepState.FAILED, error="Boom")
            return await original_execute(step, context)

        with patch.object(step_exec, "execute_step", side_effect=failing_execute):
            results = await executor.execute(steps, state_mgr)

        assert len(results) == 2  # s1 completed, s2 failed, s3 cancelled
        assert results[0].state == StepState.COMPLETED
        assert results[1].state == StepState.FAILED
        # s3 should be cancelled in state manager
        assert state_mgr.context.step_results["s3"].state == StepState.CANCELLED

    @pytest.mark.asyncio
    async def test_topological_sort_handles_diamond(self) -> None:
        """Handle diamond dependency pattern correctly."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = SequentialExecutor(step_exec, retry_mgr)

        # Diamond: s1 -> s2, s1 -> s3, s2 -> s4, s3 -> s4
        steps = [
            _make_step("s4", depends_on=["s2", "s3"]),
            _make_step("s2", depends_on=["s1"]),
            _make_step("s3", depends_on=["s1"]),
            _make_step("s1"),
        ]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute(steps, state_mgr)
        # s1 must come first, s4 must come last
        step_ids = [r.step_id for r in results]
        assert step_ids[0] == "s1"
        assert step_ids[-1] == "s4"

    @pytest.mark.asyncio
    async def test_empty_steps_list(self) -> None:
        """Execute with no steps returns empty list."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = SequentialExecutor(step_exec, retry_mgr)

        plan = _make_plan([])
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute([], state_mgr)
        assert results == []

    @pytest.mark.asyncio
    async def test_context_passed_to_dependents(self) -> None:
        """Output from step is available as context to dependents."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = SequentialExecutor(step_exec, retry_mgr)

        steps = [
            _make_step("s1"),
            _make_step("s2", depends_on=["s1"]),
        ]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute(steps, state_mgr)
        # Both should complete - context passing doesn't break execution
        assert all(r.state == StepState.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_state_manager_updated_correctly(self) -> None:
        """State manager reflects correct states after execution."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = SequentialExecutor(step_exec, retry_mgr)

        steps = [_make_step("s1"), _make_step("s2")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        await executor.execute(steps, state_mgr)
        assert state_mgr.context.step_results["s1"].state == StepState.COMPLETED
        assert state_mgr.context.step_results["s2"].state == StepState.COMPLETED
