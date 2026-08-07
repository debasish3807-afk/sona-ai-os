"""Unit tests for AgentScheduler."""

import pytest

from sona_workforce.domain.agent import (
    AgentCapability,
    AgentProfile,
    AgentRole,
    AgentState,
)
from sona_workforce.domain.models import AgentTask, AgentType
from sona_workforce.infrastructure.agent_registry import AgentRegistry
from sona_workforce.infrastructure.agent_scheduler import AgentScheduler


def _make_profile(
    agent_id: str,
    agent_type: str = "coding",
    role: AgentRole = AgentRole.WORKER,
    state: AgentState = AgentState.IDLE,
    max_concurrent: int = 3,
    priority: int = 5,
    active_tasks: int = 0,
) -> AgentProfile:
    p = AgentProfile(
        agent_id=agent_id,
        name=f"Agent {agent_id}",
        agent_type=agent_type,
        role=role,
        capabilities=[AgentCapability.CODE_GENERATION],
        state=state,
        max_concurrent_tasks=max_concurrent,
        priority=priority,
    )
    p.active_tasks = active_tasks
    return p


class TestAgentScheduler:
    @pytest.fixture
    def registry(self) -> AgentRegistry:
        return AgentRegistry()

    @pytest.fixture
    def scheduler(self, registry: AgentRegistry) -> AgentScheduler:
        return AgentScheduler(registry)

    def test_queue_starts_empty(self, scheduler: AgentScheduler) -> None:
        assert scheduler.queue_depth == 0

    def test_enqueue(self, scheduler: AgentScheduler) -> None:
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        scheduler.enqueue(task)
        assert scheduler.queue_depth == 1

    def test_dequeue(self, scheduler: AgentScheduler) -> None:
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        scheduler.enqueue(task)
        result = scheduler.dequeue()
        assert result is not None
        assert result.task_id == "t1"
        assert scheduler.queue_depth == 0

    def test_dequeue_empty(self, scheduler: AgentScheduler) -> None:
        assert scheduler.dequeue() is None

    def test_priority_ordering(self, scheduler: AgentScheduler) -> None:
        t_low = AgentTask(task_id="low", agent_type=AgentType.CODING, instruction="x", priority=10)
        t_high = AgentTask(task_id="high", agent_type=AgentType.CODING, instruction="x", priority=1)
        t_mid = AgentTask(task_id="mid", agent_type=AgentType.CODING, instruction="x", priority=5)
        scheduler.enqueue(t_low)
        scheduler.enqueue(t_high)
        scheduler.enqueue(t_mid)
        assert scheduler.dequeue().task_id == "high"  # type: ignore[union-attr]
        assert scheduler.dequeue().task_id == "mid"  # type: ignore[union-attr]
        assert scheduler.dequeue().task_id == "low"  # type: ignore[union-attr]

    @pytest.mark.asyncio
    async def test_select_agent_by_type(
        self, registry: AgentRegistry, scheduler: AgentScheduler
    ) -> None:
        await registry.register(_make_profile("a1", agent_type="coding"))
        await registry.register(_make_profile("a2", agent_type="research"))
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        selected = await scheduler.select_agent(task)
        assert selected is not None
        assert selected.agent_id == "a1"

    @pytest.mark.asyncio
    async def test_select_agent_prefers_lowest_load(
        self, registry: AgentRegistry, scheduler: AgentScheduler
    ) -> None:
        await registry.register(_make_profile("a1", active_tasks=2))
        await registry.register(_make_profile("a2", active_tasks=0))
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        selected = await scheduler.select_agent(task)
        assert selected is not None
        assert selected.agent_id == "a2"

    @pytest.mark.asyncio
    async def test_select_agent_respects_concurrency(
        self, registry: AgentRegistry, scheduler: AgentScheduler
    ) -> None:
        await registry.register(_make_profile("a1", max_concurrent=1, active_tasks=1))
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        selected = await scheduler.select_agent(task)
        assert selected is None

    @pytest.mark.asyncio
    async def test_select_agent_no_match(
        self, registry: AgentRegistry, scheduler: AgentScheduler
    ) -> None:
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        selected = await scheduler.select_agent(task)
        assert selected is None

    @pytest.mark.asyncio
    async def test_select_agent_ignores_error_state(
        self, registry: AgentRegistry, scheduler: AgentScheduler
    ) -> None:
        await registry.register(_make_profile("a1", state=AgentState.ERROR))
        await registry.register(_make_profile("a2", state=AgentState.IDLE))
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        selected = await scheduler.select_agent(task)
        assert selected is not None
        assert selected.agent_id == "a2"

    def test_mark_processing(self, scheduler: AgentScheduler) -> None:
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        scheduler.mark_processing("a1", task)
        assert scheduler.active_count == 1

    def test_mark_completed(self, scheduler: AgentScheduler) -> None:
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        scheduler.mark_processing("a1", task)
        scheduler.mark_completed("a1")
        assert scheduler.active_count == 0

    def test_get_stats(self, scheduler: AgentScheduler) -> None:
        stats = scheduler.get_stats()
        assert "queue_depth" in stats
        assert "active_count" in stats
        assert "total_registered" in stats

    @pytest.mark.asyncio
    async def test_select_prefers_higher_priority(
        self, registry: AgentRegistry, scheduler: AgentScheduler
    ) -> None:
        await registry.register(_make_profile("a1", priority=5))
        await registry.register(_make_profile("a2", priority=1))
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        selected = await scheduler.select_agent(task)
        assert selected is not None
        assert selected.agent_id == "a2"
