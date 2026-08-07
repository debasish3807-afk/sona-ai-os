"""Tests for parallel executor.

Tests verify concurrent execution, max concurrency, and failure handling.
"""

import asyncio

import pytest

from sona_brain.domain.execution import StepState
from sona_brain.infrastructure.parallel_executor import ParallelExecutor
from sona_brain.infrastructure.retry_manager import RetryConfig, RetryManager
from sona_brain.infrastructure.state_manager import ExecutionStateManager
from sona_brain.infrastructure.step_executor import StepExecutor
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


def _make_step(step_id: str, params: dict | None = None) -> ExecutionStep:
    """Create a test step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.TOOL_CALL,
        target="test-tool",
        params=params or {},
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


class TestParallelExecutor:
    """Tests for ParallelExecutor."""

    @pytest.mark.asyncio
    async def test_execute_single_step(self) -> None:
        """Execute a single step in parallel mode."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = ParallelExecutor(step_exec, retry_mgr)

        steps = [_make_step("s1")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute(steps, state_mgr)
        assert len(results) == 1
        assert results[0].state == StepState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_multiple_steps_concurrently(self) -> None:
        """Execute multiple steps and verify all complete."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = ParallelExecutor(step_exec, retry_mgr)

        steps = [_make_step(f"s{i}") for i in range(5)]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute(steps, state_mgr)
        assert len(results) == 5
        assert all(r.state == StepState.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_respects_max_concurrency(self) -> None:
        """Verify max concurrency limit is enforced."""
        from unittest.mock import patch

        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = ParallelExecutor(step_exec, retry_mgr, max_concurrency=2)

        assert executor.max_concurrency == 2

        concurrent_count = 0
        max_concurrent = 0

        original_execute = step_exec.execute_step

        async def tracking_execute(step, context=None):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            result = await original_execute(step, context)
            concurrent_count -= 1
            return result

        steps = [_make_step(f"s{i}") for i in range(4)]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        with patch.object(step_exec, "execute_step", side_effect=tracking_execute):
            results = await executor.execute(steps, state_mgr)

        assert len(results) == 4
        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_handles_individual_failures(self) -> None:
        """Individual step failures don't block other steps."""
        from unittest.mock import patch

        from sona_brain.domain.execution import StepResult

        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = ParallelExecutor(step_exec, retry_mgr)

        original_execute = step_exec.execute_step

        async def partial_failure(step, context=None):
            if step.step_id == "s2":
                return StepResult(step_id="s2", state=StepState.FAILED, error="Error")
            return await original_execute(step, context)

        steps = [_make_step("s1"), _make_step("s2"), _make_step("s3")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        with patch.object(step_exec, "execute_step", side_effect=partial_failure):
            results = await executor.execute(steps, state_mgr)

        completed = [r for r in results if r.state == StepState.COMPLETED]
        failed = [r for r in results if r.state == StepState.FAILED]
        assert len(completed) == 2
        assert len(failed) == 1

    @pytest.mark.asyncio
    async def test_empty_steps_returns_empty(self) -> None:
        """Execute with no steps returns empty list."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = ParallelExecutor(step_exec, retry_mgr)

        plan = _make_plan([])
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute([], state_mgr)
        assert results == []

    @pytest.mark.asyncio
    async def test_state_manager_updated_for_all_steps(self) -> None:
        """State manager updated for every parallel step."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = ParallelExecutor(step_exec, retry_mgr)

        steps = [_make_step("s1"), _make_step("s2")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        await executor.execute(steps, state_mgr)
        assert state_mgr.context.step_results["s1"].state == StepState.COMPLETED
        assert state_mgr.context.step_results["s2"].state == StepState.COMPLETED

    @pytest.mark.asyncio
    async def test_shared_context_available(self) -> None:
        """Shared context is available to all steps."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = ParallelExecutor(step_exec, retry_mgr)

        steps = [_make_step("s1")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        shared = {"prior_output": "data"}
        results = await executor.execute(steps, state_mgr, shared_context=shared)
        assert results[0].state == StepState.COMPLETED

    @pytest.mark.asyncio
    async def test_latency_recorded_for_all(self) -> None:
        """All results have latency recorded."""
        step_exec = StepExecutor()
        retry_mgr = RetryManager(RetryConfig(max_retries=0))
        executor = ParallelExecutor(step_exec, retry_mgr)

        steps = [_make_step(f"s{i}") for i in range(3)]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await executor.execute(steps, state_mgr)
        assert all(r.latency_ms >= 0 for r in results)
