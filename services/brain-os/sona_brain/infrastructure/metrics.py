"""Execution metrics for Brain OS.

Tracks per-plan latency, token usage, step counts, success/failure rates,
and provider utilization for observability.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStepType

from sona_brain.domain.execution import StepResult, StepState

logger = structlog.get_logger()


@dataclass
class PlanMetrics:
    """Metrics for a single plan execution.

    Attributes:
        plan_id: Plan identifier.
        total_latency_ms: Total execution time.
        tokens_in: Total input tokens used.
        tokens_out: Total output tokens generated.
        steps_total: Total number of steps.
        steps_completed: Number of completed steps.
        steps_failed: Number of failed steps.
        model_used: Primary model used.
        provider_used: Provider used.
        success: Whether the execution succeeded.
        recorded_at: When this metric was recorded.
    """

    plan_id: str
    total_latency_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    steps_total: int = 0
    steps_completed: int = 0
    steps_failed: int = 0
    model_used: str = ""
    provider_used: str = ""
    success: bool = False
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ExecutionMetrics:
    """Tracks execution metrics across multiple plan executions.

    Provides aggregate statistics for latency, token usage, success rates,
    and provider utilization.
    """

    def __init__(self) -> None:
        """Initialize metrics tracker."""
        self._plan_metrics: list[PlanMetrics] = []
        self._provider_usage: dict[str, int] = {}
        self._model_usage: dict[str, int] = {}

    @property
    def plan_count(self) -> int:
        """Return total number of tracked plan executions."""
        return len(self._plan_metrics)

    def record_execution(
        self,
        plan: ExecutionPlan,
        results: list[StepResult],
        success: bool,
    ) -> PlanMetrics:
        """Record metrics for a completed plan execution.

        Args:
            plan: The execution plan.
            results: All step results.
            success: Whether execution succeeded.

        Returns:
            The recorded PlanMetrics.
        """
        total_latency = sum(r.latency_ms for r in results)
        tokens_in, tokens_out = self._count_tokens(results, plan)
        steps_completed = sum(1 for r in results if r.state == StepState.COMPLETED)
        steps_failed = sum(1 for r in results if r.state == StepState.FAILED)

        metrics = PlanMetrics(
            plan_id=plan.plan_id,
            total_latency_ms=total_latency,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            steps_total=len(plan.steps),
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            model_used=plan.model_id,
            provider_used=plan.provider,
            success=success,
        )

        self._plan_metrics.append(metrics)

        # Track provider and model usage
        self._provider_usage[plan.provider] = self._provider_usage.get(plan.provider, 0) + 1
        self._model_usage[plan.model_id] = self._model_usage.get(plan.model_id, 0) + 1

        logger.info(
            "metrics_recorded",
            plan_id=plan.plan_id,
            latency_ms=total_latency,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            success=success,
        )

        return metrics

    def get_average_latency(self) -> float:
        """Calculate average latency across all executions.

        Returns:
            Average latency in milliseconds, or 0.0 if no data.
        """
        if not self._plan_metrics:
            return 0.0
        return sum(m.total_latency_ms for m in self._plan_metrics) / len(self._plan_metrics)

    def get_success_rate(self) -> float:
        """Calculate success rate across all executions.

        Returns:
            Success rate as a ratio (0.0 to 1.0), or 0.0 if no data.
        """
        if not self._plan_metrics:
            return 0.0
        successes = sum(1 for m in self._plan_metrics if m.success)
        return successes / len(self._plan_metrics)

    def get_average_steps_per_plan(self) -> float:
        """Calculate average number of steps per plan.

        Returns:
            Average step count, or 0.0 if no data.
        """
        if not self._plan_metrics:
            return 0.0
        return sum(m.steps_total for m in self._plan_metrics) / len(self._plan_metrics)

    def get_total_tokens(self) -> tuple[int, int]:
        """Get total token usage across all executions.

        Returns:
            Tuple of (total_tokens_in, total_tokens_out).
        """
        total_in = sum(m.tokens_in for m in self._plan_metrics)
        total_out = sum(m.tokens_out for m in self._plan_metrics)
        return total_in, total_out

    def get_provider_utilization(self) -> dict[str, int]:
        """Get provider usage counts.

        Returns:
            Dictionary mapping provider names to execution counts.
        """
        return dict(self._provider_usage)

    def get_model_utilization(self) -> dict[str, int]:
        """Get model usage counts.

        Returns:
            Dictionary mapping model names to execution counts.
        """
        return dict(self._model_usage)

    def get_failure_rate_by_provider(self) -> dict[str, float]:
        """Calculate failure rate per provider.

        Returns:
            Dictionary mapping provider names to failure rates.
        """
        provider_counts: dict[str, list[bool]] = {}
        for m in self._plan_metrics:
            if m.provider_used not in provider_counts:
                provider_counts[m.provider_used] = []
            provider_counts[m.provider_used].append(m.success)

        return {
            provider: 1.0 - (sum(1 for s in results if s) / len(results))
            for provider, results in provider_counts.items()
            if results
        }

    def get_recent_metrics(self, count: int = 10) -> list[PlanMetrics]:
        """Get the most recent plan metrics.

        Args:
            count: Number of recent metrics to return.

        Returns:
            List of recent PlanMetrics.
        """
        return self._plan_metrics[-count:]

    def _count_tokens(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> tuple[int, int]:
        """Count tokens from LLM step results.

        Args:
            results: Step results.
            plan: Execution plan.

        Returns:
            Tuple of (tokens_in, tokens_out).
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}
        total_in = 0
        total_out = 0

        for result in results:
            if (
                result.state == StepState.COMPLETED
                and step_types.get(result.step_id) == ExecutionStepType.LLM_CALL
                and isinstance(result.output, dict)
            ):
                total_in += result.output.get("tokens_in", 0)
                total_out += result.output.get("tokens_out", 0)

        return total_in, total_out
