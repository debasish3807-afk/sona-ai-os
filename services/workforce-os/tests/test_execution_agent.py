"""Unit tests for ExecutionAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agents.execution_agent import ExecutionAgent


class TestExecutionAgent:
    @pytest.fixture
    def agent(self) -> ExecutionAgent:
        return ExecutionAgent()

    def test_agent_id(self, agent: ExecutionAgent) -> None:
        assert agent.agent_id == "execution-agent-001"

    def test_agent_type(self, agent: ExecutionAgent) -> None:
        assert agent.agent_type == "automation"

    def test_role(self, agent: ExecutionAgent) -> None:
        assert agent.profile.role == AgentRole.WORKER

    def test_capabilities(self, agent: ExecutionAgent) -> None:
        caps = agent.profile.capabilities
        assert AgentCapability.TASK_EXECUTION in caps
        assert AgentCapability.DATA_ANALYSIS in caps

    def test_max_concurrent(self, agent: ExecutionAgent) -> None:
        assert agent.profile.max_concurrent_tasks == 4

    @pytest.mark.asyncio
    async def test_process_execute(self, agent: ExecutionAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.AUTOMATION,
            instruction="Execute the pipeline",
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "Execution Agent" in result.output
        assert "executed" in result.output.lower() or "completed" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_run(self, agent: ExecutionAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t2",
            agent_type=AgentType.AUTOMATION,
            instruction="Run the tests",
        )
        result = await agent.process(task)
        assert "executed" in result.output.lower() or "steps" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_schedule(self, agent: ExecutionAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t3",
            agent_type=AgentType.AUTOMATION,
            instruction="Schedule the job",
        )
        result = await agent.process(task)
        assert "scheduled" in result.output.lower()

    @pytest.mark.asyncio
    async def test_process_automate(self, agent: ExecutionAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t4",
            agent_type=AgentType.AUTOMATION,
            instruction="Automate the process",
        )
        result = await agent.process(task)
        assert "automation" in result.output.lower() or "pipeline" in result.output.lower()

    @pytest.mark.asyncio
    async def test_tokens_used(self, agent: ExecutionAgent) -> None:
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.AUTOMATION, instruction="x")
        result = await agent.process(task)
        assert result.tokens_used == 200

    @pytest.mark.asyncio
    async def test_workflow_context(self, agent: ExecutionAgent) -> None:
        await agent.initialize()
        task = AgentTask(
            task_id="t5",
            agent_type=AgentType.AUTOMATION,
            instruction="Execute task",
            context={"workflow": "ci-pipeline"},
        )
        result = await agent.process(task)
        assert "ci-pipeline" in result.output

    @pytest.mark.asyncio
    async def test_custom_agent_id(self) -> None:
        agent = ExecutionAgent(agent_id="exec-custom")
        assert agent.agent_id == "exec-custom"
