"""Unit tests for WritingAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agents.writing_agent import WritingAgent


class TestWritingAgent:
    @pytest.fixture
    def agent(self) -> WritingAgent:
        return WritingAgent()

    def test_agent_id(self, agent: WritingAgent) -> None:
        assert agent.agent_id == "writing-agent-001"

    def test_agent_type(self, agent: WritingAgent) -> None:
        assert agent.agent_type == "communication"

    def test_role(self, agent: WritingAgent) -> None:
        assert agent.profile.role == AgentRole.SPECIALIST

    def test_capabilities(self, agent: WritingAgent) -> None:
        caps = agent.profile.capabilities
        assert AgentCapability.WRITING in caps
        assert AgentCapability.SUMMARIZATION in caps

    def test_max_concurrent(self, agent: WritingAgent) -> None:
        assert agent.profile.max_concurrent_tasks == 4

    @pytest.mark.asyncio
    async def test_process_general(self, agent: WritingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.COMMUNICATION,
            instruction="Write a blog post",
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "Writing Agent" in result.output

    @pytest.mark.asyncio
    async def test_process_documentation(self, agent: WritingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t2",
            agent_type=AgentType.COMMUNICATION,
            instruction="Write the documentation",
        )
        result = await agent.process(task)
        assert "Documentation" in result.output or "documentation" in result.output

    @pytest.mark.asyncio
    async def test_process_email(self, agent: WritingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t3",
            agent_type=AgentType.COMMUNICATION,
            instruction="Draft an email",
        )
        result = await agent.process(task)
        assert "Communication" in result.output or "drafted" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_summarize(self, agent: WritingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t4",
            agent_type=AgentType.COMMUNICATION,
            instruction="Summarize the document",
        )
        result = await agent.process(task)
        assert "summarize" in result.output.lower() or "summar" in result.output.lower()

    @pytest.mark.asyncio
    async def test_tokens_used(self, agent: WritingAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.COMMUNICATION, instruction="x")
        result = await agent.process(task)
        assert result.tokens_used == 500

    @pytest.mark.asyncio
    async def test_tone_context(self, agent: WritingAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.COMMUNICATION,
            instruction="Write something",
            context={"tone": "casual"},
        )
        result = await agent.process(task)
        assert "casual" in result.output.lower()

    @pytest.mark.asyncio
    async def test_custom_agent_id(self) -> None:
        agent = WritingAgent(agent_id="writer-custom")
        assert agent.agent_id == "writer-custom"
