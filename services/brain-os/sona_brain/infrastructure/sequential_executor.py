"""Sequential executor for Brain OS.

Executes steps one-by-one in dependency order using topological sort,
passing outputs from completed steps to dependents.
"""

from typing import Any

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.infrastructure.retry_manager import RetryManager
from sona_brain.infrastructure.state_manager import ExecutionStateManager
from sona_brain.infrastructure.step_executor import StepExecutor
from sona_thalamus.domain.execution_plan import ExecutionStep

logger = structlog.get_logger()


class SequentialExecutor:
    """Executes steps sequentially in topological order.

    Respects dependencies between steps, passes outputs from completed
    steps as context to dependents, and stops on non-retryable failures.
    """

    def __init__(
        self,
        step_executor: StepExecutor,
        retry_manager: RetryManager,
    ) -> None:
        """Initialize with a step executor and retry manager.

        Args:
            step_executor: Executor for individual steps.
            retry_manager: Manager for retry logic.
        """
        self._step_executor = step_executor
        self._retry_manager = retry_manager

    async def execute(
        self,
        steps: list[ExecutionStep],
        state_manager: ExecutionStateManager,
    ) -> list[StepResult]:
        """Execute steps sequentially in dependency order.

        Args:
            steps: Steps to execute in topological order.
            state_manager: State manager for tracking execution progress.

        Returns:
            List of StepResult objects for all executed steps.
        """
        sorted_steps = self._topological_sort(steps)
        results: list[StepResult] = []
        outputs: dict[str, Any] = {}

        for step in sorted_steps:
            # Build context from dependency outputs
            context = self._build_context(step, outputs)

            await state_manager.mark_step_running(step.step_id)
            result = await self._execute_with_retry(step, context, state_manager)
            results.append(result)

            if result.state == StepState.COMPLETED:
                await state_manager.mark_step_completed(
                    step.step_id,
                    output=result.output,
                    latency_ms=result.latency_ms,
                )
                outputs[step.step_id] = result.output
            else:
                await state_manager.mark_step_failed(
                    step.step_id,
                    error=result.error or "Unknown error",
                    latency_ms=result.latency_ms,
                )
                # Stop execution on failure
                logger.warning(
                    "sequential_execution_stopped",
                    failed_step=step.step_id,
                    error=result.error,
                )
                # Cancel remaining steps
                for remaining in sorted_steps[sorted_steps.index(step) + 1 :]:
                    await state_manager.mark_step_cancelled(remaining.step_id)
                break

        return results

    async def _execute_with_retry(
        self,
        step: ExecutionStep,
        context: dict[str, Any],
        state_manager: ExecutionStateManager,
    ) -> StepResult:
        """Execute a step with retry logic on failure.

        Args:
            step: The step to execute.
            context: Context for execution.
            state_manager: State manager for tracking.

        Returns:
            The final StepResult after all attempts.
        """
        result = await self._step_executor.execute_step(step, context)

        while result.state == StepState.FAILED and self._retry_manager.should_retry(step, result):
            self._retry_manager.record_attempt(step.step_id, result.error or "")
            await state_manager.mark_step_retrying(step.step_id)
            await self._retry_manager.wait_before_retry(step.step_id)
            result = await self._step_executor.execute_step(step, context)

        if result.state == StepState.FAILED and result.error:
            self._retry_manager.record_attempt(step.step_id, result.error)

        return result

    def _topological_sort(self, steps: list[ExecutionStep]) -> list[ExecutionStep]:
        """Sort steps in dependency order using topological sort.

        Args:
            steps: Steps to sort.

        Returns:
            Steps sorted so that dependencies come first.
        """
        step_map = {s.step_id: s for s in steps}
        visited: set[str] = set()
        result: list[ExecutionStep] = []

        def visit(step_id: str) -> None:
            if step_id in visited:
                return
            visited.add(step_id)
            step = step_map.get(step_id)
            if step is None:
                return
            for dep_id in step.depends_on:
                if dep_id in step_map:
                    visit(dep_id)
            result.append(step)

        for step in steps:
            visit(step.step_id)

        return result

    def _build_context(
        self,
        step: ExecutionStep,
        outputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Build execution context from dependency outputs.

        Args:
            step: The step that needs context.
            outputs: Map of step_id to output from completed steps.

        Returns:
            Context dictionary with dependency outputs.
        """
        context: dict[str, Any] = {}
        for dep_id in step.depends_on:
            if dep_id in outputs:
                context[dep_id] = outputs[dep_id]
        return context
