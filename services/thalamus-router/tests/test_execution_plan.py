"""Unit tests for the ExecutionPlan domain model."""

from dataclasses import FrozenInstanceError

import pytest
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


class TestExecutionStepType:
    """Tests for ExecutionStepType enum."""

    def test_all_types_defined(self) -> None:
        """Verify all expected step types exist."""
        assert ExecutionStepType.LLM_CALL == "llm_call"
        assert ExecutionStepType.TOOL_CALL == "tool_call"
        assert ExecutionStepType.AGENT_DELEGATION == "agent_delegation"
        assert ExecutionStepType.MEMORY_RETRIEVAL == "memory_retrieval"
        assert ExecutionStepType.KNOWLEDGE_QUERY == "knowledge_query"
        assert ExecutionStepType.PARALLEL_GROUP == "parallel_group"
        assert ExecutionStepType.CONDITIONAL == "conditional"

    def test_type_count(self) -> None:
        """Verify exactly 7 step types exist."""
        assert len(ExecutionStepType) == 7


class TestExecutionStep:
    """Tests for the ExecutionStep frozen dataclass."""

    def test_creation_minimal(self) -> None:
        """Test creating a step with minimal args."""
        step = ExecutionStep(
            step_id="step-1",
            step_type=ExecutionStepType.LLM_CALL,
            target="llama3.2",
        )
        assert step.step_id == "step-1"
        assert step.step_type == ExecutionStepType.LLM_CALL
        assert step.target == "llama3.2"
        assert step.params == {}
        assert step.depends_on == []
        assert step.timeout_seconds == 60.0
        assert step.retryable is True
        assert step.priority == 5

    def test_creation_full(self) -> None:
        """Test creating a step with all args."""
        step = ExecutionStep(
            step_id="step-2",
            step_type=ExecutionStepType.TOOL_CALL,
            target="web_search",
            params={"query": "test"},
            depends_on=["step-1"],
            timeout_seconds=30.0,
            retryable=False,
            priority=3,
        )
        assert step.params == {"query": "test"}
        assert step.depends_on == ["step-1"]
        assert step.timeout_seconds == 30.0
        assert step.retryable is False
        assert step.priority == 3

    def test_is_frozen(self) -> None:
        """Test that ExecutionStep is immutable."""
        step = ExecutionStep(
            step_id="step-1",
            step_type=ExecutionStepType.LLM_CALL,
            target="model",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            step.target = "other"  # type: ignore[misc]


class TestExecutionPlan:
    """Tests for the ExecutionPlan frozen dataclass."""

    def test_creation_minimal(self) -> None:
        """Test creating a plan with minimal required args."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            intent="chat",
            steps=[],
            model_id="llama3.2",
            provider="ollama",
        )
        assert plan.plan_id == "plan-1"
        assert plan.intent == "chat"
        assert plan.steps == []
        assert plan.model_id == "llama3.2"
        assert plan.provider == "ollama"
        assert plan.confidence == 0.0
        assert plan.estimated_latency_ms == 0
        assert plan.estimated_cost == 0.0
        assert plan.requires_streaming is False
        assert plan.fallback_plan_id is None

    def test_creation_with_steps(self) -> None:
        """Test creating a plan with steps."""
        step = ExecutionStep(
            step_id="s1",
            step_type=ExecutionStepType.LLM_CALL,
            target="llama3.2",
        )
        plan = ExecutionPlan(
            plan_id="plan-2",
            intent="code",
            steps=[step],
            model_id="codellama",
            provider="ollama",
            confidence=0.9,
            estimated_latency_ms=2000,
            estimated_cost=0.01,
        )
        assert len(plan.steps) == 1
        assert plan.confidence == 0.9
        assert plan.estimated_latency_ms == 2000

    def test_is_frozen(self) -> None:
        """Test that ExecutionPlan is immutable."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            intent="chat",
            steps=[],
            model_id="llama3.2",
            provider="ollama",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            plan.intent = "code"  # type: ignore[misc]

    def test_plan_with_fallback(self) -> None:
        """Test plan with fallback plan ID."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            intent="code",
            steps=[],
            model_id="gpt-4",
            provider="openai",
            fallback_plan_id="plan-fallback",
        )
        assert plan.fallback_plan_id == "plan-fallback"

    def test_plan_context(self) -> None:
        """Test plan with context data."""
        plan = ExecutionPlan(
            plan_id="plan-1",
            intent="chat",
            steps=[],
            model_id="llama3.2",
            provider="ollama",
            context={"session_id": "s1", "user_id": "u1"},
        )
        assert plan.context["session_id"] == "s1"
        assert plan.context["user_id"] == "u1"
