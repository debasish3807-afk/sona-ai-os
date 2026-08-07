"""Unit tests for DelegationEngine."""

import pytest

from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agent_registry import AgentRegistry
from sona_workforce.infrastructure.agents.base_agent import BaseAgent
from sona_workforce.infrastructure.agents.coding_agent import CodingAgent
from sona_workforce.infrastructure.agents.execution_agent import ExecutionAgent
from sona_workforce.infrastructure.agents.manager_agent import ManagerAgent
from sona_workforce.infrastructure.delegation_engine import DelegationEngine


class TestDelegationEngine:
    @pytest.fixture
    async def env(self) -> tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]:
        registry = AgentRegistry()
        agents: dict[str, BaseAgent] = {}

        mgr = ManagerAgent()
        await mgr.initialize()
        await registry.register(mgr.profile)
        agents[mgr.agent_id] = mgr

        coder = CodingAgent()
        await coder.initialize()
        await registry.register(coder.profile)
        agents[coder.agent_id] = coder

        executor = ExecutionAgent()
        await executor.initialize()
        await registry.register(executor.profile)
        agents[executor.agent_id] = executor

        engine = DelegationEngine(registry, agents, max_depth=3)
        return registry, agents, engine

    @pytest.mark.asyncio
    async def test_manager_delegates_to_worker(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]
    ) -> None:
        _, _, engine = env
        task = AgentTask(task_id="t1", agent_type=AgentType.AUTOMATION, instruction="Run job")
        result = await engine.delegate("manager-agent-001", task)
        assert result.success is True
        assert result.to_agent == "execution-agent-001"

    @pytest.mark.asyncio
    async def test_worker_cannot_delegate(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]
    ) -> None:
        _, _, engine = env
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await engine.delegate("execution-agent-001", task)
        assert result.success is False
        assert "cannot delegate" in result.error

    @pytest.mark.asyncio
    async def test_depth_limit(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]
    ) -> None:
        _, _, engine = env
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await engine.delegate("manager-agent-001", task, depth=3)
        assert result.success is False
        assert "depth" in result.error.lower()

    @pytest.mark.asyncio
    async def test_unknown_agent(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]
    ) -> None:
        _, _, engine = env
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        result = await engine.delegate("nonexistent", task)
        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_delegation_chain(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]
    ) -> None:
        _, _, engine = env
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="Write code")
        result = await engine.delegate("manager-agent-001", task)
        assert result.success is True
        assert "manager-agent-001" in result.chain
        assert result.to_agent in result.chain

    @pytest.mark.asyncio
    async def test_split_and_delegate(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]
    ) -> None:
        _, _, engine = env
        task = AgentTask(task_id="big-task", agent_type=AgentType.AUTOMATION, instruction="Do all")
        results = await engine.split_and_delegate(
            "manager-agent-001", task, ["sub1", "sub2", "sub3"]
        )
        assert len(results) == 3
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_delegation_count(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]
    ) -> None:
        _, _, engine = env
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await engine.delegate("manager-agent-001", task)
        assert engine.delegation_count == 1

    @pytest.mark.asyncio
    async def test_get_stats(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]
    ) -> None:
        _, _, engine = env
        stats = engine.get_stats()
        assert stats["max_depth"] == 3
        assert stats["total_delegations"] == 0

    @pytest.mark.asyncio
    async def test_delegation_result_has_agent_result(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], DelegationEngine]
    ) -> None:
        _, _, engine = env
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="Write code")
        result = await engine.delegate("manager-agent-001", task)
        assert result.result is not None
        assert result.result.task_id == "t1"
