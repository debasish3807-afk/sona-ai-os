"""Parallel executor for Brain OS.

Executes independent steps concurrently using asyncio, respecting
a configurable maximum concurrency limit.
"""

import asyncio
from typing import Any

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.infrastructure.retry_manager import RetryManager
from sona_brain.infrastructure.state_manager import ExecutionStateManager
from sona_brain.infrastructure.step_executor import StepExecutor
from sona_thalamus.domain.execution_plan import ExecutionStep

logger = structlog.get_logger()

DEFAULT_MAX_CONCURRENCY = 10


class ParallelExecutor:
    """Executes independent steps concurrently.

    Launches steps with no pending dependencies in parallel,
    respecting a configurable max concurrency limit via semaphore.
    """

    def __init__(
        self,
        step_executor: StepExecutor,
        retry_manager: RetryManager,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    ) -> None:
        """Initialize with executor, retry manager, and concurrency limit.

        Args:
            step_executor: Executor for individual steps.
            retry_manager: Manager for retry logic.
            max_concurrency: Maximum number of concurrent step executions.
        """
        self._step_executor = step_executor
        self._retry_manager = retry_manager
        self._max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    @property
    def max_concurrency(self) -> int:
        """Return the configured max concurrency."""
        return self._max_concurrency

    async def execute(
        self,
        steps: list[ExecutionStep],
        state_manager: ExecutionStateManager,
        shared_context: dict[str, Any] | None = None,
    ) -> list[StepResult]:
        """Execute a group of independent steps concurrently.

        Args:
            steps: Steps to execute in parallel.
            state_manager: State manager for tracking execution progress.
            shared_context: Optional shared context available to all steps.

        Returns:
            List of StepResult objects for all executed steps.
        """
        if not steps:
            return []

        shared_context = shared_context or {}

        tasks = [self._execute_one(step, state_manager, shared_context) for step in steps]

        results = await asyncio.gather(*tasks, return_exceptions=False)
        return list(results)

    async def _execute_one(
        self,
        step: ExecutionStep,
        state_manager: ExecutionStateManager,
        context: dict[str, Any],
    ) -> StepResult:
        """Execute a single step with concurrency control.

        Args:
            step: The step to execute.
            state_manager: State manager for tracking.
            context: Shared execution context.

        Returns:
            The StepResult from execution.
        """
        async with self._semaphore:
            await state_manager.mark_step_running(step.step_id)

            result = await self._execute_with_retry(step, context, state_manager)

            if result.state == StepState.COMPLETED:
                await state_manager.mark_step_completed(
                    step.step_id,
                    output=result.output,
                    latency_ms=result.latency_ms,
                )
            else:
                await state_manager.mark_step_failed(
                    step.step_id,
                    error=result.error or "Unknown error",
                    latency_ms=result.latency_ms,
                )

            return result

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
