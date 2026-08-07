"""Unit tests for PlanningAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agents.planning_agent import PlanningAgent


class TestPlanningAgent:
    @pytest.fixture
    def agent(self) -> PlanningAgent:
        return PlanningAgent()

    def test_agent_id(self, agent: PlanningAgent) -> None:
        assert agent.agent_id == "planning-agent-001"

    def test_agent_type(self, agent: PlanningAgent) -> None:
        assert agent.agent_type == "planner"

    def test_role(self, agent: PlanningAgent) -> None:
        assert agent.profile.role == AgentRole.SPECIALIST

    def test_capabilities(self, agent: PlanningAgent) -> None:
        caps = agent.profile.capabilities
        assert AgentCapability.PLANNING in caps
        assert AgentCapability.TASK_EXECUTION in caps

    def test_max_concurrent(self, agent: PlanningAgent) -> None:
        assert agent.profile.max_concurrent_tasks == 4

    @pytest.mark.asyncio
    async def test_process_general(self, agent: PlanningAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.PLANNER,
            instruction="Plan the sprint",
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "Planning Agent" in result.output

    @pytest.mark.asyncio
    async def test_process_roadmap(self, agent: PlanningAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t2",
            agent_type=AgentType.PLANNER,
            instruction="Create a roadmap",
        )
        result = await agent.process(task)
        assert "roadmap" in result.output.lower() or "Roadmap" in result.output

    @pytest.mark.asyncio
    async def test_process_breakdown(self, agent: PlanningAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t3",
            agent_type=AgentType.PLANNER,
            instruction="Breakdown the epic",
        )
        result = await agent.process(task)
        assert "breakdown" in result.output.lower()

    @pytest.mark.asyncio
    async def test_tokens_used(self, agent: PlanningAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.PLANNER, instruction="x")
        result = await agent.process(task)
        assert result.tokens_used == 350

    @pytest.mark.asyncio
    async def test_project_context(self, agent: PlanningAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t4",
            agent_type=AgentType.PLANNER,
            instruction="Plan something",
            context={"project": "sona-ai"},
        )
        result = await agent.process(task)
        assert "sona-ai" in result.output

    @pytest.mark.asyncio
    async def test_custom_agent_id(self) -> None:
        agent = PlanningAgent(agent_id="planner-custom")
        assert agent.agent_id == "planner-custom"
