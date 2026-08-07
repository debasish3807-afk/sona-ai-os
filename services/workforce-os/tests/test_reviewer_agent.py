"""Unit tests for ReviewerAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agents.reviewer_agent import ReviewerAgent


class TestReviewerAgent:
    @pytest.fixture
    def agent(self) -> ReviewerAgent:
        return ReviewerAgent()

    def test_agent_id(self, agent: ReviewerAgent) -> None:
        assert agent.agent_id == "reviewer-agent-001"

    def test_agent_type(self, agent: ReviewerAgent) -> None:
        assert agent.agent_type == "coding"

    def test_role(self, agent: ReviewerAgent) -> None:
        assert agent.profile.role == AgentRole.REVIEWER

    def test_capabilities(self, agent: ReviewerAgent) -> None:
        caps = agent.profile.capabilities
        assert AgentCapability.QUALITY_REVIEW in caps
        assert AgentCapability.CODE_REVIEW in caps
        assert AgentCapability.SUMMARIZATION in caps

    @pytest.mark.asyncio
    async def test_process_code_review(self, agent: ReviewerAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.CODING,
            instruction="Review the code changes",
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "Reviewer Agent" in result.output

    @pytest.mark.asyncio
    async def test_process_quality(self, agent: ReviewerAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t2",
            agent_type=AgentType.CODING,
            instruction="Check quality standards",
        )
        result = await agent.process(task)
        assert "quality" in result.output.lower() or "Quality" in result.output

    @pytest.mark.asyncio
    async def test_process_validate(self, agent: ReviewerAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t3",
            agent_type=AgentType.CODING,
            instruction="Validate the output",
        )
        result = await agent.process(task)
        assert "Validation" in result.output or "validation" in result.output

    @pytest.mark.asyncio
    async def test_tokens_used(self, agent: ReviewerAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await agent.process(task)
        assert result.tokens_used == 350

    @pytest.mark.asyncio
    async def test_review_type_context(self, agent: ReviewerAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.CODING,
            instruction="Review",
            context={"review_type": "security"},
        )
        result = await agent.process(task)
        assert "security" in result.output

    @pytest.mark.asyncio
    async def test_custom_agent_id(self) -> None:
        agent = ReviewerAgent(agent_id="rev-custom")
        assert agent.agent_id == "rev-custom"
