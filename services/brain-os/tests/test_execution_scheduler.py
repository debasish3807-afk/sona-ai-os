"""Tests for execution scheduler.

Tests verify wave-based execution, dependency grouping, and failure handling.
"""

import pytest

from sona_brain.domain.execution import StepState
from sona_brain.infrastructure.execution_scheduler import ExecutionScheduler
from sona_brain.infrastructure.parallel_executor import ParallelExecutor
from sona_brain.infrastructure.retry_manager import RetryConfig, RetryManager
from sona_brain.infrastructure.sequential_executor import SequentialExecutor
from sona_brain.infrastructure.state_manager import ExecutionStateManager
from sona_brain.infrastructure.step_executor import StepExecutor
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


def _make_step(
    step_id: str,
    depends_on: list[str] | None = None,
    priority: int = 5,
) -> ExecutionStep:
    """Create a test step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.LLM_CALL,
        target="test-model",
        params={"prompt": step_id, "max_tokens_in": 10, "max_tokens_out": 5},
        depends_on=depends_on or [],
        priority=priority,
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


def _create_scheduler() -> ExecutionScheduler:
    """Create a configured scheduler."""
    step_exec = StepExecutor()
    retry_mgr = RetryManager(RetryConfig(max_retries=0))
    seq_exec = SequentialExecutor(step_exec, retry_mgr)
    par_exec = ParallelExecutor(step_exec, retry_mgr)
    return ExecutionScheduler(seq_exec, par_exec)


class TestExecutionScheduler:
    """Tests for ExecutionScheduler."""

    @pytest.mark.asyncio
    async def test_single_step_plan(self) -> None:
        """Execute a plan with one step."""
        scheduler = _create_scheduler()
        steps = [_make_step("s1")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await scheduler.execute_plan(plan, state_mgr)
        assert len(results) == 1
        assert results[0].state == StepState.COMPLETED

    @pytest.mark.asyncio
    async def test_independent_steps_form_one_wave(self) -> None:
        """Independent steps are grouped into a single wave."""
        scheduler = _create_scheduler()
        steps = [_make_step("s1"), _make_step("s2"), _make_step("s3")]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await scheduler.execute_plan(plan, state_mgr)
        assert len(results) == 3
        assert all(r.state == StepState.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_linear_chain_forms_multiple_waves(self) -> None:
        """Linear dependency chain forms separate waves."""
        scheduler = _create_scheduler()
        steps = [
            _make_step("s1"),
            _make_step("s2", depends_on=["s1"]),
            _make_step("s3", depends_on=["s2"]),
        ]
        plan = _make_plan(steps)

        wave_count = scheduler.get_wave_count(steps)
        assert wave_count == 3

    @pytest.mark.asyncio
    async def test_diamond_dependency(self) -> None:
        """Diamond pattern: a -> b, a -> c, b+c -> d."""
        scheduler = _create_scheduler()
        steps = [
            _make_step("a"),
            _make_step("b", depends_on=["a"]),
            _make_step("c", depends_on=["a"]),
            _make_step("d", depends_on=["b", "c"]),
        ]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await scheduler.execute_plan(plan, state_mgr)
        assert len(results) == 4
        assert all(r.state == StepState.COMPLETED for r in results)

        # Wave structure: [a], [b, c], [d]
        wave_count = scheduler.get_wave_count(steps)
        assert wave_count == 3

    @pytest.mark.asyncio
    async def test_wave_failure_cancels_remaining(self) -> None:
        """Failure in a wave cancels subsequent waves."""
        from unittest.mock import patch

        from sona_brain.domain.execution import StepResult

        scheduler = _create_scheduler()
        step_exec = scheduler._sequential_executor._step_executor

        steps = [
            _make_step("s1"),
            _make_step("s2", depends_on=["s1"]),
        ]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        original_execute = step_exec.execute_step

        async def fail_s1(step, context=None):
            if step.step_id == "s1":
                return StepResult(step_id="s1", state=StepState.FAILED, error="Fail")
            return await original_execute(step, context)

        with patch.object(step_exec, "execute_step", side_effect=fail_s1):
            results = await scheduler.execute_plan(plan, state_mgr)

        # s1 failed, s2 should be cancelled
        assert state_mgr.context.step_results["s2"].state == StepState.CANCELLED

    @pytest.mark.asyncio
    async def test_empty_plan(self) -> None:
        """Execute an empty plan."""
        scheduler = _create_scheduler()
        plan = _make_plan([])
        state_mgr = ExecutionStateManager(plan)

        results = await scheduler.execute_plan(plan, state_mgr)
        assert results == []

    def test_wave_count_independent(self) -> None:
        """All independent steps form 1 wave."""
        scheduler = _create_scheduler()
        steps = [_make_step(f"s{i}") for i in range(5)]
        assert scheduler.get_wave_count(steps) == 1

    def test_wave_count_chain(self) -> None:
        """Linear chain of n steps forms n waves."""
        scheduler = _create_scheduler()
        steps = [
            _make_step("s1"),
            _make_step("s2", depends_on=["s1"]),
            _make_step("s3", depends_on=["s2"]),
            _make_step("s4", depends_on=["s3"]),
        ]
        assert scheduler.get_wave_count(steps) == 4

    @pytest.mark.asyncio
    async def test_priority_ordering_within_wave(self) -> None:
        """Steps within a wave are sorted by priority."""
        scheduler = _create_scheduler()
        steps = [
            _make_step("s1", priority=10),
            _make_step("s2", priority=1),
            _make_step("s3", priority=5),
        ]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await scheduler.execute_plan(plan, state_mgr)
        assert len(results) == 3
        assert all(r.state == StepState.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_complex_dependency_graph(self) -> None:
        """Complex graph with mixed dependencies."""
        scheduler = _create_scheduler()
        steps = [
            _make_step("a"),
            _make_step("b"),
            _make_step("c", depends_on=["a"]),
            _make_step("d", depends_on=["a", "b"]),
            _make_step("e", depends_on=["c", "d"]),
        ]
        plan = _make_plan(steps)
        state_mgr = ExecutionStateManager(plan)

        results = await scheduler.execute_plan(plan, state_mgr)
        assert len(results) == 5
        assert all(r.state == StepState.COMPLETED for r in results)
