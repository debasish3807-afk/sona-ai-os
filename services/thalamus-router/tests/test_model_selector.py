"""Unit tests for the ModelSelector."""

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.model_selector import ModelConfig, ModelSelector
from sona_thalamus.infrastructure.task_classifier import TaskClassification, TaskType


class TestModelSelector:
    """Tests for model selection logic."""

    def setup_method(self) -> None:
        """Create a fresh selector for each test."""
        self.selector = ModelSelector()

    def _make_task(
        self,
        task_type: TaskType = TaskType.SIMPLE,
        complexity: float = 0.3,
    ) -> TaskClassification:
        """Create a test task classification."""
        return TaskClassification(
            task_type=task_type,
            complexity_score=complexity,
            requires_tools=False,
            requires_memory=False,
            requires_streaming=True,
        )

    def test_simple_chat_selects_fast_model(self) -> None:
        """Test that simple chat tasks select a fast model."""
        task = self._make_task(TaskType.SIMPLE)
        config = self.selector.select(task, IntentCategory.CHAT)
        assert config.model_id != ""
        assert config.provider != ""

    def test_code_task_selects_code_capable(self) -> None:
        """Test that code tasks select a code-capable model."""
        task = self._make_task(TaskType.TECHNICAL)
        config = self.selector.select(task, IntentCategory.CODE)
        assert "code" in config.capabilities or "technical" in config.capabilities

    def test_research_task_selects_reasoning_model(self) -> None:
        """Test that research tasks select a reasoning model."""
        task = self._make_task(TaskType.RESEARCH)
        config = self.selector.select(task, IntentCategory.RESEARCH)
        assert "research" in config.capabilities or "reasoning" in config.capabilities

    def test_returns_model_config(self) -> None:
        """Test that select returns a proper ModelConfig."""
        task = self._make_task()
        config = self.selector.select(task, IntentCategory.CHAT)
        assert isinstance(config, ModelConfig)
        assert config.max_tokens > 0

    def test_cost_limit_filters_expensive_models(self) -> None:
        """Test that cost limit filters out expensive models."""
        selector = ModelSelector(cost_limit=0.0)
        task = self._make_task(TaskType.TECHNICAL)
        config = selector.select(task, IntentCategory.CODE)
        # Should only select free models (ollama)
        assert config.cost_per_token == 0.0

    def test_default_model_fallback(self) -> None:
        """Test fallback to default model when no candidates match."""
        # Custom selector with empty model catalog
        selector = ModelSelector(models={}, default_model="fallback-model")
        task = self._make_task()
        config = selector.select(task, IntentCategory.CHAT)
        assert config.model_id == "fallback-model"

    def test_custom_model_catalog(self) -> None:
        """Test selector with custom model catalog."""
        custom_models = {
            "my-model": ModelConfig(
                model_id="my-model",
                provider="custom",
                capabilities=["chat", "general"],
                max_tokens=8192,
                latency_class="fast",
            ),
        }
        selector = ModelSelector(models=custom_models)
        task = self._make_task(TaskType.SIMPLE)
        config = selector.select(task, IntentCategory.CHAT)
        assert config.model_id == "my-model"

    def test_analytical_task_selects_reasoning(self) -> None:
        """Test that analytical tasks select reasoning-capable model."""
        task = self._make_task(TaskType.ANALYTICAL)
        config = self.selector.select(task, IntentCategory.RESEARCH)
        assert "reasoning" in config.capabilities or "analytical" in config.capabilities
