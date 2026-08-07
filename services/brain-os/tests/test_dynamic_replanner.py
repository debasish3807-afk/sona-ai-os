"""Tests for dynamic replanner.

Tests verify plan modification on failure, model substitution, and simplification.
"""

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.infrastructure.dynamic_replanner import DynamicReplanner
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


def _make_plan(steps: list[ExecutionStep], model: str = "gpt-4o") -> ExecutionPlan:
    """Create a test plan."""
    return ExecutionPlan(
        plan_id="original-plan",
        intent="test",
        steps=steps,
        model_id=model,
        provider="openai",
        confidence=0.9,
    )


def _llm_step(step_id: str = "llm-1", depends_on: list[str] | None = None) -> ExecutionStep:
    """Create an LLM step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.LLM_CALL,
        target="gpt-4o",
        depends_on=depends_on or [],
    )


def _tool_step(step_id: str = "tool-1", depends_on: list[str] | None = None) -> ExecutionStep:
    """Create a tool step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.TOOL_CALL,
        target="web_search",
        depends_on=depends_on or [],
    )


class TestDynamicReplanner:
    """Tests for DynamicReplanner."""

    def test_no_failures_returns_none(self) -> None:
        """No failures means no replan needed."""
        replanner = DynamicReplanner()
        plan = _make_plan([_llm_step()])
        results = [StepResult(step_id="llm-1", state=StepState.COMPLETED)]

        new_plan = replanner.replan(plan, results)
        assert new_plan is None

    def test_remove_failed_tool_step(self) -> None:
        """Remove a failed non-LLM step."""
        replanner = DynamicReplanner()
        plan = _make_plan([_tool_step("tool-1"), _llm_step("llm-1", depends_on=["tool-1"])])
        results = [
            StepResult(step_id="tool-1", state=StepState.FAILED, error="Tool error"),
            StepResult(step_id="llm-1", state=StepState.COMPLETED),
        ]

        new_plan = replanner.replan(plan, results)
        assert new_plan is not None
        assert new_plan.plan_id.startswith("replan-")
        # Tool step removed, LLM remains
        step_ids = [s.step_id for s in new_plan.steps]
        assert "tool-1" not in step_ids
        assert "llm-1" in step_ids

    def test_removes_dependency_on_removed_step(self) -> None:
        """Dependencies on removed steps are cleaned up."""
        replanner = DynamicReplanner()
        plan = _make_plan([_tool_step("tool-1"), _llm_step("llm-1", depends_on=["tool-1"])])
        results = [
            StepResult(step_id="tool-1", state=StepState.FAILED, error="Error"),
        ]

        new_plan = replanner.replan(plan, results)
        assert new_plan is not None
        llm_step = next(s for s in new_plan.steps if s.step_id == "llm-1")
        assert "tool-1" not in llm_step.depends_on

    def test_substitute_model_on_llm_failure(self) -> None:
        """Substitute model when LLM step fails and no tool to remove."""
        replanner = DynamicReplanner()
        plan = _make_plan([_llm_step()])
        results = [
            StepResult(step_id="llm-1", state=StepState.FAILED, error="Model error"),
        ]

        new_plan = replanner.replan(plan, results)
        assert new_plan is not None
        # Model should differ from original
        assert new_plan.model_id != "gpt-4o" or new_plan.provider != "openai"

    def test_simplify_plan_llm_only(self) -> None:
        """Simplify complex plan to LLM-only when other strategies fail."""
        # Use same model as fallback to force simplification path
        replanner = DynamicReplanner(
            fallback_models=[("gpt-4o", "openai")]  # Same as original = no substitution
        )
        plan = _make_plan([_llm_step("llm-1")])
        results = [
            StepResult(step_id="llm-1", state=StepState.FAILED, error="Error"),
        ]

        new_plan = replanner.replan(plan, results)
        assert new_plan is not None
        # Simplified plan should have LLM step with no dependencies
        assert all(s.step_type == ExecutionStepType.LLM_CALL for s in new_plan.steps)
        assert all(s.depends_on == [] for s in new_plan.steps)

    def test_fallback_plan_id_set(self) -> None:
        """New plan references original as fallback."""
        replanner = DynamicReplanner()
        plan = _make_plan([_tool_step(), _llm_step("llm-1")])
        results = [
            StepResult(step_id="tool-1", state=StepState.FAILED, error="Err"),
        ]

        new_plan = replanner.replan(plan, results)
        assert new_plan is not None
        assert new_plan.fallback_plan_id == "original-plan"

    def test_preserves_plan_metadata(self) -> None:
        """New plan preserves intent, confidence, etc."""
        replanner = DynamicReplanner()
        plan = _make_plan([_tool_step(), _llm_step("llm-1")])
        results = [
            StepResult(step_id="tool-1", state=StepState.FAILED, error="Err"),
        ]

        new_plan = replanner.replan(plan, results)
        assert new_plan is not None
        assert new_plan.intent == "test"
        assert new_plan.confidence == 0.9

    def test_returns_none_when_no_strategy_works(self) -> None:
        """Returns None when plan cannot be recovered."""
        # Only tool steps, all fail, no LLM to fall back to
        # Use same model as fallback so substitution doesn't produce a valid plan with LLM
        replanner = DynamicReplanner(fallback_models=[("gpt-4o", "openai")])
        plan = ExecutionPlan(
            plan_id="all-tools",
            intent="test",
            steps=[_tool_step("t1"), _tool_step("t2")],
            model_id="gpt-4o",
            provider="openai",
        )
        results = [
            StepResult(step_id="t1", state=StepState.FAILED, error="Err"),
            StepResult(step_id="t2", state=StepState.FAILED, error="Err"),
        ]

        new_plan = replanner.replan(plan, results)
        assert new_plan is None

    def test_custom_fallback_models(self) -> None:
        """Custom fallback models are used for substitution."""
        replanner = DynamicReplanner(fallback_models=[("claude-3-opus", "anthropic")])
        plan = _make_plan([_llm_step()])
        results = [
            StepResult(step_id="llm-1", state=StepState.FAILED, error="Error"),
        ]

        new_plan = replanner.replan(plan, results)
        assert new_plan is not None
        assert new_plan.model_id == "claude-3-opus"
        assert new_plan.provider == "anthropic"

    def test_multiple_tool_failures_removed(self) -> None:
        """Multiple failed tool steps are all removed."""
        replanner = DynamicReplanner()
        plan = _make_plan(
            [
                _tool_step("t1"),
                _tool_step("t2"),
                _llm_step("llm-1", depends_on=["t1", "t2"]),
            ]
        )
        results = [
            StepResult(step_id="t1", state=StepState.FAILED, error="Err"),
            StepResult(step_id="t2", state=StepState.FAILED, error="Err"),
        ]

        new_plan = replanner.replan(plan, results)
        assert new_plan is not None
        step_ids = [s.step_id for s in new_plan.steps]
        assert "t1" not in step_ids
        assert "t2" not in step_ids
        assert "llm-1" in step_ids
