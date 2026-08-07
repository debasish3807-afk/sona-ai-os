"""Unit tests for MemoryAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agents.memory_agent import MemoryAgent


class TestMemoryAgent:
    @pytest.fixture
    def agent(self) -> MemoryAgent:
        return MemoryAgent()

    def test_agent_id(self, agent: MemoryAgent) -> None:
        assert agent.agent_id == "memory-agent-001"

    def test_agent_type(self, agent: MemoryAgent) -> None:
        assert agent.agent_type == "system"

    def test_role(self, agent: MemoryAgent) -> None:
        assert agent.profile.role == AgentRole.WORKER

    def test_capabilities(self, agent: MemoryAgent) -> None:
        caps = agent.profile.capabilities
        assert AgentCapability.MEMORY_MANAGEMENT in caps
        assert AgentCapability.DATA_ANALYSIS in caps

    def test_max_concurrent(self, agent: MemoryAgent) -> None:
        assert agent.profile.max_concurrent_tasks == 6

    @pytest.mark.asyncio
    async def test_process_store(self, agent: MemoryAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.SYSTEM,
            instruction="Store this information",
            context={"key": "name", "value": "sona"},
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "stored" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_retrieve(self, agent: MemoryAgent) -> None:
        await agent.initialize()
        # Store first
        store_task = AgentTask(
            task_id="t1",
            agent_type=AgentType.SYSTEM,
            instruction="Store value",
            context={"key": "test_key", "value": "test_value"},
        )
        await agent.process(store_task)
        # Retrieve
        retrieve_task = AgentTask(
            task_id="t2",
            agent_type=AgentType.SYSTEM,
            instruction="Retrieve from memory",
            context={"key": "test_key"},
        )
        result = await agent.process(retrieve_task)
        assert "test_value" in result.output

    @pytest.mark.asyncio
    async def test_process_clear(self, agent: MemoryAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.SYSTEM,
            instruction="Clear all memory",
        )
        result = await agent.process(task)
        assert "clear" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_general(self, agent: MemoryAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.SYSTEM,
            instruction="Check status",
        )
        result = await agent.process(task)
        assert "Memory Agent" in result.output

    @pytest.mark.asyncio
    async def test_tokens_used(self, agent: MemoryAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.SYSTEM, instruction="x")
        result = await agent.process(task)
        assert result.tokens_used == 150

    @pytest.mark.asyncio
    async def test_custom_agent_id(self) -> None:
        agent = MemoryAgent(agent_id="mem-custom")
        assert agent.agent_id == "mem-custom"
