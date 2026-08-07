"""Tests for failure recovery.

Tests verify failure classification, recovery recommendations, and error responses.
"""

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.infrastructure.failure_recovery import (
    FailureRecovery,
    FailureType,
    RecoveryAction,
)
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


def _make_plan() -> ExecutionPlan:
    """Create a test plan."""
    return ExecutionPlan(
        plan_id="test-plan",
        intent="test",
        steps=[
            ExecutionStep(
                step_id="s1",
                step_type=ExecutionStepType.LLM_CALL,
                target="model",
            )
        ],
        model_id="gpt-4o",
        provider="openai",
    )


def _make_plan_with_llm_result() -> ExecutionPlan:
    """Create plan with LLM step for partial result tests."""
    return ExecutionPlan(
        plan_id="test-plan",
        intent="test",
        steps=[
            ExecutionStep(step_id="llm-1", step_type=ExecutionStepType.LLM_CALL, target="m"),
            ExecutionStep(step_id="tool-1", step_type=ExecutionStepType.TOOL_CALL, target="t"),
        ],
        model_id="gpt-4o",
        provider="openai",
    )


class TestFailureRecovery:
    """Tests for FailureRecovery."""

    def test_classify_timeout_failure(self) -> None:
        """Classify timeout errors correctly."""
        recovery = FailureRecovery()
        results = [
            StepResult(step_id="s1", state=StepState.FAILED, error="Step timed out after 30s"),
        ]
        plan = _make_plan()

        failure_type = recovery.classify_failure(results, plan)
        assert failure_type == FailureType.TIMEOUT_FAILURE

    def test_classify_provider_failure(self) -> None:
        """Classify provider connection errors."""
        recovery = FailureRecovery()
        results = [
            StepResult(step_id="s1", state=StepState.FAILED, error="Provider unavailable: 503"),
        ]
        plan = _make_plan()

        failure_type = recovery.classify_failure(results, plan)
        assert failure_type == FailureType.PROVIDER_FAILURE

    def test_classify_model_failure(self) -> None:
        """Classify model-specific errors."""
        recovery = FailureRecovery()
        results = [
            StepResult(
                step_id="s1", state=StepState.FAILED, error="Model rate limit exceeded: 429"
            ),
        ]
        plan = _make_plan()

        failure_type = recovery.classify_failure(results, plan)
        assert failure_type == FailureType.MODEL_FAILURE

    def test_classify_retries_exhausted(self) -> None:
        """Classify retry exhaustion."""
        recovery = FailureRecovery()
        results = [
            StepResult(step_id="s1", state=StepState.FAILED, error="Generic error", retry_count=3),
        ]
        plan = _make_plan()

        failure_type = recovery.classify_failure(results, plan)
        assert failure_type == FailureType.RETRIES_EXHAUSTED

    def test_classify_unrecoverable(self) -> None:
        """Classify unknown errors as unrecoverable."""
        recovery = FailureRecovery()
        results = [
            StepResult(step_id="s1", state=StepState.FAILED, error="Something broke"),
        ]
        plan = _make_plan()

        failure_type = recovery.classify_failure(results, plan)
        assert failure_type == FailureType.UNRECOVERABLE

    def test_recommend_retry_provider(self) -> None:
        """Provider failure recommends retry with different provider."""
        recovery = FailureRecovery()
        plan = _make_plan()
        results = [StepResult(step_id="s1", state=StepState.FAILED)]

        action = recovery.recommend_action(FailureType.PROVIDER_FAILURE, results, plan)
        assert action == RecoveryAction.RETRY_DIFFERENT_PROVIDER

    def test_recommend_retry_model(self) -> None:
        """Model failure recommends retry with different model."""
        recovery = FailureRecovery()
        plan = _make_plan()
        results = [StepResult(step_id="s1", state=StepState.FAILED)]

        action = recovery.recommend_action(FailureType.MODEL_FAILURE, results, plan)
        assert action == RecoveryAction.RETRY_DIFFERENT_MODEL

    def test_recommend_fail_unrecoverable(self) -> None:
        """Unrecoverable failure recommends fail with error."""
        recovery = FailureRecovery()
        plan = _make_plan()
        results = [StepResult(step_id="s1", state=StepState.FAILED)]

        action = recovery.recommend_action(FailureType.UNRECOVERABLE, results, plan)
        assert action == RecoveryAction.FAIL_WITH_ERROR

    def test_recommend_partial_results_on_timeout(self) -> None:
        """Timeout with partial LLM results recommends using them."""
        recovery = FailureRecovery()
        plan = _make_plan_with_llm_result()
        results = [
            StepResult(step_id="llm-1", state=StepState.COMPLETED, output={"content": "data"}),
            StepResult(step_id="tool-1", state=StepState.FAILED, error="timed out"),
        ]

        action = recovery.recommend_action(FailureType.TIMEOUT_FAILURE, results, plan)
        assert action == RecoveryAction.USE_PARTIAL_RESULTS

    def test_create_error_response(self) -> None:
        """Create error response with failure info."""
        recovery = FailureRecovery()
        plan = _make_plan()
        results = [
            StepResult(step_id="s1", state=StepState.FAILED, error="Timeout exceeded"),
        ]

        response = recovery.create_error_response(
            plan, results, "session-1", FailureType.TIMEOUT_FAILURE
        )
        assert response.session_id == "session-1"
        assert "error" in response.content.lower() or "timeout" in response.content.lower()
        assert response.model_used == "gpt-4o"

    def test_create_error_response_with_partial_content(self) -> None:
        """Error response uses partial content when available."""
        recovery = FailureRecovery()
        plan = _make_plan_with_llm_result()
        results = [
            StepResult(
                step_id="llm-1",
                state=StepState.COMPLETED,
                output={"content": "Partial answer here"},
            ),
            StepResult(step_id="tool-1", state=StepState.FAILED, error="Error"),
        ]

        response = recovery.create_error_response(plan, results, "s1", FailureType.PARTIAL_FAILURE)
        assert response.content == "Partial answer here"

    def test_classify_no_failures(self) -> None:
        """No failures classifies as partial failure."""
        recovery = FailureRecovery()
        results = [StepResult(step_id="s1", state=StepState.COMPLETED)]
        plan = _make_plan()

        failure_type = recovery.classify_failure(results, plan)
        assert failure_type == FailureType.PARTIAL_FAILURE
