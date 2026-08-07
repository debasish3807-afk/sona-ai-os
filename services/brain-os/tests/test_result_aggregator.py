"""Tests for result aggregator.

Tests verify combining step results into a BrainResponse.
"""

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.infrastructure.result_aggregator import ResultAggregator
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


def _make_plan(steps: list[ExecutionStep]) -> ExecutionPlan:
    """Create a test plan."""
    return ExecutionPlan(
        plan_id="test-plan",
        intent="test",
        steps=steps,
        model_id="default-model",
        provider="default-provider",
    )


def _llm_step(step_id: str = "llm-1") -> ExecutionStep:
    """Create an LLM step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.LLM_CALL,
        target="gpt-4o",
    )


def _tool_step(step_id: str = "tool-1") -> ExecutionStep:
    """Create a tool step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.TOOL_CALL,
        target="web_search",
    )


def _agent_step(step_id: str = "agent-1") -> ExecutionStep:
    """Create an agent step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.AGENT_DELEGATION,
        target="research",
    )


def _memory_step(step_id: str = "mem-1") -> ExecutionStep:
    """Create a memory step."""
    return ExecutionStep(
        step_id=step_id,
        step_type=ExecutionStepType.MEMORY_RETRIEVAL,
        target="memory-os",
    )


class TestResultAggregator:
    """Tests for ResultAggregator."""

    def test_aggregate_single_llm_result(self) -> None:
        """Aggregate a single LLM step result."""
        agg = ResultAggregator()
        plan = _make_plan([_llm_step()])
        results = [
            StepResult(
                step_id="llm-1",
                state=StepState.COMPLETED,
                output={
                    "content": "Hello world",
                    "model": "gpt-4o",
                    "tokens_in": 50,
                    "tokens_out": 20,
                },
                latency_ms=200.0,
            ),
        ]

        response = agg.aggregate(results, plan, "session-1")
        assert response.content == "Hello world"
        assert response.session_id == "session-1"
        assert response.model_used == "gpt-4o"
        assert response.tokens == {"input": 50, "output": 20}
        assert response.latency_ms == 200.0

    def test_aggregate_multiple_llm_steps(self) -> None:
        """Last LLM step's content is used as primary output."""
        agg = ResultAggregator()
        plan = _make_plan([_llm_step("llm-1"), _llm_step("llm-2")])
        results = [
            StepResult(
                step_id="llm-1",
                state=StepState.COMPLETED,
                output={"content": "Step 1", "model": "gpt-4o", "tokens_in": 30, "tokens_out": 10},
                latency_ms=100.0,
            ),
            StepResult(
                step_id="llm-2",
                state=StepState.COMPLETED,
                output={
                    "content": "Final answer",
                    "model": "gpt-4o",
                    "tokens_in": 40,
                    "tokens_out": 20,
                },
                latency_ms=150.0,
            ),
        ]

        response = agg.aggregate(results, plan, "s1")
        assert response.content == "Final answer"
        assert response.tokens == {"input": 70, "output": 30}
        assert response.latency_ms == 250.0

    def test_aggregate_with_agent_step(self) -> None:
        """Agent used is extracted from agent delegation steps."""
        agg = ResultAggregator()
        plan = _make_plan([_agent_step(), _llm_step()])
        results = [
            StepResult(
                step_id="agent-1",
                state=StepState.COMPLETED,
                output={"agent": "research", "result": "data"},
                latency_ms=50.0,
            ),
            StepResult(
                step_id="llm-1",
                state=StepState.COMPLETED,
                output={"content": "Result", "model": "gpt-4o", "tokens_in": 20, "tokens_out": 10},
                latency_ms=100.0,
            ),
        ]

        response = agg.aggregate(results, plan, "s1")
        assert response.agent_used == "research"

    def test_aggregate_with_memory_step(self) -> None:
        """Memory updated flag set when memory step completes."""
        agg = ResultAggregator()
        plan = _make_plan([_memory_step(), _llm_step()])
        results = [
            StepResult(
                step_id="mem-1",
                state=StepState.COMPLETED,
                output={"memories": ["m1"]},
                latency_ms=20.0,
            ),
            StepResult(
                step_id="llm-1",
                state=StepState.COMPLETED,
                output={
                    "content": "With memory",
                    "model": "gpt-4o",
                    "tokens_in": 10,
                    "tokens_out": 5,
                },
                latency_ms=80.0,
            ),
        ]

        response = agg.aggregate(results, plan, "s1")
        assert response.memory_updated is True

    def test_aggregate_no_llm_results(self) -> None:
        """Aggregate with no LLM results uses tool output."""
        agg = ResultAggregator()
        plan = _make_plan([_tool_step()])
        results = [
            StepResult(
                step_id="tool-1",
                state=StepState.COMPLETED,
                output={"result": "tool output"},
                latency_ms=50.0,
            ),
        ]

        response = agg.aggregate(results, plan, "s1")
        assert response.content == "tool output"

    def test_aggregate_all_failed(self) -> None:
        """Aggregate with all failed steps returns empty content."""
        agg = ResultAggregator()
        plan = _make_plan([_llm_step()])
        results = [
            StepResult(
                step_id="llm-1",
                state=StepState.FAILED,
                error="Timeout",
                latency_ms=30000.0,
            ),
        ]

        response = agg.aggregate(results, plan, "s1")
        assert response.content == ""

    def test_aggregate_fallback_model(self) -> None:
        """Model falls back to plan.model_id if not in output."""
        agg = ResultAggregator()
        plan = _make_plan([_tool_step()])
        results = [
            StepResult(
                step_id="tool-1",
                state=StepState.COMPLETED,
                output={"result": "no model"},
                latency_ms=10.0,
            ),
        ]

        response = agg.aggregate(results, plan, "s1")
        assert response.model_used == "default-model"

    def test_aggregate_total_latency(self) -> None:
        """Total latency is sum of all step latencies."""
        agg = ResultAggregator()
        plan = _make_plan([_llm_step("l1"), _llm_step("l2")])
        results = [
            StepResult(
                step_id="l1",
                state=StepState.COMPLETED,
                output={"content": "a", "model": "m", "tokens_in": 1, "tokens_out": 1},
                latency_ms=100.0,
            ),
            StepResult(
                step_id="l2",
                state=StepState.COMPLETED,
                output={"content": "b", "model": "m", "tokens_in": 2, "tokens_out": 2},
                latency_ms=200.0,
            ),
        ]

        response = agg.aggregate(results, plan, "s1")
        assert response.latency_ms == 300.0

    def test_no_agent_returns_none(self) -> None:
        """No agent step means agent_used is None."""
        agg = ResultAggregator()
        plan = _make_plan([_llm_step()])
        results = [
            StepResult(
                step_id="llm-1",
                state=StepState.COMPLETED,
                output={"content": "hi", "model": "m", "tokens_in": 1, "tokens_out": 1},
                latency_ms=10.0,
            ),
        ]

        response = agg.aggregate(results, plan, "s1")
        assert response.agent_used is None
        assert response.memory_updated is False
