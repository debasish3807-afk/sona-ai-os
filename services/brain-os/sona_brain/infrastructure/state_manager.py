"""Execution state manager for Brain OS.

Tracks the lifecycle state of an execution plan, managing per-step
state transitions and providing query methods for execution progress.
Thread-safe via asyncio.Lock.
"""

import asyncio
from datetime import UTC, datetime

import structlog

from sona_brain.domain.execution import ExecutionContext, ExecutionState, StepResult, StepState
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep

logger = structlog.get_logger()


class ExecutionStateManager:
    """Manages the lifecycle state of plan execution.

    Tracks per-step states and overall execution state with
    thread-safe transitions via asyncio.Lock.
    """

    def __init__(self, plan: ExecutionPlan) -> None:
        """Initialize state manager for a given plan.

        Args:
            plan: The execution plan to track state for.
        """
        self._plan = plan
        self._context = ExecutionContext(plan_id=plan.plan_id)
        self._lock = asyncio.Lock()
        self._steps_by_id: dict[str, ExecutionStep] = {s.step_id: s for s in plan.steps}

        # Initialize all steps as PENDING
        for step in plan.steps:
            self._context.step_results[step.step_id] = StepResult(
                step_id=step.step_id,
                state=StepState.PENDING,
            )

    @property
    def context(self) -> ExecutionContext:
        """Return the current execution context."""
        return self._context

    @property
    def plan(self) -> ExecutionPlan:
        """Return the underlying plan."""
        return self._plan

    async def start_execution(self) -> None:
        """Transition execution to RUNNING state."""
        async with self._lock:
            self._context.state = ExecutionState.RUNNING
            logger.info("execution_started", plan_id=self._plan.plan_id)

    async def mark_step_running(self, step_id: str) -> None:
        """Mark a step as currently running.

        Args:
            step_id: Identifier of the step to mark.
        """
        async with self._lock:
            result = self._context.step_results[step_id]
            result.state = StepState.RUNNING
            result.started_at = datetime.now(UTC)
            logger.debug("step_running", plan_id=self._plan.plan_id, step_id=step_id)

    async def mark_step_completed(
        self,
        step_id: str,
        output: object = None,
        latency_ms: float = 0.0,
    ) -> None:
        """Mark a step as completed with its output.

        Args:
            step_id: Identifier of the step that completed.
            output: Output data from the step execution.
            latency_ms: Execution latency in milliseconds.
        """
        async with self._lock:
            result = self._context.step_results[step_id]
            result.state = StepState.COMPLETED
            result.output = output
            result.latency_ms = latency_ms
            result.completed_at = datetime.now(UTC)
            logger.info(
                "step_completed",
                plan_id=self._plan.plan_id,
                step_id=step_id,
                latency_ms=latency_ms,
            )

    async def mark_step_failed(
        self,
        step_id: str,
        error: str,
        latency_ms: float = 0.0,
    ) -> None:
        """Mark a step as failed with an error message.

        Args:
            step_id: Identifier of the failed step.
            error: Error description.
            latency_ms: Execution latency before failure.
        """
        async with self._lock:
            result = self._context.step_results[step_id]
            result.state = StepState.FAILED
            result.error = error
            result.latency_ms = latency_ms
            result.completed_at = datetime.now(UTC)
            self._context.errors.append(f"Step {step_id}: {error}")
            logger.warning(
                "step_failed",
                plan_id=self._plan.plan_id,
                step_id=step_id,
                error=error,
            )

    async def mark_step_retrying(self, step_id: str) -> None:
        """Mark a step as retrying.

        Args:
            step_id: Identifier of the step being retried.
        """
        async with self._lock:
            result = self._context.step_results[step_id]
            result.state = StepState.RETRYING
            result.retry_count += 1
            logger.info(
                "step_retrying",
                plan_id=self._plan.plan_id,
                step_id=step_id,
                retry_count=result.retry_count,
            )

    async def mark_step_skipped(self, step_id: str) -> None:
        """Mark a step as skipped.

        Args:
            step_id: Identifier of the step to skip.
        """
        async with self._lock:
            result = self._context.step_results[step_id]
            result.state = StepState.SKIPPED
            result.completed_at = datetime.now(UTC)

    async def mark_step_cancelled(self, step_id: str) -> None:
        """Mark a step as cancelled.

        Args:
            step_id: Identifier of the step to cancel.
        """
        async with self._lock:
            result = self._context.step_results[step_id]
            result.state = StepState.CANCELLED
            result.completed_at = datetime.now(UTC)

    async def complete_execution(self, final_output: str = "") -> None:
        """Transition execution to COMPLETED state.

        Args:
            final_output: The aggregated final output content.
        """
        async with self._lock:
            self._context.state = ExecutionState.COMPLETED
            self._context.final_output = final_output
            self._context.completed_at = datetime.now(UTC)
            logger.info("execution_completed", plan_id=self._plan.plan_id)

    async def fail_execution(self, error: str) -> None:
        """Transition execution to FAILED state.

        Args:
            error: Error description for the overall failure.
        """
        async with self._lock:
            self._context.state = ExecutionState.FAILED
            self._context.errors.append(error)
            self._context.completed_at = datetime.now(UTC)
            logger.error("execution_failed", plan_id=self._plan.plan_id, error=error)

    async def mark_replanning(self) -> None:
        """Transition execution to REPLANNING state."""
        async with self._lock:
            self._context.state = ExecutionState.REPLANNING
            logger.info("execution_replanning", plan_id=self._plan.plan_id)

    def get_ready_steps(self) -> list[ExecutionStep]:
        """Return steps whose dependencies are all completed.

        Returns:
            List of ExecutionStep objects ready to execute.
        """
        ready: list[ExecutionStep] = []
        for step in self._plan.steps:
            result = self._context.step_results[step.step_id]
            if result.state != StepState.PENDING:
                continue
            # Check all dependencies are completed
            deps_met = all(
                self._context.step_results[dep_id].state == StepState.COMPLETED
                for dep_id in step.depends_on
                if dep_id in self._context.step_results
            )
            if deps_met:
                ready.append(step)
        return ready

    def get_step_result(self, step_id: str) -> StepResult | None:
        """Get the result for a specific step.

        Args:
            step_id: Identifier of the step.

        Returns:
            The StepResult if found, None otherwise.
        """
        return self._context.step_results.get(step_id)

    def is_complete(self) -> bool:
        """Check if all steps have finished (completed, failed, skipped, or cancelled).

        Returns:
            True if no steps are pending or running.
        """
        terminal_states = {
            StepState.COMPLETED,
            StepState.FAILED,
            StepState.SKIPPED,
            StepState.CANCELLED,
        }
        return all(
            r.state in terminal_states for r in self._context.step_results.values()
        )

    def get_completed_count(self) -> int:
        """Return the number of successfully completed steps.

        Returns:
            Count of steps in COMPLETED state.
        """
        return sum(
            1
            for r in self._context.step_results.values()
            if r.state == StepState.COMPLETED
        )

    def get_failed_count(self) -> int:
        """Return the number of failed steps.

        Returns:
            Count of steps in FAILED state.
        """
        return sum(
            1
            for r in self._context.step_results.values()
            if r.state == StepState.FAILED
        )

    def all_deps_completed(self, step_id: str) -> bool:
        """Check if all dependencies for a step are completed.

        Args:
            step_id: Identifier of the step to check.

        Returns:
            True if all dependencies are in COMPLETED state.
        """
        step = self._steps_by_id.get(step_id)
        if step is None:
            return False
        return all(
            self._context.step_results.get(dep_id, StepResult(step_id=dep_id, state=StepState.PENDING)).state
            == StepState.COMPLETED
            for dep_id in step.depends_on
        )
