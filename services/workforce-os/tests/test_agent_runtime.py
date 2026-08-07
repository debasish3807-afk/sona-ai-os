"""Unit tests for AgentRuntime."""

import asyncio

import pytest

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agent_registry import AgentRegistry
from sona_workforce.infrastructure.agent_runtime import AgentRuntime
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class FastAgent(BaseAgent):
    def __init__(self, agent_id: str = "fast-agent") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Fast",
            agent_type=AgentType.CODING,
            role=AgentRole.WORKER,
            capabilities=[AgentCapability.CODE_GENERATION],
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.CODING,
            output="done",
            status="success",
            tokens_used=50,
        )


class SlowAgent(BaseAgent):
    def __init__(self, agent_id: str = "slow-agent") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Slow",
            agent_type=AgentType.CODING,
            role=AgentRole.WORKER,
            capabilities=[AgentCapability.CODE_GENERATION],
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        await asyncio.sleep(10)  # Will be timed out
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.CODING,
            output="done",
            status="success",
        )


class FailingAgent(BaseAgent):
    def __init__(self, agent_id: str = "failing-agent") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Failing",
            agent_type=AgentType.CODING,
            role=AgentRole.WORKER,
            capabilities=[AgentCapability.CODE_GENERATION],
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        raise RuntimeError("Agent crash")


class TestAgentRuntime:
    @pytest.fixture
    def runtime(self) -> AgentRuntime:
        registry = AgentRegistry()
        return AgentRuntime(registry, max_retries=1, default_timeout=5.0)

    @pytest.mark.asyncio
    async def test_execute_success(self, runtime: AgentRuntime) -> None:
        agent = FastAgent()
        await agent.initialize()
        runtime.register_agent_instance(agent)
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await runtime.execute("fast-agent", task)
        assert result.status == "success"
        assert result.output == "done"

    @pytest.mark.asyncio
    async def test_execute_timeout(self, runtime: AgentRuntime) -> None:
        agent = SlowAgent()
        await agent.initialize()
        runtime.register_agent_instance(agent)
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await runtime.execute("slow-agent", task, timeout=0.1)
        assert result.status == "timeout"

    @pytest.mark.asyncio
    async def test_execute_unknown_agent(self, runtime: AgentRuntime) -> None:
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await runtime.execute("nonexistent", task)
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_execute_agent_crash(self, runtime: AgentRuntime) -> None:
        agent = FailingAgent()
        await agent.initialize()
        runtime.register_agent_instance(agent)
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await runtime.execute("failing-agent", task)
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_execute_parallel(self, runtime: AgentRuntime) -> None:
        a1 = FastAgent("agent-1")
        a2 = FastAgent("agent-2")
        await a1.initialize()
        await a2.initialize()
        runtime.register_agent_instance(a1)
        runtime.register_agent_instance(a2)
        tasks = [
            ("agent-1", AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")),
            ("agent-2", AgentTask(task_id="t2", agent_type=AgentType.CODING, instruction="y")),
        ]
        results = await runtime.execute_parallel(tasks)
        assert len(results) == 2
        assert all(r.status == "success" for r in results)

    def test_get_stats(self, runtime: AgentRuntime) -> None:
        stats = runtime.get_stats()
        assert stats["total_executions"] == 0
        assert stats["total_failures"] == 0
        assert stats["registered_agents"] == 0

    @pytest.mark.asyncio
    async def test_stats_increment(self, runtime: AgentRuntime) -> None:
        agent = FastAgent()
        await agent.initialize()
        runtime.register_agent_instance(agent)
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await runtime.execute("fast-agent", task)
        stats = runtime.get_stats()
        assert stats["total_executions"] == 1

    def test_get_agent_instance(self, runtime: AgentRuntime) -> None:
        agent = FastAgent()
        runtime.register_agent_instance(agent)
        assert runtime.get_agent_instance("fast-agent") is agent
        assert runtime.get_agent_instance("missing") is None

    @pytest.mark.asyncio
    async def test_failure_increments_stats(self, runtime: AgentRuntime) -> None:
        agent = FailingAgent()
        await agent.initialize()
        runtime.register_agent_instance(agent)
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await runtime.execute("failing-agent", task)
        stats = runtime.get_stats()
        assert stats["total_failures"] == 1
