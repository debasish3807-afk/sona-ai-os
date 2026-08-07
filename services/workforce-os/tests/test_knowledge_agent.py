"""Unit tests for KnowledgeAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agents.knowledge_agent import KnowledgeAgent


class TestKnowledgeAgent:
    @pytest.fixture
    def agent(self) -> KnowledgeAgent:
        return KnowledgeAgent()

    def test_agent_id(self, agent: KnowledgeAgent) -> None:
        assert agent.agent_id == "knowledge-agent-001"

    def test_agent_type(self, agent: KnowledgeAgent) -> None:
        assert agent.agent_type == "research"

    def test_role(self, agent: KnowledgeAgent) -> None:
        assert agent.profile.role == AgentRole.SPECIALIST

    def test_capabilities(self, agent: KnowledgeAgent) -> None:
        caps = agent.profile.capabilities
        assert AgentCapability.KNOWLEDGE_RETRIEVAL in caps
        assert AgentCapability.RESEARCH in caps
        assert AgentCapability.SUMMARIZATION in caps

    def test_max_concurrent(self, agent: KnowledgeAgent) -> None:
        assert agent.profile.max_concurrent_tasks == 5

    @pytest.mark.asyncio
    async def test_process_search(self, agent: KnowledgeAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.RESEARCH,
            instruction="Search for Python best practices",
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "Knowledge Agent" in result.output
        assert "search" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_index(self, agent: KnowledgeAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t2",
            agent_type=AgentType.RESEARCH,
            instruction="Index the documents",
        )
        result = await agent.process(task)
        assert "indexed" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_extract(self, agent: KnowledgeAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t3",
            agent_type=AgentType.RESEARCH,
            instruction="Extract key concepts",
        )
        result = await agent.process(task)
        assert "extract" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_general(self, agent: KnowledgeAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t4",
            agent_type=AgentType.RESEARCH,
            instruction="Get knowledge",
        )
        result = await agent.process(task)
        assert "retrieval" in result.output.lower()

    @pytest.mark.asyncio
    async def test_tokens_used(self, agent: KnowledgeAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.RESEARCH, instruction="x")
        result = await agent.process(task)
        assert result.tokens_used == 300

    @pytest.mark.asyncio
    async def test_domain_context(self, agent: KnowledgeAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t5",
            agent_type=AgentType.RESEARCH,
            instruction="Get data",
            context={"domain": "machine-learning"},
        )
        result = await agent.process(task)
        assert "machine-learning" in result.output

    @pytest.mark.asyncio
    async def test_custom_agent_id(self) -> None:
        agent = KnowledgeAgent(agent_id="kb-custom")
        assert agent.agent_id == "kb-custom"
