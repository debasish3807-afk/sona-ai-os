"""Timeout recovery for Brain OS.

Handles timeout scenarios by cancelling timed-out steps gracefully,
determining if partial results are usable, and falling back to simpler
execution strategies.
"""

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType

logger = structlog.get_logger()


class TimeoutRecoveryConfig:
    """Configuration for timeout recovery behavior.

    Attributes:
        partial_result_threshold: Minimum ratio of completed steps to accept partial results.
        fallback_timeout_multiplier: Multiplier for timeout on fallback execution.
    """

    def __init__(
        self,
        partial_result_threshold: float = 0.5,
        fallback_timeout_multiplier: float = 1.5,
    ) -> None:
        """Initialize timeout recovery configuration.

        Args:
            partial_result_threshold: Min completed ratio to accept partial results.
            fallback_timeout_multiplier: Timeout multiplier for fallback steps.
        """
        self.partial_result_threshold = partial_result_threshold
        self.fallback_timeout_multiplier = fallback_timeout_multiplier


class TimeoutRecovery:
    """Handles timeout scenarios during plan execution.

    Determines whether partial results from a timed-out execution are
    usable, and creates simplified fallback plans when needed.
    """

    def __init__(self, config: TimeoutRecoveryConfig | None = None) -> None:
        """Initialize timeout recovery handler.

        Args:
            config: Configuration. Uses defaults if None.
        """
        self._config = config or TimeoutRecoveryConfig()

    @property
    def config(self) -> TimeoutRecoveryConfig:
        """Return the timeout recovery configuration."""
        return self._config

    def has_timed_out_steps(self, results: list[StepResult]) -> bool:
        """Check if any steps timed out.

        Args:
            results: Step results to check.

        Returns:
            True if any step failed with a timeout error.
        """
        return any(
            r.state == StepState.FAILED and r.error and "timed out" in r.error.lower()
            for r in results
        )

    def can_use_partial_results(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> bool:
        """Determine if partial results are sufficient to produce a response.

        Checks if enough steps completed (meeting the threshold) and
        if there's at least one completed LLM step providing content.

        Args:
            results: Step results from execution.
            plan: The execution plan.

        Returns:
            True if partial results are usable.
        """
        if not results:
            return False

        completed_count = sum(1 for r in results if r.state == StepState.COMPLETED)
        total_count = len(plan.steps)

        if total_count == 0:
            return False

        completion_ratio = completed_count / total_count

        # Need to meet threshold AND have at least one LLM result
        has_llm_result = self._has_completed_llm_step(results, plan)

        meets_threshold = completion_ratio >= self._config.partial_result_threshold

        logger.info(
            "partial_result_check",
            completed=completed_count,
            total=total_count,
            ratio=completion_ratio,
            threshold=self._config.partial_result_threshold,
            has_llm=has_llm_result,
            usable=meets_threshold and has_llm_result,
        )

        return meets_threshold and has_llm_result

    def get_timed_out_steps(self, results: list[StepResult]) -> list[StepResult]:
        """Get all steps that timed out.

        Args:
            results: Step results to filter.

        Returns:
            List of timed-out step results.
        """
        return [
            r
            for r in results
            if r.state == StepState.FAILED and r.error and "timed out" in r.error.lower()
        ]

    def create_fallback_plan(
        self,
        plan: ExecutionPlan,
        timed_out_steps: list[StepResult],
    ) -> ExecutionPlan | None:
        """Create a simplified fallback plan excluding timed-out steps.

        Increases timeouts for remaining steps and removes dependencies
        on timed-out steps.

        Args:
            plan: Original plan that had timeouts.
            timed_out_steps: Steps that timed out.

        Returns:
            New plan without timed-out steps, or None if not possible.
        """
        timed_out_ids = {r.step_id for r in timed_out_steps}

        # Keep only steps that didn't time out
        remaining_steps: list[ExecutionStep] = []
        for step in plan.steps:
            if step.step_id in timed_out_ids:
                continue

            # Remove dependencies on timed-out steps
            new_depends = [d for d in step.depends_on if d not in timed_out_ids]

            # Increase timeout for remaining steps
            new_timeout = step.timeout_seconds * self._config.fallback_timeout_multiplier

            new_step = ExecutionStep(
                step_id=step.step_id,
                step_type=step.step_type,
                target=step.target,
                params=step.params,
                depends_on=new_depends,
                timeout_seconds=new_timeout,
                retryable=step.retryable,
                priority=step.priority,
            )
            remaining_steps.append(new_step)

        if not remaining_steps:
            return None

        # Ensure at least one LLM step remains
        has_llm = any(s.step_type == ExecutionStepType.LLM_CALL for s in remaining_steps)
        if not has_llm:
            return None

        return ExecutionPlan(
            plan_id=f"timeout-fallback-{plan.plan_id[:8]}",
            intent=plan.intent,
            steps=remaining_steps,
            model_id=plan.model_id,
            provider=plan.provider,
            context=plan.context,
            confidence=plan.confidence * 0.8,  # Reduce confidence for fallback
            estimated_latency_ms=int(
                plan.estimated_latency_ms * self._config.fallback_timeout_multiplier
            ),
            requires_streaming=plan.requires_streaming,
            fallback_plan_id=plan.plan_id,
        )

    def _has_completed_llm_step(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> bool:
        """Check if there's at least one completed LLM step.

        Args:
            results: Step results.
            plan: Execution plan.

        Returns:
            True if a completed LLM step exists.
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}
        return any(
            r.state == StepState.COMPLETED
            and step_types.get(r.step_id) == ExecutionStepType.LLM_CALL
            for r in results
        )
