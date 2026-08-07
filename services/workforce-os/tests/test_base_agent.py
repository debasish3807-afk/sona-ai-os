"""Unit tests for BaseAgent."""

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole, AgentState
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing."""

    def __init__(self, should_fail: bool = False) -> None:
        super().__init__(
            agent_id="test-agent-001",
            name="Test Agent",
            agent_type=AgentType.CODING,
            role=AgentRole.WORKER,
            capabilities=[AgentCapability.CODE_GENERATION],
            max_concurrent_tasks=3,
            priority=5,
        )
        self._should_fail = should_fail

    async def _execute(self, task: AgentTask) -> AgentResult:
        if self._should_fail:
            raise RuntimeError("Simulated failure")
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.CODING,
            output=f"Processed: {task.instruction}",
            status="success",
            tokens_used=100,
        )


class TestBaseAgent:
    @pytest.mark.asyncio
    async def test_initialize(self) -> None:
        agent = ConcreteAgent()
        await agent.initialize()
        assert agent.state == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_process_success(self) -> None:
        agent = ConcreteAgent()
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.CODING,
            instruction="Write code",
        )
        result = await agent.process(task)
        assert result.status == "success"
        assert "Processed: Write code" in result.output
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_process_failure(self) -> None:
        agent = ConcreteAgent(should_fail=True)
        await agent.initialize()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.CODING,
            instruction="Fail task",
        )
        result = await agent.process(task)
        assert result.status == "error"
        assert result.output == ""

    @pytest.mark.asyncio
    async def test_state_transitions_on_success(self) -> None:
        agent = ConcreteAgent()
        await agent.initialize()
        assert agent.state == AgentState.IDLE
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await agent.process(task)
        assert agent.state == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_state_transitions_on_failure(self) -> None:
        agent = ConcreteAgent(should_fail=True)
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await agent.process(task)
        assert agent.state == AgentState.ERROR

    @pytest.mark.asyncio
    async def test_metrics_tracking_success(self) -> None:
        agent = ConcreteAgent()
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await agent.process(task)
        metrics = agent.metrics
        assert metrics["total_processed"] == 1
        assert metrics["total_failed"] == 0
        assert metrics["total_tokens"] == 100
        assert metrics["total_duration_ms"] > 0

    @pytest.mark.asyncio
    async def test_metrics_tracking_failure(self) -> None:
        agent = ConcreteAgent(should_fail=True)
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await agent.process(task)
        metrics = agent.metrics
        assert metrics["total_processed"] == 0
        assert metrics["total_failed"] == 1

    @pytest.mark.asyncio
    async def test_get_capabilities(self) -> None:
        agent = ConcreteAgent()
        caps = await agent.get_capabilities()
        assert "code_generation" in caps

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        agent = ConcreteAgent()
        await agent.initialize()
        assert await agent.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_after_error(self) -> None:
        agent = ConcreteAgent(should_fail=True)
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await agent.process(task)
        assert await agent.health_check() is False

    @pytest.mark.asyncio
    async def test_shutdown(self) -> None:
        agent = ConcreteAgent()
        await agent.initialize()
        await agent.shutdown()
        assert agent.state == AgentState.SHUTDOWN

    def test_profile_access(self) -> None:
        agent = ConcreteAgent()
        assert agent.agent_id == "test-agent-001"
        assert agent.agent_type == "coding"

    @pytest.mark.asyncio
    async def test_active_tasks_tracking(self) -> None:
        agent = ConcreteAgent()
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        # Before processing, active_tasks = 0
        assert agent.profile.active_tasks == 0
        await agent.process(task)
        # After processing, active_tasks should be back to 0
        assert agent.profile.active_tasks == 0

    @pytest.mark.asyncio
    async def test_total_completed_increment(self) -> None:
        agent = ConcreteAgent()
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await agent.process(task)
        await agent.process(task)
        assert agent.profile.total_completed == 2

    @pytest.mark.asyncio
    async def test_total_failed_increment(self) -> None:
        agent = ConcreteAgent(should_fail=True)
        await agent.initialize()
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await agent.process(task)
        assert agent.profile.total_failed == 1
