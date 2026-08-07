"""Unit tests for the ExecutionPlanner."""

from sona_thalamus.domain.execution_plan import ExecutionStepType
from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.context_builder import ExecutionContext
from sona_thalamus.infrastructure.execution_planner import ExecutionPlanner
from sona_thalamus.infrastructure.task_classifier import TaskClassification, TaskType


class TestExecutionPlanner:
    """Tests for execution plan building."""

    def setup_method(self) -> None:
        """Create a fresh planner for each test."""
        self.planner = ExecutionPlanner()

    def _make_context(
        self,
        needs_memory: bool = False,
        needs_knowledge: bool = False,
    ) -> ExecutionContext:
        """Create a test execution context."""
        return ExecutionContext(
            session_id="sess-1",
            user_id="user-1",
            needs_memory_retrieval=needs_memory,
            needs_knowledge_query=needs_knowledge,
            token_budget=2048,
        )

    def _make_task(
        self,
        task_type: TaskType = TaskType.SIMPLE,
        requires_streaming: bool = True,
    ) -> TaskClassification:
        """Create a test task classification."""
        return TaskClassification(
            task_type=task_type,
            complexity_score=0.3,
            requires_tools=False,
            requires_memory=False,
            requires_streaming=requires_streaming,
        )

    def test_simple_plan_has_llm_step(self) -> None:
        """Test that a simple plan contains at least one LLM call."""
        context = self._make_context()
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.CHAT,
            task=task,
            context=context,
            model_id="llama3.2",
            provider="ollama",
            tools=[],
            agents=[],
            confidence=0.8,
        )
        llm_steps = [s for s in plan.steps if s.step_type == ExecutionStepType.LLM_CALL]
        assert len(llm_steps) == 1
        assert llm_steps[0].target == "llama3.2"

    def test_plan_includes_memory_step(self) -> None:
        """Test memory retrieval step is added when needed."""
        context = self._make_context(needs_memory=True)
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.MEMORY,
            task=task,
            context=context,
            model_id="llama3.2",
            provider="ollama",
            tools=[],
            agents=[],
            confidence=0.7,
        )
        memory_steps = [s for s in plan.steps if s.step_type == ExecutionStepType.MEMORY_RETRIEVAL]
        assert len(memory_steps) == 1

    def test_plan_includes_knowledge_step(self) -> None:
        """Test knowledge query step is added when needed."""
        context = self._make_context(needs_knowledge=True)
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.RESEARCH,
            task=task,
            context=context,
            model_id="mixtral",
            provider="ollama",
            tools=[],
            agents=[],
            confidence=0.8,
        )
        knowledge_steps = [
            s for s in plan.steps if s.step_type == ExecutionStepType.KNOWLEDGE_QUERY
        ]
        assert len(knowledge_steps) == 1

    def test_plan_includes_tool_steps(self) -> None:
        """Test tool call steps are added."""
        context = self._make_context()
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.CODE,
            task=task,
            context=context,
            model_id="codellama",
            provider="ollama",
            tools=["code_execution", "file_system"],
            agents=[],
            confidence=0.8,
        )
        tool_steps = [s for s in plan.steps if s.step_type == ExecutionStepType.TOOL_CALL]
        assert len(tool_steps) == 2

    def test_plan_includes_agent_steps(self) -> None:
        """Test agent delegation steps are added."""
        context = self._make_context()
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.CODE,
            task=task,
            context=context,
            model_id="codellama",
            provider="ollama",
            tools=[],
            agents=["coding_agent"],
            confidence=0.8,
        )
        agent_steps = [s for s in plan.steps if s.step_type == ExecutionStepType.AGENT_DELEGATION]
        assert len(agent_steps) == 1

    def test_step_ordering_dependencies(self) -> None:
        """Test that LLM step depends on memory and knowledge steps."""
        context = self._make_context(needs_memory=True, needs_knowledge=True)
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.RESEARCH,
            task=task,
            context=context,
            model_id="mixtral",
            provider="ollama",
            tools=[],
            agents=[],
            confidence=0.8,
        )
        llm_step = next(s for s in plan.steps if s.step_type == ExecutionStepType.LLM_CALL)
        assert len(llm_step.depends_on) == 2

    def test_plan_has_valid_plan_id(self) -> None:
        """Test that plan has a unique ID."""
        context = self._make_context()
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.CHAT,
            task=task,
            context=context,
            model_id="llama3.2",
            provider="ollama",
            tools=[],
            agents=[],
            confidence=0.8,
        )
        assert plan.plan_id != ""
        assert len(plan.plan_id) > 0

    def test_plan_estimated_latency(self) -> None:
        """Test that estimated latency is calculated."""
        context = self._make_context()
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.CHAT,
            task=task,
            context=context,
            model_id="llama3.2",
            provider="ollama",
            tools=[],
            agents=[],
            confidence=0.8,
        )
        assert plan.estimated_latency_ms > 0

    def test_plan_estimated_cost(self) -> None:
        """Test that estimated cost is calculated."""
        context = self._make_context()
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.CHAT,
            task=task,
            context=context,
            model_id="llama3.2",
            provider="ollama",
            tools=[],
            agents=[],
            confidence=0.8,
        )
        assert plan.estimated_cost > 0.0

    def test_plan_context_includes_session(self) -> None:
        """Test that plan context includes session info."""
        context = self._make_context()
        task = self._make_task()
        plan = self.planner.build_plan(
            intent=IntentCategory.CHAT,
            task=task,
            context=context,
            model_id="llama3.2",
            provider="ollama",
            tools=[],
            agents=[],
            confidence=0.8,
        )
        assert plan.context["session_id"] == "sess-1"
        assert plan.context["user_id"] == "user-1"
