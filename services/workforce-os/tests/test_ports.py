"""Unit tests for Workforce OS abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest

from sona_workforce.application.ports import AgentCoordinatorPort, AgentPort
from sona_workforce.domain.models import AgentResult, AgentStatus, AgentTask, AgentType


class TestAgentPort:
    """Tests for the AgentPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify AgentPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AgentPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = AgentPort.__abstractmethods__
        assert "initialize" in abstract_methods
        assert "process" in abstract_methods
        assert "get_capabilities" in abstract_methods
        assert "health_check" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class CodingAgent(AgentPort):
            async def initialize(self) -> None:
                pass

            async def process(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output="Generated code",
                    status="success",
                )

            async def get_capabilities(self) -> list[str]:
                return ["code_generation", "code_review", "debugging"]

            async def health_check(self) -> bool:
                return True

        agent = CodingAgent()
        assert isinstance(agent, AgentPort)

    def test_partial_implementation_raises(self) -> None:
        """Verify partial implementations cannot be instantiated."""

        class IncompleteAgent(AgentPort):
            async def initialize(self) -> None:
                pass

            async def process(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output="",
                    status="success",
                )

        with pytest.raises(TypeError):
            IncompleteAgent()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_process_returns_agent_result(self) -> None:
        """Test that a concrete process() returns the right type."""

        class MockAgent(AgentPort):
            async def initialize(self) -> None:
                pass

            async def process(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output=f"Processed: {task.instruction}",
                    status="success",
                    tokens_used=100,
                    duration_ms=50.0,
                )

            async def get_capabilities(self) -> list[str]:
                return ["general"]

            async def health_check(self) -> bool:
                return True

        agent = MockAgent()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.CODING,
            instruction="Write tests",
        )
        result = await agent.process(task)
        assert result.task_id == "t1"
        assert result.output == "Processed: Write tests"
        assert isinstance(result, AgentResult)
        assert result.tokens_used == 100

    @pytest.mark.asyncio
    async def test_get_capabilities_returns_list(self) -> None:
        """Test that get_capabilities returns capability list."""

        class ResearchAgent(AgentPort):
            async def initialize(self) -> None:
                pass

            async def process(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output="",
                    status="success",
                )

            async def get_capabilities(self) -> list[str]:
                return ["web_search", "summarization", "fact_checking"]

            async def health_check(self) -> bool:
                return True

        agent = ResearchAgent()
        caps = await agent.get_capabilities()
        assert "web_search" in caps
        assert "summarization" in caps
        assert len(caps) == 3

    @pytest.mark.asyncio
    async def test_health_check_returns_bool(self) -> None:
        """Test that health_check returns boolean status."""

        class HealthyAgent(AgentPort):
            async def initialize(self) -> None:
                pass

            async def process(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output="",
                    status="success",
                )

            async def get_capabilities(self) -> list[str]:
                return []

            async def health_check(self) -> bool:
                return True

        agent = HealthyAgent()
        assert await agent.health_check() is True


class TestAgentCoordinatorPort:
    """Tests for the AgentCoordinatorPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify AgentCoordinatorPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AgentCoordinatorPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = AgentCoordinatorPort.__abstractmethods__
        assert "dispatch" in abstract_methods
        assert "dispatch_parallel" in abstract_methods
        assert "register_agent" in abstract_methods
        assert "list_agents" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteCoordinator(AgentCoordinatorPort):
            async def dispatch(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output="dispatched",
                    status="success",
                )

            async def dispatch_parallel(self, tasks: list[AgentTask]) -> list[AgentResult]:
                return [
                    AgentResult(
                        task_id=t.task_id,
                        agent_type=t.agent_type,
                        output="done",
                        status="success",
                    )
                    for t in tasks
                ]

            async def register_agent(self, agent_type: AgentType, agent: AgentPort) -> None:
                pass

            async def list_agents(self) -> dict[AgentType, AgentStatus]:
                return {}

        coordinator = ConcreteCoordinator()
        assert isinstance(coordinator, AgentCoordinatorPort)

    def test_partial_implementation_raises(self) -> None:
        """Verify partial implementations cannot be instantiated."""

        class PartialCoordinator(AgentCoordinatorPort):
            async def dispatch(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output="",
                    status="success",
                )

        with pytest.raises(TypeError):
            PartialCoordinator()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_dispatch_returns_agent_result(self) -> None:
        """Test that dispatch routes task and returns result."""

        class MockCoordinator(AgentCoordinatorPort):
            async def dispatch(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output=f"Routed to {task.agent_type} agent",
                    status="success",
                    tokens_used=200,
                    duration_ms=150.0,
                )

            async def dispatch_parallel(self, tasks: list[AgentTask]) -> list[AgentResult]:
                return []

            async def register_agent(self, agent_type: AgentType, agent: AgentPort) -> None:
                pass

            async def list_agents(self) -> dict[AgentType, AgentStatus]:
                return {}

        coordinator = MockCoordinator()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.RESEARCH,
            instruction="Find papers on transformers",
        )
        result = await coordinator.dispatch(task)
        assert result.task_id == "t1"
        assert result.output == "Routed to research agent"
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_dispatch_parallel_returns_list(self) -> None:
        """Test that dispatch_parallel handles multiple tasks."""

        class MockCoordinator(AgentCoordinatorPort):
            async def dispatch(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output="",
                    status="success",
                )

            async def dispatch_parallel(self, tasks: list[AgentTask]) -> list[AgentResult]:
                return [
                    AgentResult(
                        task_id=t.task_id,
                        agent_type=t.agent_type,
                        output=f"Result for {t.task_id}",
                        status="success",
                    )
                    for t in tasks
                ]

            async def register_agent(self, agent_type: AgentType, agent: AgentPort) -> None:
                pass

            async def list_agents(self) -> dict[AgentType, AgentStatus]:
                return {}

        coordinator = MockCoordinator()
        tasks = [
            AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="Write code"),
            AgentTask(task_id="t2", agent_type=AgentType.RESEARCH, instruction="Find info"),
            AgentTask(task_id="t3", agent_type=AgentType.PLANNER, instruction="Plan steps"),
        ]
        results = await coordinator.dispatch_parallel(tasks)
        assert len(results) == 3
        assert results[0].task_id == "t1"
        assert results[2].task_id == "t3"

    @pytest.mark.asyncio
    async def test_list_agents_returns_status_dict(self) -> None:
        """Test that list_agents returns agent type to status mapping."""

        class MockCoordinator(AgentCoordinatorPort):
            async def dispatch(self, task: AgentTask) -> AgentResult:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    output="",
                    status="success",
                )

            async def dispatch_parallel(self, tasks: list[AgentTask]) -> list[AgentResult]:
                return []

            async def register_agent(self, agent_type: AgentType, agent: AgentPort) -> None:
                pass

            async def list_agents(self) -> dict[AgentType, AgentStatus]:
                return {
                    AgentType.CODING: AgentStatus.IDLE,
                    AgentType.RESEARCH: AgentStatus.BUSY,
                    AgentType.SYSTEM: AgentStatus.STOPPED,
                }

        coordinator = MockCoordinator()
        agents = await coordinator.list_agents()
        assert agents[AgentType.CODING] == AgentStatus.IDLE
        assert agents[AgentType.RESEARCH] == AgentStatus.BUSY
        assert agents[AgentType.SYSTEM] == AgentStatus.STOPPED
        assert len(agents) == 3
