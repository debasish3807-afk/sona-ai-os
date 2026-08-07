"""Unit tests for ResearchAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agents.research_agent import ResearchAgent


class TestResearchAgent:
    @pytest.fixture
    def agent(self) -> ResearchAgent:
        return ResearchAgent()

    def test_agent_id(self, agent: ResearchAgent) -> None:
        assert agent.agent_id == "research-agent-001"

    def test_agent_type(self, agent: ResearchAgent) -> None:
        assert agent.agent_type == "research"

    def test_role(self, agent: ResearchAgent) -> None:
        assert agent.profile.role == AgentRole.SPECIALIST

    def test_capabilities(self, agent: ResearchAgent) -> None:
        caps = agent.profile.capabilities
        assert AgentCapability.RESEARCH in caps
        assert AgentCapability.SUMMARIZATION in caps
        assert AgentCapability.DATA_ANALYSIS in caps

    def test_max_concurrent(self, agent: ResearchAgent) -> None:
        assert agent.profile.max_concurrent_tasks == 5

    @pytest.mark.asyncio
    async def test_process_general(self, agent: ResearchAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.RESEARCH,
            instruction="Find papers on AI",
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "Research Agent" in result.output
        assert "Find papers on AI" in result.output

    @pytest.mark.asyncio
    async def test_process_summarize(self, agent: ResearchAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t2",
            agent_type=AgentType.RESEARCH,
            instruction="Summarize the findings",
        )
        result = await agent.process(task)
        assert "Summary" in result.output

    @pytest.mark.asyncio
    async def test_process_analyze(self, agent: ResearchAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t3",
            agent_type=AgentType.RESEARCH,
            instruction="Analyze the data set",
        )
        result = await agent.process(task)
        assert "analysis" in result.output.lower()

    @pytest.mark.asyncio
    async def test_tokens_used(self, agent: ResearchAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.RESEARCH, instruction="x")
        result = await agent.process(task)
        assert result.tokens_used == 450

    @pytest.mark.asyncio
    async def test_process_with_sources(self, agent: ResearchAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t4",
            agent_type=AgentType.RESEARCH,
            instruction="Research topic",
            context={"sources": ["url1", "url2", "url3", "url4", "url5"]},
        )
        result = await agent.process(task)
        assert "5" in result.output

    @pytest.mark.asyncio
    async def test_custom_agent_id(self) -> None:
        agent = ResearchAgent(agent_id="custom-research")
        assert agent.agent_id == "custom-research"
