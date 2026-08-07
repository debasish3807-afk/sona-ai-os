"""Integration tests for WorkforceManager."""

import pytest

from sona_workforce.application.ports import AgentCoordinatorPort
from sona_workforce.domain.models import AgentStatus, AgentTask, AgentType
from sona_workforce.infrastructure.agents.coding_agent import CodingAgent
from sona_workforce.infrastructure.agents.execution_agent import ExecutionAgent
from sona_workforce.infrastructure.agents.research_agent import ResearchAgent
from sona_workforce.infrastructure.di import create_workforce_manager
from sona_workforce.infrastructure.workforce_manager import WorkforceManager


class TestWorkforceManager:
    @pytest.fixture
    async def manager(self) -> WorkforceManager:
        wm = WorkforceManager()
        await wm.register_agent(AgentType.CODING, CodingAgent())
        await wm.register_agent(AgentType.RESEARCH, ResearchAgent())
        await wm.register_agent(AgentType.AUTOMATION, ExecutionAgent())
        return wm

    def test_implements_port(self) -> None:
        assert issubclass(WorkforceManager, AgentCoordinatorPort)

    @pytest.mark.asyncio
    async def test_register_agent(self) -> None:
        wm = WorkforceManager()
        await wm.register_agent(AgentType.CODING, CodingAgent())
        agents = await wm.list_agents()
        assert AgentType.CODING in agents

    @pytest.mark.asyncio
    async def test_dispatch_success(self, manager: WorkforceManager) -> None:
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.CODING,
            instruction="Write code",
        )
        result = await manager.dispatch(task)
        assert result.status == "success"
        assert result.task_id == "t1"

    @pytest.mark.asyncio
    async def test_dispatch_routes_by_type(self, manager: WorkforceManager) -> None:
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.RESEARCH,
            instruction="Find info",
        )
        result = await manager.dispatch(task)
        assert result.status == "success"
        assert "Research Agent" in result.output

    @pytest.mark.asyncio
    async def test_dispatch_no_agent_queues(self) -> None:
        wm = WorkforceManager()
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.VOICE,
            instruction="Process speech",
        )
        result = await wm.dispatch(task)
        assert result.status == "queued"

    @pytest.mark.asyncio
    async def test_dispatch_parallel(self, manager: WorkforceManager) -> None:
        tasks = [
            AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x"),
            AgentTask(task_id="t2", agent_type=AgentType.RESEARCH, instruction="y"),
            AgentTask(task_id="t3", agent_type=AgentType.AUTOMATION, instruction="z"),
        ]
        results = await manager.dispatch_parallel(tasks)
        assert len(results) == 3
        assert all(r.status == "success" for r in results)

    @pytest.mark.asyncio
    async def test_list_agents(self, manager: WorkforceManager) -> None:
        agents = await manager.list_agents()
        assert len(agents) >= 3
        assert all(isinstance(s, AgentStatus) for s in agents.values())

    @pytest.mark.asyncio
    async def test_metrics_after_dispatch(self, manager: WorkforceManager) -> None:
        task = AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="x")
        await manager.dispatch(task)
        summary = manager.metrics.get_summary()
        assert summary["tasks_total"] == 1
        assert summary["failures_total"] == 0

    @pytest.mark.asyncio
    async def test_health_check_all(self, manager: WorkforceManager) -> None:
        results = await manager.health_check_all()
        assert len(results) >= 3
        assert all(isinstance(v, bool) for v in results.values())

    @pytest.mark.asyncio
    async def test_get_stats(self, manager: WorkforceManager) -> None:
        stats = manager.get_stats()
        assert "metrics" in stats
        assert "scheduler" in stats
        assert "runtime" in stats
        assert "health" in stats
        assert "communication" in stats
        assert "delegation" in stats

    @pytest.mark.asyncio
    async def test_register_non_base_agent_raises(self) -> None:
        wm = WorkforceManager()
        with pytest.raises(TypeError):
            await wm.register_agent(AgentType.CODING, object())  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_multiple_dispatches(self, manager: WorkforceManager) -> None:
        for i in range(5):
            task = AgentTask(task_id=f"t{i}", agent_type=AgentType.CODING, instruction=f"task {i}")
            result = await manager.dispatch(task)
            assert result.status == "success"
        summary = manager.metrics.get_summary()
        assert summary["tasks_total"] == 5


class TestCreateWorkforceManager:
    @pytest.mark.asyncio
    async def test_creates_with_all_agents(self) -> None:
        wm = await create_workforce_manager()
        agents = await wm.list_agents()
        assert len(agents) >= 4  # Multiple agent types

    @pytest.mark.asyncio
    async def test_all_agents_healthy(self) -> None:
        wm = await create_workforce_manager()
        health = await wm.health_check_all()
        assert all(h is True for h in health.values())

    @pytest.mark.asyncio
    async def test_dispatch_to_any_type(self) -> None:
        wm = await create_workforce_manager()
        types = [AgentType.CODING, AgentType.RESEARCH, AgentType.PLANNER, AgentType.AUTOMATION]
        for at in types:
            task = AgentTask(task_id=f"t-{at}", agent_type=at, instruction="test")
            result = await wm.dispatch(task)
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_parallel_dispatch_all_types(self) -> None:
        wm = await create_workforce_manager()
        tasks = [
            AgentTask(task_id="t1", agent_type=AgentType.CODING, instruction="code"),
            AgentTask(task_id="t2", agent_type=AgentType.RESEARCH, instruction="research"),
            AgentTask(task_id="t3", agent_type=AgentType.PLANNER, instruction="plan"),
        ]
        results = await wm.dispatch_parallel(tasks)
        assert len(results) == 3
        assert all(r.status == "success" for r in results)

    @pytest.mark.asyncio
    async def test_factory_returns_workforce_manager(self) -> None:
        wm = await create_workforce_manager()
        assert isinstance(wm, WorkforceManager)
        assert isinstance(wm, AgentCoordinatorPort)
