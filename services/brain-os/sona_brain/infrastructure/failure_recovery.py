"""Failure recovery for Brain OS.

Handles various failure modes during execution, including provider failures,
model failures, retry exhaustion, and unrecoverable errors.
"""

from enum import StrEnum

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.domain.models import BrainResponse
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStepType

logger = structlog.get_logger()


class FailureType(StrEnum):
    """Classification of failure types."""

    PROVIDER_FAILURE = "provider_failure"
    MODEL_FAILURE = "model_failure"
    TIMEOUT_FAILURE = "timeout_failure"
    RETRIES_EXHAUSTED = "retries_exhausted"
    UNRECOVERABLE = "unrecoverable"
    PARTIAL_FAILURE = "partial_failure"


class RecoveryAction(StrEnum):
    """Actions the failure recovery system can recommend."""

    RETRY_DIFFERENT_PROVIDER = "retry_different_provider"
    RETRY_DIFFERENT_MODEL = "retry_different_model"
    USE_PARTIAL_RESULTS = "use_partial_results"
    FAIL_WITH_ERROR = "fail_with_error"
    REPLAN = "replan"


class FailureRecovery:
    """Handles execution failure recovery decisions.

    Classifies failures, determines recovery strategies, and produces
    error responses when recovery is not possible.
    """

    def classify_failure(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> FailureType:
        """Classify the type of failure from step results.

        Args:
            results: Step results from execution.
            plan: The execution plan.

        Returns:
            The classified FailureType.
        """
        failed_results = [r for r in results if r.state == StepState.FAILED]

        if not failed_results:
            return FailureType.PARTIAL_FAILURE

        # Check for timeout failures
        timeout_failures = [r for r in failed_results if r.error and "timed out" in r.error.lower()]
        if timeout_failures:
            return FailureType.TIMEOUT_FAILURE

        # Check for provider-related failures
        provider_errors = [
            r
            for r in failed_results
            if r.error
            and any(
                kw in r.error.lower()
                for kw in ["provider", "connection", "unavailable", "503", "502"]
            )
        ]
        if provider_errors:
            return FailureType.PROVIDER_FAILURE

        # Check for model-specific failures
        model_errors = [
            r
            for r in failed_results
            if r.error
            and any(
                kw in r.error.lower()
                for kw in ["model", "capacity", "overloaded", "rate limit", "429"]
            )
        ]
        if model_errors:
            return FailureType.MODEL_FAILURE

        # Check for retry exhaustion
        retry_exhausted = [r for r in failed_results if r.retry_count > 0]
        if retry_exhausted:
            return FailureType.RETRIES_EXHAUSTED

        return FailureType.UNRECOVERABLE

    def recommend_action(
        self,
        failure_type: FailureType,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> RecoveryAction:
        """Recommend a recovery action based on failure classification.

        Args:
            failure_type: The classified failure type.
            results: Step results from execution.
            plan: The execution plan.

        Returns:
            Recommended RecoveryAction.
        """
        match failure_type:
            case FailureType.PROVIDER_FAILURE:
                return RecoveryAction.RETRY_DIFFERENT_PROVIDER
            case FailureType.MODEL_FAILURE:
                return RecoveryAction.RETRY_DIFFERENT_MODEL
            case FailureType.TIMEOUT_FAILURE:
                if self._has_usable_partial_results(results, plan):
                    return RecoveryAction.USE_PARTIAL_RESULTS
                return RecoveryAction.REPLAN
            case FailureType.RETRIES_EXHAUSTED:
                if self._has_usable_partial_results(results, plan):
                    return RecoveryAction.USE_PARTIAL_RESULTS
                return RecoveryAction.REPLAN
            case FailureType.PARTIAL_FAILURE:
                return RecoveryAction.USE_PARTIAL_RESULTS
            case FailureType.UNRECOVERABLE:
                return RecoveryAction.FAIL_WITH_ERROR
            case _:
                return RecoveryAction.FAIL_WITH_ERROR

    def create_error_response(
        self,
        plan: ExecutionPlan,
        results: list[StepResult],
        session_id: str,
        failure_type: FailureType,
    ) -> BrainResponse:
        """Create an error response with partial results when possible.

        Args:
            plan: The execution plan that failed.
            results: Step results.
            session_id: Session identifier.
            failure_type: The classified failure.

        Returns:
            A BrainResponse with error information.
        """
        # Try to extract any partial content
        partial_content = self._extract_partial_content(results, plan)

        # Build error message
        failed_results = [r for r in results if r.state == StepState.FAILED]
        error_msgs = [r.error or "Unknown error" for r in failed_results[:3]]
        error_summary = "; ".join(error_msgs)

        content = (
            partial_content
            if partial_content
            else (f"I encountered an error processing your request: {error_summary}")
        )

        total_latency = sum(r.latency_ms for r in results)

        logger.error(
            "failure_response_created",
            plan_id=plan.plan_id,
            failure_type=failure_type,
            has_partial=bool(partial_content),
        )

        return BrainResponse(
            content=content,
            session_id=session_id,
            model_used=plan.model_id,
            tokens={"input": 0, "output": 0},
            latency_ms=total_latency,
            agent_used=None,
            memory_updated=False,
        )

    def _has_usable_partial_results(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> bool:
        """Check if partial results contain usable LLM output.

        Args:
            results: Step results.
            plan: Execution plan.

        Returns:
            True if there's at least one completed LLM step.
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}
        return any(
            r.state == StepState.COMPLETED
            and step_types.get(r.step_id) == ExecutionStepType.LLM_CALL
            for r in results
        )

    def _extract_partial_content(
        self,
        results: list[StepResult],
        plan: ExecutionPlan,
    ) -> str:
        """Extract content from any completed LLM steps.

        Args:
            results: Step results.
            plan: Execution plan.

        Returns:
            Extracted content string, or empty if none available.
        """
        step_types = {s.step_id: s.step_type for s in plan.steps}

        for result in results:
            if (
                result.state == StepState.COMPLETED
                and step_types.get(result.step_id) == ExecutionStepType.LLM_CALL
                and isinstance(result.output, dict)
            ):
                content = result.output.get("content", "")
                if content:
                    return str(content)

        return ""
