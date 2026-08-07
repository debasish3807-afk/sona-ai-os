"""Unit tests for AgentRegistry."""

import pytest

from sona_workforce.domain.agent import (
    AgentCapability,
    AgentProfile,
    AgentRole,
    AgentState,
)
from sona_workforce.infrastructure.agent_registry import AgentRegistry


def _make_profile(
    agent_id: str = "agent-1",
    agent_type: str = "coding",
    role: AgentRole = AgentRole.WORKER,
    capabilities: list[AgentCapability] | None = None,
    state: AgentState = AgentState.IDLE,
    max_concurrent: int = 3,
) -> AgentProfile:
    return AgentProfile(
        agent_id=agent_id,
        name=f"Agent {agent_id}",
        agent_type=agent_type,
        role=role,
        capabilities=capabilities or [AgentCapability.CODE_GENERATION],
        state=state,
        max_concurrent_tasks=max_concurrent,
    )


class TestAgentRegistry:
    @pytest.mark.asyncio
    async def test_register_agent(self) -> None:
        registry = AgentRegistry()
        profile = _make_profile()
        await registry.register(profile)
        assert registry.count == 1

    @pytest.mark.asyncio
    async def test_register_multiple(self) -> None:
        registry = AgentRegistry()
        await registry.register(_make_profile("a1"))
        await registry.register(_make_profile("a2"))
        assert registry.count == 2

    @pytest.mark.asyncio
    async def test_unregister(self) -> None:
        registry = AgentRegistry()
        await registry.register(_make_profile("a1"))
        result = await registry.unregister("a1")
        assert result is True
        assert registry.count == 0

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self) -> None:
        registry = AgentRegistry()
        result = await registry.unregister("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_agent(self) -> None:
        registry = AgentRegistry()
        profile = _make_profile("a1")
        await registry.register(profile)
        retrieved = registry.get("a1")
        assert retrieved is profile

    def test_get_nonexistent(self) -> None:
        registry = AgentRegistry()
        assert registry.get("missing") is None

    @pytest.mark.asyncio
    async def test_get_by_type(self) -> None:
        registry = AgentRegistry()
        await registry.register(_make_profile("a1", agent_type="coding"))
        await registry.register(_make_profile("a2", agent_type="research"))
        await registry.register(_make_profile("a3", agent_type="coding"))
        result = registry.get_by_type("coding")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_capability(self) -> None:
        registry = AgentRegistry()
        await registry.register(_make_profile("a1", capabilities=[AgentCapability.CODE_GENERATION]))
        await registry.register(_make_profile("a2", capabilities=[AgentCapability.RESEARCH]))
        result = registry.get_by_capability(AgentCapability.CODE_GENERATION)
        assert len(result) == 1
        assert result[0].agent_id == "a1"

    @pytest.mark.asyncio
    async def test_get_by_role(self) -> None:
        registry = AgentRegistry()
        await registry.register(_make_profile("a1", role=AgentRole.MANAGER))
        await registry.register(_make_profile("a2", role=AgentRole.WORKER))
        await registry.register(_make_profile("a3", role=AgentRole.MANAGER))
        result = registry.get_by_role(AgentRole.MANAGER)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_available(self) -> None:
        registry = AgentRegistry()
        await registry.register(_make_profile("a1", state=AgentState.IDLE))
        await registry.register(_make_profile("a2", state=AgentState.ERROR))
        await registry.register(_make_profile("a3", state=AgentState.IDLE))
        result = registry.get_available()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_available_respects_capacity(self) -> None:
        registry = AgentRegistry()
        profile = _make_profile("a1", max_concurrent=1)
        profile.active_tasks = 1
        await registry.register(profile)
        result = registry.get_available()
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_update_state(self) -> None:
        registry = AgentRegistry()
        await registry.register(_make_profile("a1"))
        result = registry.update_state("a1", AgentState.PROCESSING)
        assert result is True
        assert registry.get("a1")
        assert registry.get("a1").state == AgentState.PROCESSING  # type: ignore[union-attr]

    def test_update_state_nonexistent(self) -> None:
        registry = AgentRegistry()
        result = registry.update_state("missing", AgentState.ERROR)
        assert result is False

    @pytest.mark.asyncio
    async def test_all_agents(self) -> None:
        registry = AgentRegistry()
        await registry.register(_make_profile("a1"))
        await registry.register(_make_profile("a2"))
        result = registry.all_agents()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_registry(self) -> None:
        registry = AgentRegistry()
        assert registry.count == 0
        assert registry.all_agents() == []
        assert registry.get_available() == []
        assert registry.get_by_type("coding") == []
