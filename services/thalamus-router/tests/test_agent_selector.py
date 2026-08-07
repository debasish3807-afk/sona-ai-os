"""Unit tests for the AgentSelector."""

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.agent_selector import AgentSelector
from sona_thalamus.infrastructure.task_classifier import TaskClassification, TaskType


class TestAgentSelector:
    """Tests for agent selection logic."""

    def setup_method(self) -> None:
        """Create a fresh selector for each test."""
        self.selector = AgentSelector()

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

    def test_code_intent_agents(self) -> None:
        """Test that code intent includes coding agent."""
        task = self._make_task(TaskType.TECHNICAL)
        agents = self.selector.select(IntentCategory.CODE, task)
        assert "coding_agent" in agents

    def test_research_intent_agents(self) -> None:
        """Test that research intent includes research agent."""
        task = self._make_task(TaskType.RESEARCH)
        agents = self.selector.select(IntentCategory.RESEARCH, task)
        assert "research_agent" in agents

    def test_automation_intent_agents(self) -> None:
        """Test that automation intent includes workflow agent."""
        task = self._make_task(TaskType.COMPOSITE)
        agents = self.selector.select(IntentCategory.AUTOMATION, task)
        assert "workflow_agent" in agents

    def test_chat_no_agents(self) -> None:
        """Test that simple chat doesn't require agents."""
        task = self._make_task(TaskType.SIMPLE, complexity=0.1)
        agents = self.selector.select(IntentCategory.CHAT, task)
        assert agents == []

    def test_complex_task_adds_planner(self) -> None:
        """Test that complex tasks add planner agent."""
        task = self._make_task(TaskType.SIMPLE, complexity=0.8)
        agents = self.selector.select(IntentCategory.CHAT, task)
        assert "planner_agent" in agents

    def test_composite_task_adds_planner(self) -> None:
        """Test that composite task type adds planner agent."""
        task = self._make_task(TaskType.COMPOSITE, complexity=0.3)
        agents = self.selector.select(IntentCategory.CHAT, task)
        assert "planner_agent" in agents

    def test_analytical_task_adds_reasoning(self) -> None:
        """Test that analytical tasks add reasoning agent."""
        task = self._make_task(TaskType.ANALYTICAL, complexity=0.3)
        agents = self.selector.select(IntentCategory.CHAT, task)
        assert "reasoning_agent" in agents

    def test_creative_task_adds_creative_agent(self) -> None:
        """Test that creative tasks add creative agent."""
        task = self._make_task(TaskType.CREATIVE, complexity=0.3)
        agents = self.selector.select(IntentCategory.CHAT, task)
        assert "creative_agent" in agents

    def test_returns_sorted_list(self) -> None:
        """Test that results are sorted."""
        task = self._make_task(TaskType.TECHNICAL, complexity=0.8)
        agents = self.selector.select(IntentCategory.CODE, task)
        assert agents == sorted(agents)

    def test_no_duplicates(self) -> None:
        """Test that agent list has no duplicates."""
        task = self._make_task(TaskType.TECHNICAL, complexity=0.8)
        agents = self.selector.select(IntentCategory.CODE, task)
        assert len(agents) == len(set(agents))

    def test_custom_complexity_threshold(self) -> None:
        """Test custom complexity threshold."""
        selector = AgentSelector(complexity_threshold=0.9)
        task = self._make_task(TaskType.SIMPLE, complexity=0.8)
        agents = selector.select(IntentCategory.CHAT, task)
        assert "planner_agent" not in agents
