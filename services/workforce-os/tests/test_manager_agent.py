"""Unit tests for ManagerAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agents.manager_agent import ManagerAgent


class TestManagerAgent:
    @pytest.fixture
    def agent(self) -> ManagerAgent:
        return ManagerAgent()

    def test_agent_id(self, agent: ManagerAgent) -> None:
        assert agent.agent_id == "manager-agent-001"

    def test_agent_type(self, agent: ManagerAgent) -> None:
        assert agent.agent_type == "planner"

    def test_role(self, agent: ManagerAgent) -> None:
        assert agent.profile.role == AgentRole.MANAGER

    def test_capabilities(self, agent: ManagerAgent) -> None:
        caps = agent.profile.capabilities
        assert AgentCapability.DELEGATION in caps
        assert AgentCapability.PLANNING in caps
        assert AgentCapability.QUALITY_REVIEW in caps

    def test_max_concurrent(self, agent: ManagerAgent) -> None:
        assert agent.profile.max_concurrent_tasks == 2

    def test_priority(self, agent: ManagerAgent) -> None:
        assert agent.profile.priority == 1

    @pytest.mark.asyncio
    async def test_process_delegate(self, agent: ManagerAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.PLANNER,
            instruction="Delegate this task",
            context={"delegate_to": "coding-agent"},
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "Manager Agent" in result.output
        assert "coding-agent" in result.output

    @pytest.mark.asyncio
    async def test_process_coordinate(self, agent: ManagerAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t2",
            agent_type=AgentType.PLANNER,
            instruction="Coordinate the team",
            context={"team_size": 5},
        )
        result = await agent.process(task)
        assert "5" in result.output
        assert "Coordinating" in result.output

    @pytest.mark.asyncio
    async def test_process_plan(self, agent: ManagerAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t3",
            agent_type=AgentType.PLANNER,
            instruction="Plan the sprint",
        )
        result = await agent.process(task)
        assert "plan" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_general(self, agent: ManagerAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t4",
            agent_type=AgentType.PLANNER,
            instruction="Check status",
        )
        result = await agent.process(task)
        assert "Management" in result.output

    @pytest.mark.asyncio
    async def test_tokens_used(self, agent: ManagerAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.PLANNER, instruction="x")
        result = await agent.process(task)
        assert result.tokens_used == 250

    @pytest.mark.asyncio
    async def test_custom_agent_id(self) -> None:
        agent = ManagerAgent(agent_id="mgr-custom")
        assert agent.agent_id == "mgr-custom"
