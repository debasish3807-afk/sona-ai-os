"""Reflection engine for Brain OS.

Provides post-execution quality assessment, determining whether output
quality meets confidence thresholds and recommending retry strategies.
"""

from enum import StrEnum

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.domain.models import BrainResponse
from sona_thalamus.domain.execution_plan import ExecutionPlan

logger = structlog.get_logger()


class ReflectionDecision(StrEnum):
    """Decisions the reflection engine can make."""

    ACCEPT = "accept"
    RETRY_WITH_HIGHER_TEMP = "retry_with_higher_temp"
    RETRY_WITH_DIFFERENT_MODEL = "retry_with_different_model"


class ReflectionConfig:
    """Configuration for the reflection engine.

    Attributes:
        min_content_length: Minimum acceptable response content length.
        confidence_threshold: Minimum confidence score to accept.
        max_reflection_rounds: Maximum reflection iterations to prevent loops.
        temperature_increase: How much to increase temperature on retry.
    """

    def __init__(
        self,
        min_content_length: int = 10,
        confidence_threshold: float = 0.5,
        max_reflection_rounds: int = 2,
        temperature_increase: float = 0.2,
    ) -> None:
        """Initialize reflection configuration.

        Args:
            min_content_length: Minimum response content length to accept.
            confidence_threshold: Minimum plan confidence to accept.
            max_reflection_rounds: Maximum retry iterations.
            temperature_increase: Temperature bump per retry.
        """
        self.min_content_length = min_content_length
        self.confidence_threshold = confidence_threshold
        self.max_reflection_rounds = max_reflection_rounds
        self.temperature_increase = temperature_increase


class ReflectionEngine:
    """Post-execution quality assessment engine.

    Evaluates whether the generated output meets quality thresholds
    and recommends retry strategies when quality is insufficient.
    """

    def __init__(self, config: ReflectionConfig | None = None) -> None:
        """Initialize reflection engine with configuration.

        Args:
            config: Reflection configuration. Uses defaults if None.
        """
        self._config = config or ReflectionConfig()
        self._reflection_count = 0

    @property
    def config(self) -> ReflectionConfig:
        """Return the reflection configuration."""
        return self._config

    @property
    def reflection_count(self) -> int:
        """Return the number of reflection rounds performed."""
        return self._reflection_count

    def evaluate(
        self,
        response: BrainResponse,
        plan: ExecutionPlan,
        step_results: list[StepResult],
    ) -> ReflectionDecision:
        """Evaluate output quality and decide whether to accept or retry.

        Args:
            response: The generated BrainResponse to evaluate.
            plan: The execution plan that produced this response.
            step_results: All step results from execution.

        Returns:
            A ReflectionDecision indicating accept or retry strategy.
        """
        # Check if max reflections exceeded
        if self._reflection_count >= self._config.max_reflection_rounds:
            logger.info(
                "reflection_limit_reached",
                count=self._reflection_count,
                max=self._config.max_reflection_rounds,
            )
            return ReflectionDecision.ACCEPT

        # Evaluate quality criteria
        issues: list[str] = []

        if len(response.content) < self._config.min_content_length:
            issues.append(
                f"Content too short: {len(response.content)} < {self._config.min_content_length}"
            )

        if plan.confidence < self._config.confidence_threshold:
            issues.append(
                f"Low confidence: {plan.confidence} < {self._config.confidence_threshold}"
            )

        # Check for empty or error-like responses
        if not response.content.strip():
            issues.append("Empty response content")

        # Check step failure ratio
        failed_count = sum(1 for r in step_results if r.state == StepState.FAILED)
        total_count = len(step_results)
        if total_count > 0 and failed_count / total_count > 0.5:
            issues.append(f"High failure ratio: {failed_count}/{total_count}")

        if not issues:
            logger.info("reflection_accepted", plan_id=plan.plan_id)
            return ReflectionDecision.ACCEPT

        self._reflection_count += 1
        decision = self._select_retry_strategy(issues, plan)

        logger.info(
            "reflection_retry",
            plan_id=plan.plan_id,
            issues=issues,
            decision=decision,
            round=self._reflection_count,
        )

        return decision

    def _select_retry_strategy(
        self,
        issues: list[str],
        plan: ExecutionPlan,
    ) -> ReflectionDecision:
        """Select the best retry strategy based on identified issues.

        Args:
            issues: List of quality issues found.
            plan: The execution plan.

        Returns:
            The recommended retry decision.
        """
        # If content is too short, try higher temperature first
        if any("Content too short" in i for i in issues):
            if self._reflection_count == 1:
                return ReflectionDecision.RETRY_WITH_HIGHER_TEMP
            return ReflectionDecision.RETRY_WITH_DIFFERENT_MODEL

        # If high failure ratio, try different model
        if any("High failure ratio" in i for i in issues):
            return ReflectionDecision.RETRY_WITH_DIFFERENT_MODEL

        # Default: try higher temperature first round, different model second
        if self._reflection_count == 1:
            return ReflectionDecision.RETRY_WITH_HIGHER_TEMP
        return ReflectionDecision.RETRY_WITH_DIFFERENT_MODEL

    def reset(self) -> None:
        """Reset reflection count for a new execution."""
        self._reflection_count = 0

    def get_adjusted_temperature(self, current_temp: float) -> float:
        """Calculate adjusted temperature for retry.

        Args:
            current_temp: Current temperature setting.

        Returns:
            New temperature clamped to [0.0, 2.0].
        """
        new_temp = current_temp + self._config.temperature_increase
        return min(new_temp, 2.0)
