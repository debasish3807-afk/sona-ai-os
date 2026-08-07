"""Unit tests for HealthMonitor."""

import pytest

from sona_workforce.domain.agent import (
    AgentCapability,
    AgentRole,
    AgentState,
)
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agent_registry import AgentRegistry
from sona_workforce.infrastructure.agents.base_agent import BaseAgent
from sona_workforce.infrastructure.health_monitor import HealthMonitor


class HealthyAgent(BaseAgent):
    def __init__(self, agent_id: str = "healthy-agent") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Healthy",
            agent_type=AgentType.CODING,
            role=AgentRole.WORKER,
            capabilities=[AgentCapability.CODE_GENERATION],
        )

    async def _execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.CODING,
            output="ok",
            status="success",
        )


class UnhealthyAgent(BaseAgent):
    def __init__(self, agent_id: str = "unhealthy-agent") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Unhealthy",
            agent_type=AgentType.CODING,
            role=AgentRole.WORKER,
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        self._healthy = False

    async def _execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.CODING,
            output="",
            status="error",
        )


class TestHealthMonitor:
    @pytest.fixture
    async def env(self) -> tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]:
        registry = AgentRegistry()
        agents: dict[str, BaseAgent] = {}

        healthy = HealthyAgent()
        await healthy.initialize()
        await registry.register(healthy.profile)
        agents["healthy-agent"] = healthy

        unhealthy = UnhealthyAgent()
        await unhealthy.initialize()
        await registry.register(unhealthy.profile)
        agents["unhealthy-agent"] = unhealthy

        monitor = HealthMonitor(registry, agents, max_consecutive_failures=3)
        return registry, agents, monitor

    @pytest.mark.asyncio
    async def test_check_healthy_agent(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        _, _, monitor = env
        status = await monitor.check_agent("healthy-agent")
        assert status.healthy is True
        assert status.last_check_passed is True

    @pytest.mark.asyncio
    async def test_check_unhealthy_agent(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        _, _, monitor = env
        status = await monitor.check_agent("unhealthy-agent")
        assert status.healthy is False
        assert status.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_check_nonexistent_agent(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        _, _, monitor = env
        status = await monitor.check_agent("ghost")
        assert status.healthy is False

    @pytest.mark.asyncio
    async def test_check_all(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        _, _, monitor = env
        results = await monitor.check_all()
        assert "healthy-agent" in results
        assert "unhealthy-agent" in results
        assert results["healthy-agent"].healthy is True
        assert results["unhealthy-agent"].healthy is False

    @pytest.mark.asyncio
    async def test_consecutive_failures_marks_error(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        registry, _, monitor = env
        for _ in range(3):
            await monitor.check_agent("unhealthy-agent")
        profile = registry.get("unhealthy-agent")
        assert profile is not None
        assert profile.state == AgentState.ERROR

    @pytest.mark.asyncio
    async def test_get_healthy_agents(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        _, _, monitor = env
        await monitor.check_all()
        healthy = monitor.get_healthy_agents()
        assert "healthy-agent" in healthy
        assert "unhealthy-agent" not in healthy

    @pytest.mark.asyncio
    async def test_get_unhealthy_agents(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        _, _, monitor = env
        await monitor.check_all()
        unhealthy = monitor.get_unhealthy_agents()
        assert "unhealthy-agent" in unhealthy

    @pytest.mark.asyncio
    async def test_get_status(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        _, _, monitor = env
        await monitor.check_agent("healthy-agent")
        status = monitor.get_status("healthy-agent")
        assert status is not None
        assert status.healthy is True

    def test_get_status_unknown(self) -> None:
        monitor = HealthMonitor(AgentRegistry(), {})
        assert monitor.get_status("unknown") is None

    @pytest.mark.asyncio
    async def test_get_stats(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        _, _, monitor = env
        await monitor.check_all()
        stats = monitor.get_stats()
        assert stats["total_agents"] == 2
        assert stats["healthy_agents"] == 1
        assert stats["unhealthy_agents"] == 1
        assert stats["total_checks"] == 2

    @pytest.mark.asyncio
    async def test_recovery_detection(
        self, env: tuple[AgentRegistry, dict[str, BaseAgent], HealthMonitor]
    ) -> None:
        _, agents, monitor = env
        # First check: unhealthy
        await monitor.check_agent("unhealthy-agent")
        assert monitor.get_status("unhealthy-agent")
        assert not monitor.get_status("unhealthy-agent").healthy  # type: ignore[union-attr]
        # Make it healthy
        agents["unhealthy-agent"]._healthy = True
        await monitor.check_agent("unhealthy-agent")
        assert monitor.get_status("unhealthy-agent").healthy  # type: ignore[union-attr]
