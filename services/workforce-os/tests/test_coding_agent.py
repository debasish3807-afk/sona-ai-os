"""Unit tests for CodingAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agents.coding_agent import CodingAgent


class TestCodingAgent:
    @pytest.fixture
    def agent(self) -> CodingAgent:
        return CodingAgent()

    def test_agent_id(self, agent: CodingAgent) -> None:
        assert agent.agent_id == "coding-agent-001"

    def test_agent_type(self, agent: CodingAgent) -> None:
        assert agent.agent_type == "coding"

    def test_role(self, agent: CodingAgent) -> None:
        assert agent.profile.role == AgentRole.SPECIALIST

    def test_capabilities(self, agent: CodingAgent) -> None:
        caps = agent.profile.capabilities
        assert AgentCapability.CODE_GENERATION in caps
        assert AgentCapability.CODE_REVIEW in caps

    def test_max_concurrent(self, agent: CodingAgent) -> None:
        assert agent.profile.max_concurrent_tasks == 3

    @pytest.mark.asyncio
    async def test_process_general(self, agent: CodingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.CODING,
            instruction="Write a function",
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "Coding Agent" in result.output
        assert "Write a function" in result.output
        assert "best practices" in result.output

    @pytest.mark.asyncio
    async def test_process_review(self, agent: CodingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t2",
            agent_type=AgentType.CODING,
            instruction="Review the code",
        )
        result = await agent.process(task)
        assert "review" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_debug(self, agent: CodingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t3",
            agent_type=AgentType.CODING,
            instruction="Debug the issue",
        )
        result = await agent.process(task)
        assert "debug" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_test(self, agent: CodingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t4",
            agent_type=AgentType.CODING,
            instruction="Write test cases",
        )
        result = await agent.process(task)
        assert "Test" in result.output or "test" in result.output

    @pytest.mark.asyncio
    async def test_artifacts(self, agent: CodingAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await agent.process(task)
        assert result.artifacts is not None
        assert result.artifacts[0]["type"] == "code"

    @pytest.mark.asyncio
    async def test_tokens_used(self, agent: CodingAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await agent.process(task)
        assert result.tokens_used == 600

    @pytest.mark.asyncio
    async def test_context_language(self, agent: CodingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.CODING,
            instruction="Write code",
            context={"language": "rust"},
        )
        result = await agent.process(task)
        assert "rust" in result.output.lower()

    @pytest.mark.asyncio
    async def test_custom_agent_id(self) -> None:
        agent = CodingAgent(agent_id="my-coder")
        assert agent.agent_id == "my-coder"
