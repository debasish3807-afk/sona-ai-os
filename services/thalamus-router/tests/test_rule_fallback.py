"""Unit tests for the RuleFallback."""

from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStepType
from sona_thalamus.infrastructure.rule_fallback import RuleFallback


class TestRuleFallback:
    """Tests for fallback plan generation."""

    def setup_method(self) -> None:
        """Create a fresh fallback generator for each test."""
        self.fallback = RuleFallback()

    def test_creates_valid_plan(self) -> None:
        """Test that fallback creates a valid ExecutionPlan."""
        plan = self.fallback.create_fallback_plan(
            content="Hello",
            confidence=0.1,
        )
        assert isinstance(plan, ExecutionPlan)
        assert plan.plan_id != ""

    def test_plan_uses_default_model(self) -> None:
        """Test that fallback plan uses the default model."""
        plan = self.fallback.create_fallback_plan(
            content="Hello",
            confidence=0.1,
        )
        assert plan.model_id == "llama3.2"
        assert plan.provider == "ollama"

    def test_plan_has_single_llm_step(self) -> None:
        """Test that fallback plan has exactly one LLM step."""
        plan = self.fallback.create_fallback_plan(
            content="Hello",
            confidence=0.1,
        )
        assert len(plan.steps) == 1
        assert plan.steps[0].step_type == ExecutionStepType.LLM_CALL

    def test_plan_intent_is_chat(self) -> None:
        """Test that fallback plan intent is always CHAT."""
        plan = self.fallback.create_fallback_plan(
            content="Implement something",
            confidence=0.05,
        )
        assert plan.intent == "chat"

    def test_plan_includes_confidence(self) -> None:
        """Test that plan stores the original confidence."""
        plan = self.fallback.create_fallback_plan(
            content="Hello",
            confidence=0.12,
        )
        assert plan.confidence == 0.12

    def test_plan_context_has_fallback_flag(self) -> None:
        """Test that plan context marks it as a fallback."""
        plan = self.fallback.create_fallback_plan(
            content="Hello",
            confidence=0.1,
        )
        assert plan.context["fallback"] is True

    def test_plan_includes_session_id(self) -> None:
        """Test that session ID is included in context."""
        plan = self.fallback.create_fallback_plan(
            content="Hello",
            confidence=0.1,
            session_id="sess-abc",
        )
        assert plan.context["session_id"] == "sess-abc"

    def test_plan_requires_streaming(self) -> None:
        """Test that fallback plans use streaming."""
        plan = self.fallback.create_fallback_plan(
            content="Hello",
            confidence=0.1,
        )
        assert plan.requires_streaming is True

    def test_custom_default_model(self) -> None:
        """Test fallback with custom model."""
        fallback = RuleFallback(default_model="gpt-3.5-turbo", default_provider="openai")
        plan = fallback.create_fallback_plan(
            content="Hello",
            confidence=0.1,
        )
        assert plan.model_id == "gpt-3.5-turbo"
        assert plan.provider == "openai"

    def test_plan_has_estimated_latency(self) -> None:
        """Test that plan has latency estimate."""
        plan = self.fallback.create_fallback_plan(
            content="Hello",
            confidence=0.1,
        )
        assert plan.estimated_latency_ms > 0

    def test_plan_has_estimated_cost(self) -> None:
        """Test that plan has cost estimate."""
        plan = self.fallback.create_fallback_plan(
            content="Hello",
            confidence=0.1,
        )
        assert plan.estimated_cost > 0.0
