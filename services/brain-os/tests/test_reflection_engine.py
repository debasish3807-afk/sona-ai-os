"""Tests for reflection engine.

Tests verify quality evaluation, retry decisions, and reflection limits.
"""

import pytest

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.domain.models import BrainResponse
from sona_brain.infrastructure.reflection_engine import (
    ReflectionConfig,
    ReflectionDecision,
    ReflectionEngine,
)
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


def _make_response(content: str = "A valid response") -> BrainResponse:
    """Create a test response."""
    return BrainResponse(
        content=content,
        session_id="s1",
        model_used="gpt-4o",
        tokens={"input": 10, "output": 5},
        latency_ms=100.0,
    )


def _make_plan(confidence: float = 0.9) -> ExecutionPlan:
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
        confidence=confidence,
    )


def _make_results(state: StepState = StepState.COMPLETED) -> list[StepResult]:
    """Create test results."""
    return [StepResult(step_id="s1", state=state)]


class TestReflectionEngine:
    """Tests for ReflectionEngine."""

    def test_accept_good_response(self) -> None:
        """Accept a response that meets all quality criteria."""
        engine = ReflectionEngine()
        response = _make_response("This is a good response with enough content")
        plan = _make_plan(confidence=0.9)
        results = _make_results(StepState.COMPLETED)

        decision = engine.evaluate(response, plan, results)
        assert decision == ReflectionDecision.ACCEPT

    def test_reject_short_response(self) -> None:
        """Reject a response that is too short."""
        engine = ReflectionEngine(ReflectionConfig(min_content_length=20))
        response = _make_response("Short")
        plan = _make_plan(confidence=0.9)
        results = _make_results()

        decision = engine.evaluate(response, plan, results)
        assert decision != ReflectionDecision.ACCEPT

    def test_reject_empty_response(self) -> None:
        """Reject an empty response."""
        engine = ReflectionEngine()
        response = _make_response("")
        plan = _make_plan(confidence=0.9)
        results = _make_results()

        decision = engine.evaluate(response, plan, results)
        assert decision != ReflectionDecision.ACCEPT

    def test_reject_low_confidence(self) -> None:
        """Reject response with low plan confidence."""
        engine = ReflectionEngine(ReflectionConfig(confidence_threshold=0.8))
        response = _make_response("Good content here")
        plan = _make_plan(confidence=0.3)
        results = _make_results()

        decision = engine.evaluate(response, plan, results)
        assert decision != ReflectionDecision.ACCEPT

    def test_first_retry_uses_higher_temp(self) -> None:
        """First reflection retry recommends higher temperature."""
        engine = ReflectionEngine(ReflectionConfig(min_content_length=100))
        response = _make_response("Too short")
        plan = _make_plan()
        results = _make_results()

        decision = engine.evaluate(response, plan, results)
        assert decision == ReflectionDecision.RETRY_WITH_HIGHER_TEMP

    def test_second_retry_uses_different_model(self) -> None:
        """Second reflection retry recommends different model."""
        engine = ReflectionEngine(ReflectionConfig(min_content_length=100))
        response = _make_response("Too short")
        plan = _make_plan()
        results = _make_results()

        # First evaluation
        engine.evaluate(response, plan, results)
        # Second evaluation
        decision = engine.evaluate(response, plan, results)
        assert decision == ReflectionDecision.RETRY_WITH_DIFFERENT_MODEL

    def test_max_reflections_forces_accept(self) -> None:
        """After max reflections, always accept."""
        engine = ReflectionEngine(ReflectionConfig(min_content_length=100, max_reflection_rounds=2))
        response = _make_response("Short")
        plan = _make_plan()
        results = _make_results()

        # Exhaust reflections
        engine.evaluate(response, plan, results)
        engine.evaluate(response, plan, results)
        # Third time should accept
        decision = engine.evaluate(response, plan, results)
        assert decision == ReflectionDecision.ACCEPT

    def test_reflection_count_tracked(self) -> None:
        """Reflection count increments on non-accept decisions."""
        engine = ReflectionEngine(ReflectionConfig(min_content_length=100))
        response = _make_response("Short")
        plan = _make_plan()
        results = _make_results()

        assert engine.reflection_count == 0
        engine.evaluate(response, plan, results)
        assert engine.reflection_count == 1

    def test_reset(self) -> None:
        """Reset clears reflection count."""
        engine = ReflectionEngine(ReflectionConfig(min_content_length=100))
        response = _make_response("Short")
        plan = _make_plan()
        results = _make_results()

        engine.evaluate(response, plan, results)
        engine.reset()
        assert engine.reflection_count == 0

    def test_high_failure_ratio_triggers_different_model(self) -> None:
        """High step failure ratio recommends different model."""
        engine = ReflectionEngine()
        response = _make_response("x" * 20)
        plan = _make_plan(confidence=0.9)
        # More than half failed
        results = [
            StepResult(step_id="s1", state=StepState.FAILED),
            StepResult(step_id="s2", state=StepState.FAILED),
            StepResult(step_id="s3", state=StepState.COMPLETED),
        ]

        decision = engine.evaluate(response, plan, results)
        assert decision in (
            ReflectionDecision.RETRY_WITH_HIGHER_TEMP,
            ReflectionDecision.RETRY_WITH_DIFFERENT_MODEL,
        )

    def test_get_adjusted_temperature(self) -> None:
        """Temperature adjustment applies increase."""
        engine = ReflectionEngine(ReflectionConfig(temperature_increase=0.3))
        assert engine.get_adjusted_temperature(0.7) == pytest.approx(1.0)

    def test_temperature_capped_at_2(self) -> None:
        """Temperature cannot exceed 2.0."""
        engine = ReflectionEngine(ReflectionConfig(temperature_increase=0.5))
        assert engine.get_adjusted_temperature(1.8) == 2.0
