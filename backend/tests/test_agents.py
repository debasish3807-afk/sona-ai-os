"""Comprehensive tests for the Multi-Agent Coordination Fabric."""

from __future__ import annotations

import pytest

from agents.agent_capability_mapper import AgentCapabilityMapper
from agents.agent_checkpoint import AgentCheckpoint
from agents.agent_context import AgentContext
from agents.agent_coordinator import AgentCoordinator
from agents.agent_delegator import AgentDelegator
from agents.agent_executor import AgentExecutor
from agents.agent_factory import AgentFactory
from agents.agent_lifecycle import AgentLifecycle
from agents.agent_manager import AgentManager
from agents.agent_memory import AgentMemory
from agents.agent_metrics import AgentMetrics
from agents.agent_monitor import AgentMonitor
from agents.agent_negotiator import AgentNegotiator
from agents.agent_permissions import AgentPermissions, Permission
from agents.agent_policies import AgentPolicy, PolicyEngine
from agents.agent_profile import AgentProfile, ProfileRegistry
from agents.agent_recovery import AgentRecovery
from agents.agent_registry import AgentRegistry
from agents.agent_router import AgentRouter
from agents.agent_scheduler import AgentScheduler
from agents.agent_security import AgentSecurity
from agents.agent_selector import AgentSelector
from agents.agent_supervisor import AgentSupervisor
from agents.agent_telemetry import AgentTelemetry
from agents.events import AgentEvent, AgentEventType
from agents.exceptions import (
    AgentNotFoundError,
    DelegationError,
)
from agents.schemas import (
    Agent,
    AgentMessage,
    AgentPriority,
    AgentState,
    AgentTask,
    AgentType,
    CoordinationMode,
    CoordinationPlan,
)

# ============================================================
# Agent Creation / Termination Tests (15)
# ============================================================


class TestAgentCreation:
    """Tests for agent creation and termination."""

    @pytest.mark.asyncio
    async def test_create_agent_basic(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        agent = await mgr.create_agent("test", AgentType.CODING)
        assert agent.name == "test"
        assert agent.agent_type == AgentType.CODING

    @pytest.mark.asyncio
    async def test_create_agent_with_capabilities(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        agent = await mgr.create_agent("test", AgentType.CODING, capabilities=["python", "rust"])
        assert "python" in agent.capabilities

    @pytest.mark.asyncio
    async def test_create_agent_registered(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        agent = await mgr.create_agent("test", AgentType.RESEARCH)
        assert registry.get(agent.agent_id) is not None

    @pytest.mark.asyncio
    async def test_terminate_agent(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        agent = await mgr.create_agent("test", AgentType.PLANNER)
        result = await mgr.terminate_agent(agent.agent_id)
        assert result is True
        assert registry.get(agent.agent_id) is None

    @pytest.mark.asyncio
    async def test_terminate_nonexistent(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        result = await mgr.terminate_agent("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_create_multiple_agents(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        await mgr.create_agent("a1", AgentType.CODING)
        await mgr.create_agent("a2", AgentType.RESEARCH)
        assert registry.count == 2

    @pytest.mark.asyncio
    async def test_get_agent(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        agent = await mgr.create_agent("test", AgentType.MEMORY)
        found = mgr.get_agent(agent.agent_id)
        assert found is not None
        assert found.name == "test"

    @pytest.mark.asyncio
    async def test_list_agents_empty(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        assert mgr.list_agents() == []

    @pytest.mark.asyncio
    async def test_list_agents_by_state(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        await mgr.create_agent("test", AgentType.CODING)
        result = mgr.list_agents(state=AgentState.CREATED)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_status(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        await mgr.create_agent("test", AgentType.CODING)
        status = mgr.get_status()
        assert status["total_agents"] == 1

    @pytest.mark.asyncio
    async def test_assign_task(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        agent = await mgr.create_agent("test", AgentType.CODING)
        task = await mgr.assign_task(agent.agent_id, "write code")
        assert task.agent_id == agent.agent_id
        assert task.description == "write code"

    @pytest.mark.asyncio
    async def test_assign_task_nonexistent_agent(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        with pytest.raises(AgentNotFoundError):
            await mgr.assign_task("fake", "task")

    @pytest.mark.asyncio
    async def test_agent_state_after_creation(self):
        factory = AgentFactory()
        agent = factory.create("test", AgentType.PLANNER)
        assert agent.state == AgentState.CREATED

    @pytest.mark.asyncio
    async def test_agent_has_unique_id(self):
        factory = AgentFactory()
        a1 = factory.create("a1", AgentType.CODING)
        a2 = factory.create("a2", AgentType.CODING)
        assert a1.agent_id != a2.agent_id

    @pytest.mark.asyncio
    async def test_agent_default_priority(self):
        factory = AgentFactory()
        agent = factory.create("test", AgentType.CODING)
        assert agent.priority == AgentPriority.NORMAL


# ============================================================
# Agent Registry Tests (15)
# ============================================================


class TestAgentRegistry:
    """Tests for agent registry."""

    def test_register_agent(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        assert reg.register(agent) is True

    def test_register_duplicate(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        reg.register(agent)
        assert reg.register(agent) is False

    def test_deregister_agent(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        reg.register(agent)
        assert reg.deregister(agent.agent_id) is True

    def test_deregister_nonexistent(self):
        reg = AgentRegistry()
        assert reg.deregister("fake") is False

    def test_get_agent(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        reg.register(agent)
        assert reg.get(agent.agent_id) == agent

    def test_get_nonexistent(self):
        reg = AgentRegistry()
        assert reg.get("fake") is None

    def test_list_all(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        a2 = Agent(name="a2", agent_type=AgentType.RESEARCH)
        reg.register(a1)
        reg.register(a2)
        assert len(reg.list_all()) == 2

    def test_list_by_type(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        a2 = Agent(name="a2", agent_type=AgentType.RESEARCH)
        reg.register(a1)
        reg.register(a2)
        assert len(reg.list_by_type(AgentType.CODING)) == 1

    def test_list_by_state(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        a1.state = AgentState.IDLE
        reg.register(a1)
        assert len(reg.list_by_state(AgentState.IDLE)) == 1
        assert len(reg.list_by_state(AgentState.RUNNING)) == 0

    def test_discover_capability(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING, capabilities=["python", "rust"])
        reg.register(a1)
        assert len(reg.discover("python")) == 1
        assert len(reg.discover("java")) == 0

    def test_count_property(self):
        reg = AgentRegistry()
        assert reg.count == 0
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        assert reg.count == 1

    def test_get_stats(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        stats = reg.get_stats()
        assert stats["total"] == 1

    def test_list_all_empty(self):
        reg = AgentRegistry()
        assert reg.list_all() == []

    def test_discover_multiple(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING, capabilities=["python"])
        a2 = Agent(name="a2", agent_type=AgentType.TESTING, capabilities=["python"])
        reg.register(a1)
        reg.register(a2)
        assert len(reg.discover("python")) == 2

    def test_register_returns_true(self):
        reg = AgentRegistry()
        a = Agent(name="x", agent_type=AgentType.PLANNER)
        assert reg.register(a) is True


# ============================================================
# Agent Factory Tests (15)
# ============================================================


class TestAgentFactory:
    """Tests for agent factory."""

    def test_create_basic(self):
        f = AgentFactory()
        agent = f.create("test", AgentType.CODING)
        assert agent.name == "test"

    def test_create_with_capabilities(self):
        f = AgentFactory()
        agent = f.create("test", AgentType.CODING, capabilities=["python"])
        assert "python" in agent.capabilities

    def test_create_default_capabilities(self):
        f = AgentFactory()
        agent = f.create("test", AgentType.PLANNER)
        assert "planning" in agent.capabilities
        assert "decomposition" in agent.capabilities

    def test_create_with_priority(self):
        f = AgentFactory()
        agent = f.create("test", AgentType.CODING, priority=AgentPriority.HIGH)
        assert agent.priority == AgentPriority.HIGH

    def test_create_with_metadata(self):
        f = AgentFactory()
        agent = f.create("test", AgentType.CODING, metadata={"version": "1.0"})
        assert agent.metadata["version"] == "1.0"

    def test_create_team(self):
        f = AgentFactory()
        specs = [
            {"name": "planner", "agent_type": AgentType.PLANNER},
            {"name": "coder", "agent_type": AgentType.CODING},
        ]
        team = f.create_team(specs)
        assert len(team) == 2

    def test_create_team_empty(self):
        f = AgentFactory()
        team = f.create_team([])
        assert team == []

    def test_default_capabilities_research(self):
        f = AgentFactory()
        agent = f.create("r", AgentType.RESEARCH)
        assert "search" in agent.capabilities

    def test_default_capabilities_security(self):
        f = AgentFactory()
        agent = f.create("s", AgentType.SECURITY)
        assert "threat_analysis" in agent.capabilities

    def test_default_capabilities_memory(self):
        f = AgentFactory()
        agent = f.create("m", AgentType.MEMORY)
        assert "storage" in agent.capabilities

    def test_default_capabilities_testing(self):
        f = AgentFactory()
        agent = f.create("t", AgentType.TESTING)
        assert "test_generation" in agent.capabilities

    def test_default_capabilities_custom(self):
        f = AgentFactory()
        agent = f.create("c", AgentType.CUSTOM)
        assert "custom" in agent.capabilities

    def test_create_state_is_created(self):
        f = AgentFactory()
        agent = f.create("test", AgentType.CODING)
        assert agent.state == AgentState.CREATED

    def test_create_generates_unique_ids(self):
        f = AgentFactory()
        a1 = f.create("a", AgentType.CODING)
        a2 = f.create("b", AgentType.CODING)
        assert a1.agent_id != a2.agent_id

    def test_create_team_with_capabilities(self):
        f = AgentFactory()
        specs = [{"name": "x", "agent_type": AgentType.CODING, "capabilities": ["go"]}]
        team = f.create_team(specs)
        assert "go" in team[0].capabilities


# ============================================================
# Agent Lifecycle State Machine Tests (15)
# ============================================================


class TestAgentLifecycle:
    """Tests for agent lifecycle state machine."""

    def test_valid_transition_created_to_initializing(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        assert lc.transition(agent, AgentState.INITIALIZING) is True
        assert agent.state == AgentState.INITIALIZING

    def test_valid_transition_initializing_to_idle(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.INITIALIZING)
        assert lc.transition(agent, AgentState.IDLE) is True

    def test_valid_transition_idle_to_assigned(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.IDLE)
        assert lc.transition(agent, AgentState.ASSIGNED) is True

    def test_valid_transition_assigned_to_running(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        assert lc.transition(agent, AgentState.RUNNING) is True

    def test_valid_transition_running_to_completed(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.RUNNING)
        assert lc.transition(agent, AgentState.COMPLETED) is True

    def test_valid_transition_running_to_failed(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.RUNNING)
        assert lc.transition(agent, AgentState.FAILED) is True

    def test_valid_transition_running_to_paused(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.RUNNING)
        assert lc.transition(agent, AgentState.PAUSED) is True

    def test_valid_transition_paused_to_running(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.PAUSED)
        assert lc.transition(agent, AgentState.RUNNING) is True

    def test_valid_transition_paused_to_terminated(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.PAUSED)
        assert lc.transition(agent, AgentState.TERMINATED) is True

    def test_invalid_transition_created_to_running(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        assert lc.transition(agent, AgentState.RUNNING) is False
        assert agent.state == AgentState.CREATED

    def test_invalid_transition_terminated(self):
        lc = AgentLifecycle()
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.TERMINATED)
        assert lc.transition(agent, AgentState.IDLE) is False

    def test_can_transition_true(self):
        lc = AgentLifecycle()
        assert lc.can_transition(AgentState.IDLE, AgentState.ASSIGNED) is True

    def test_can_transition_false(self):
        lc = AgentLifecycle()
        assert lc.can_transition(AgentState.IDLE, AgentState.RUNNING) is False

    def test_get_valid_transitions(self):
        lc = AgentLifecycle()
        valid = lc.get_valid_transitions(AgentState.RUNNING)
        assert AgentState.COMPLETED in valid
        assert AgentState.FAILED in valid
        assert AgentState.PAUSED in valid

    def test_get_valid_transitions_terminated(self):
        lc = AgentLifecycle()
        valid = lc.get_valid_transitions(AgentState.TERMINATED)
        assert valid == []


# ============================================================
# Agent Context Isolation Tests (10)
# ============================================================


class TestAgentContext:
    """Tests for agent context isolation."""

    def test_set_and_get(self):
        ctx = AgentContext("agent1")
        ctx.set("key", "value")
        assert ctx.get("key") == "value"

    def test_get_default(self):
        ctx = AgentContext("agent1")
        assert ctx.get("missing", "default") == "default"

    def test_snapshot(self):
        ctx = AgentContext("agent1", "task1")
        ctx.set("x", 42)
        snap = ctx.snapshot()
        assert snap["variables"]["x"] == 42
        assert snap["agent_id"] == "agent1"

    def test_restore(self):
        ctx = AgentContext("agent1")
        ctx.set("x", 42)
        snap = ctx.snapshot()
        ctx.set("x", 99)
        ctx.restore(snap)
        assert ctx.get("x") == 42

    def test_isolate(self):
        ctx = AgentContext("agent1")
        ctx.set("x", [1, 2, 3])
        isolated = ctx.isolate()
        isolated.set("x", [4, 5, 6])
        assert ctx.get("x") == [1, 2, 3]

    def test_context_id_unique(self):
        c1 = AgentContext("a")
        c2 = AgentContext("a")
        assert c1.context_id != c2.context_id

    def test_history_tracked(self):
        ctx = AgentContext("agent1")
        ctx.set("a", 1)
        ctx.set("b", 2)
        assert len(ctx.history) == 2

    def test_isolate_preserves_history(self):
        ctx = AgentContext("agent1")
        ctx.set("x", 1)
        isolated = ctx.isolate()
        assert len(isolated.history) == 1

    def test_created_at_set(self):
        ctx = AgentContext("agent1")
        assert ctx.created_at > 0

    def test_task_id_stored(self):
        ctx = AgentContext("agent1", "task123")
        assert ctx.task_id == "task123"


# ============================================================
# Agent Profile Tests (8)
# ============================================================


class TestAgentProfile:
    """Tests for agent profiles."""

    def test_profile_creation(self):
        p = AgentProfile(AgentType.CODING)
        assert p.agent_type == AgentType.CODING

    def test_profile_defaults(self):
        p = AgentProfile(AgentType.CODING)
        assert p.max_concurrent == 3
        assert p.timeout_seconds == 300.0
        assert p.retry_limit == 3

    def test_profile_to_dict(self):
        p = AgentProfile(AgentType.CODING)
        d = p.to_dict()
        assert d["agent_type"] == "coding"

    def test_profile_registry_register(self):
        pr = ProfileRegistry()
        p = AgentProfile(AgentType.CODING)
        pr.register(AgentType.CODING, p)
        assert pr.get(AgentType.CODING) is not None

    def test_profile_registry_get_none(self):
        pr = ProfileRegistry()
        assert pr.get(AgentType.SECURITY) is None

    def test_profile_registry_list_all(self):
        pr = ProfileRegistry()
        p = AgentProfile(AgentType.CODING)
        pr.register(AgentType.CODING, p)
        all_profiles = pr.list_all()
        assert "coding" in all_profiles

    def test_profile_capabilities_mutable(self):
        p = AgentProfile(AgentType.RESEARCH)
        p.capabilities.append("web_search")
        assert "web_search" in p.capabilities

    def test_profile_specializations(self):
        p = AgentProfile(AgentType.CODING)
        p.specializations = ["python", "rust"]
        assert "python" in p.specializations


# ============================================================
# Agent Memory Tests (10)
# ============================================================


class TestAgentMemory:
    """Tests for per-agent memory."""

    def test_store_and_get(self):
        mem = AgentMemory("agent1")
        mem.store("key", "value")
        assert mem.get("key") == "value"

    def test_get_missing(self):
        mem = AgentMemory("agent1")
        assert mem.get("missing") is None

    def test_clear(self):
        mem = AgentMemory("agent1")
        mem.store("k", "v")
        mem.clear()
        assert mem.size == 0

    def test_size_property(self):
        mem = AgentMemory("agent1")
        mem.store("a", 1)
        mem.store("b", 2)
        assert mem.size == 2

    def test_get_history(self):
        mem = AgentMemory("agent1")
        mem.store("x", 1)
        history = mem.get_history()
        assert len(history) == 1
        assert history[0]["key"] == "x"

    def test_export(self):
        mem = AgentMemory("agent1")
        mem.store("x", 42)
        data = mem.export()
        assert data["agent_id"] == "agent1"
        assert data["store"]["x"] == 42

    def test_import_state(self):
        mem = AgentMemory("agent1")
        mem.import_state({"store": {"a": 1}, "history": []})
        assert mem.get("a") == 1

    def test_overwrite_value(self):
        mem = AgentMemory("agent1")
        mem.store("x", 1)
        mem.store("x", 2)
        assert mem.get("x") == 2

    def test_history_after_clear(self):
        mem = AgentMemory("agent1")
        mem.store("x", 1)
        mem.clear()
        assert mem.get_history() == []

    def test_export_empty(self):
        mem = AgentMemory("agent1")
        data = mem.export()
        assert data["store"] == {}


# ============================================================
# Agent Router / Selector Tests (12)
# ============================================================


class TestAgentRouterSelector:
    """Tests for agent routing and selection."""

    def test_route_empty_registry(self):
        reg = AgentRegistry()
        router = AgentRouter(reg)
        assert router.route("do something") == []

    def test_route_finds_agents(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING, capabilities=["python"])
        reg.register(agent)
        router = AgentRouter(reg)
        results = router.route("write python", required_capabilities=["python"])
        assert len(results) == 1

    def test_route_single(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING, capabilities=["python"])
        reg.register(agent)
        router = AgentRouter(reg)
        result = router.route_single("task")
        assert result is not None

    def test_route_single_empty(self):
        reg = AgentRegistry()
        router = AgentRouter(reg)
        assert router.route_single("task") is None

    def test_route_scores_agents(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING, capabilities=["python", "rust"])
        a2 = Agent(name="a2", agent_type=AgentType.CODING, capabilities=["python"])
        reg.register(a1)
        reg.register(a2)
        router = AgentRouter(reg)
        results = router.route("code", required_capabilities=["python", "rust"])
        assert results[0].agent_id == a1.agent_id

    def test_score_agent_no_caps(self):
        reg = AgentRegistry()
        router = AgentRouter(reg)
        agent = Agent(name="a", agent_type=AgentType.CODING)
        assert router._score_agent(agent, []) == 0.0

    def test_selector_select_best(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING, capabilities=["python"])
        reg.register(agent)
        selector = AgentSelector(reg)
        results = selector.select_best("python")
        assert len(results) == 1

    def test_selector_select_best_empty(self):
        reg = AgentRegistry()
        selector = AgentSelector(reg)
        assert selector.select_best("python") == []

    def test_selector_select_team(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING, capabilities=["python"])
        a2 = Agent(name="a2", agent_type=AgentType.RESEARCH, capabilities=["search"])
        reg.register(a1)
        reg.register(a2)
        selector = AgentSelector(reg)
        team = selector.select_team(["python", "search"])
        assert len(team) == 2

    def test_selector_select_team_partial(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING, capabilities=["python"])
        reg.register(a1)
        selector = AgentSelector(reg)
        team = selector.select_team(["python", "unknown"])
        assert len(team) == 1

    def test_selector_rank_prefers_idle(self):
        reg = AgentRegistry()
        a1 = Agent(
            name="a1", agent_type=AgentType.CODING, capabilities=["python"], state=AgentState.IDLE
        )
        a2 = Agent(
            name="a2",
            agent_type=AgentType.CODING,
            capabilities=["python"],
            state=AgentState.CREATED,
        )
        reg.register(a1)
        reg.register(a2)
        selector = AgentSelector(reg)
        results = selector.select_best("python", count=2)
        assert results[0].state == AgentState.IDLE

    def test_route_excludes_running_agents(self):
        reg = AgentRegistry()
        agent = Agent(
            name="a", agent_type=AgentType.CODING, capabilities=["python"], state=AgentState.RUNNING
        )
        reg.register(agent)
        router = AgentRouter(reg)
        results = router.route("task", required_capabilities=["python"])
        assert len(results) == 0


# ============================================================
# Agent Coordinator Modes Tests (15)
# ============================================================


class TestAgentCoordinator:
    """Tests for multi-agent coordination."""

    @pytest.mark.asyncio
    async def test_coordinate_parallel(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        plan = CoordinationPlan(mode=CoordinationMode.PARALLEL, agents=[a1.agent_id], tasks=["t1"])
        tasks = [AgentTask(description="t1")]
        result = await coord.coordinate(plan, tasks)
        assert result["mode"] == "parallel"

    @pytest.mark.asyncio
    async def test_coordinate_sequential(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        plan = CoordinationPlan(
            mode=CoordinationMode.SEQUENTIAL, agents=[a1.agent_id], tasks=["t1"]
        )
        tasks = [AgentTask(description="t1")]
        result = await coord.coordinate(plan, tasks)
        assert result["mode"] == "sequential"

    @pytest.mark.asyncio
    async def test_coordinate_consensus(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        a2 = Agent(name="a2", agent_type=AgentType.RESEARCH)
        reg.register(a1)
        reg.register(a2)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        plan = CoordinationPlan(mode=CoordinationMode.CONSENSUS, agents=[a1.agent_id, a2.agent_id])
        tasks = [AgentTask(description="decide")]
        result = await coord.coordinate(plan, tasks)
        assert result["consensus_reached"] is True

    @pytest.mark.asyncio
    async def test_parallel_distributes_tasks(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        a2 = Agent(name="a2", agent_type=AgentType.RESEARCH)
        reg.register(a1)
        reg.register(a2)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        tasks = [AgentTask(description="t1"), AgentTask(description="t2")]
        results = await coord.coordinate_parallel([a1, a2], tasks)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_sequential_uses_first_agent(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        tasks = [AgentTask(description="t1")]
        results = await coord.coordinate_sequential([a1], tasks)
        assert results[0]["agent_id"] == a1.agent_id

    @pytest.mark.asyncio
    async def test_consensus_threshold(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        result = await coord.coordinate_consensus([a1], [], threshold=0.5)
        assert result["consensus_reached"] is True

    @pytest.mark.asyncio
    async def test_coordinate_empty_agents(self):
        reg = AgentRegistry()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        plan = CoordinationPlan(mode=CoordinationMode.PARALLEL, agents=[], tasks=[])
        tasks = []
        result = await coord.coordinate(plan, tasks)
        assert "results" in result

    @pytest.mark.asyncio
    async def test_coordinate_default_mode(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        plan = CoordinationPlan(mode=CoordinationMode.SINGLE, agents=[a1.agent_id])
        tasks = [AgentTask(description="t")]
        result = await coord.coordinate(plan, tasks)
        assert "results" in result

    @pytest.mark.asyncio
    async def test_parallel_empty_tasks(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        results = await coord.coordinate_parallel([a1], [])
        assert results == []

    @pytest.mark.asyncio
    async def test_sequential_empty_tasks(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        results = await coord.coordinate_sequential([a1], [])
        assert results == []

    @pytest.mark.asyncio
    async def test_parallel_multiple_agents(self):
        reg = AgentRegistry()
        agents = [Agent(name=f"a{i}", agent_type=AgentType.CODING) for i in range(5)]
        for a in agents:
            reg.register(a)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        tasks = [AgentTask(description=f"t{i}") for i in range(5)]
        results = await coord.coordinate_parallel(agents, tasks)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_plan_id_in_result(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        plan = CoordinationPlan(mode=CoordinationMode.PARALLEL, agents=[a1.agent_id])
        result = await coord.coordinate(plan, [])
        assert result["plan_id"] == plan.plan_id

    @pytest.mark.asyncio
    async def test_coordinate_updates_task_state(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        task = AgentTask(description="t1")
        await coord.coordinate_parallel([a1], [task])
        assert task.state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_consensus_result_has_threshold(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        result = await coord.coordinate_consensus([a1], [], threshold=0.9)
        assert result["result"]["threshold"] == 0.9

    @pytest.mark.asyncio
    async def test_coordinate_hierarchical_defaults_sequential(self):
        reg = AgentRegistry()
        a1 = Agent(name="a1", agent_type=AgentType.CODING)
        reg.register(a1)
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coord = AgentCoordinator(reg, scheduler, negotiator)
        plan = CoordinationPlan(mode=CoordinationMode.HIERARCHICAL, agents=[a1.agent_id])
        result = await coord.coordinate(plan, [AgentTask(description="t")])
        assert "results" in result


# ============================================================
# Agent Negotiator / Consensus Tests (12)
# ============================================================


class TestAgentNegotiator:
    """Tests for agent negotiation and consensus."""

    @pytest.mark.asyncio
    async def test_negotiate_picks_agent(self):
        neg = AgentNegotiator()
        agents = [Agent(name="a", agent_type=AgentType.CODING)]
        task = AgentTask(description="code")
        winner = await neg.negotiate(agents, task)
        assert winner.agent_id == agents[0].agent_id

    @pytest.mark.asyncio
    async def test_negotiate_empty_raises(self):
        neg = AgentNegotiator()
        with pytest.raises(ValueError):
            await neg.negotiate([], AgentTask(description="x"))

    @pytest.mark.asyncio
    async def test_vote_all_approve(self):
        neg = AgentNegotiator()
        agents = [Agent(name=f"a{i}", agent_type=AgentType.CODING) for i in range(3)]
        result = await neg.vote(agents, {"action": "deploy"})
        assert result["agreement"] == 1.0

    @pytest.mark.asyncio
    async def test_reach_consensus_above_threshold(self):
        neg = AgentNegotiator()
        votes = [{"approve": True}, {"approve": True}, {"approve": False}]
        reached, result = await neg.reach_consensus(votes, threshold=0.6)
        assert reached is True

    @pytest.mark.asyncio
    async def test_reach_consensus_below_threshold(self):
        neg = AgentNegotiator()
        votes = [{"approve": False}, {"approve": False}, {"approve": True}]
        reached, result = await neg.reach_consensus(votes, threshold=0.8)
        assert reached is False

    @pytest.mark.asyncio
    async def test_calculate_agreement_all_approve(self):
        neg = AgentNegotiator()
        votes = [{"approve": True}, {"approve": True}]
        assert neg._calculate_agreement(votes) == 1.0

    @pytest.mark.asyncio
    async def test_calculate_agreement_empty(self):
        neg = AgentNegotiator()
        assert neg._calculate_agreement([]) == 0.0

    @pytest.mark.asyncio
    async def test_negotiate_multiple_agents(self):
        neg = AgentNegotiator()
        agents = [
            Agent(name="a1", agent_type=AgentType.CODING, priority=AgentPriority.HIGH),
            Agent(name="a2", agent_type=AgentType.CODING, priority=AgentPriority.LOW),
        ]
        task = AgentTask(description="code")
        winner = await neg.negotiate(agents, task)
        assert winner is not None

    @pytest.mark.asyncio
    async def test_vote_returns_proposal(self):
        neg = AgentNegotiator()
        agents = [Agent(name="a", agent_type=AgentType.CODING)]
        result = await neg.vote(agents, {"x": 1})
        assert result["proposal"] == {"x": 1}

    @pytest.mark.asyncio
    async def test_consensus_result_structure(self):
        neg = AgentNegotiator()
        votes = [{"approve": True}]
        reached, result = await neg.reach_consensus(votes)
        assert "agreement" in result
        assert "threshold" in result
        assert "reached" in result

    @pytest.mark.asyncio
    async def test_consensus_default_threshold(self):
        neg = AgentNegotiator()
        votes = [{"approve": True}]
        reached, result = await neg.reach_consensus(votes)
        assert result["threshold"] == 0.7

    @pytest.mark.asyncio
    async def test_negotiate_history_recorded(self):
        neg = AgentNegotiator()
        agents = [Agent(name="a", agent_type=AgentType.CODING)]
        task = AgentTask(description="code")
        await neg.negotiate(agents, task)
        assert len(neg._negotiation_history) == 1


# ============================================================
# Agent Delegator Tests (10)
# ============================================================


class TestAgentDelegator:
    """Tests for task delegation."""

    @pytest.mark.asyncio
    async def test_delegate_basic(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        reg.register(agent)
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        task = AgentTask(description="code")
        result = await delegator.delegate(task)
        assert result.agent_id == agent.agent_id

    @pytest.mark.asyncio
    async def test_delegate_no_agents(self):
        reg = AgentRegistry()
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        task = AgentTask(description="code")
        with pytest.raises(DelegationError):
            await delegator.delegate(task)

    @pytest.mark.asyncio
    async def test_delegate_unknown_strategy(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        reg.register(agent)
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        task = AgentTask(description="code")
        with pytest.raises(DelegationError):
            await delegator.delegate(task, strategy="unknown")

    @pytest.mark.asyncio
    async def test_delegate_to_team(self):
        reg = AgentRegistry()
        for i in range(5):
            reg.register(Agent(name=f"a{i}", agent_type=AgentType.CODING))
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        task = AgentTask(description="code")
        team = await delegator.delegate_to_team(task, team_size=3)
        assert len(team) == 3

    @pytest.mark.asyncio
    async def test_delegate_to_team_empty(self):
        reg = AgentRegistry()
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        task = AgentTask(description="code")
        with pytest.raises(DelegationError):
            await delegator.delegate_to_team(task)

    @pytest.mark.asyncio
    async def test_delegate_sets_agent_id(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        reg.register(agent)
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        task = AgentTask(description="code")
        await delegator.delegate(task)
        assert task.agent_id == agent.agent_id

    @pytest.mark.asyncio
    async def test_delegate_best_match(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING, capabilities=["python"])
        reg.register(agent)
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        task = AgentTask(description="write python")
        result = await delegator.delegate(task, strategy="best_match")
        assert result is not None

    @pytest.mark.asyncio
    async def test_delegate_round_robin(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        reg.register(agent)
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        task = AgentTask(description="code")
        result = await delegator.delegate(task, strategy="round_robin")
        assert result is not None

    @pytest.mark.asyncio
    async def test_delegate_team_size_larger_than_available(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        reg.register(agent)
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        task = AgentTask(description="code")
        team = await delegator.delegate_to_team(task, team_size=10)
        assert len(team) == 1

    @pytest.mark.asyncio
    async def test_delegate_strategies_dict(self):
        reg = AgentRegistry()
        router = AgentRouter(reg)
        selector = AgentSelector(reg)
        delegator = AgentDelegator(reg, router, selector)
        assert "best_match" in delegator._strategies


# ============================================================
# Agent Executor Tests (12)
# ============================================================


class TestAgentExecutor:
    """Tests for agent task execution."""

    @pytest.mark.asyncio
    async def test_execute_basic(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        task = AgentTask(description="code")
        ctx = AgentContext(agent.agent_id)
        result = await executor.execute(agent, task, ctx)
        assert result.state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_sets_result(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        task = AgentTask(description="code")
        ctx = AgentContext(agent.agent_id)
        result = await executor.execute(agent, task, ctx)
        assert result.result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_sets_completed_at(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        task = AgentTask(description="code")
        ctx = AgentContext(agent.agent_id)
        result = await executor.execute(agent, task, ctx)
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_batch(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agents_tasks = [
            (
                Agent(name=f"a{i}", agent_type=AgentType.CODING, state=AgentState.ASSIGNED),
                AgentTask(description=f"t{i}"),
            )
            for i in range(3)
        ]
        results = await executor.execute_batch(agents_tasks)
        assert len(results) == 3
        assert all(r.state == AgentState.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_execute_batch_empty(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        results = await executor.execute_batch([])
        assert results == []

    @pytest.mark.asyncio
    async def test_execute_transitions_agent(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        task = AgentTask(description="code")
        ctx = AgentContext(agent.agent_id)
        await executor.execute(agent, task, ctx)
        assert agent.state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_context_has_start_time(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        task = AgentTask(description="code")
        ctx = AgentContext(agent.agent_id)
        await executor.execute(agent, task, ctx)
        assert ctx.get("start_time") is not None

    @pytest.mark.asyncio
    async def test_execute_result_has_agent_id(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        task = AgentTask(description="code")
        ctx = AgentContext(agent.agent_id)
        result = await executor.execute(agent, task, ctx)
        assert result.result["agent_id"] == agent.agent_id

    @pytest.mark.asyncio
    async def test_execute_multiple_sequential(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        for i in range(5):
            agent = Agent(name=f"a{i}", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
            task = AgentTask(description=f"t{i}")
            ctx = AgentContext(agent.agent_id)
            result = await executor.execute(agent, task, ctx)
            assert result.state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_preserves_task_id(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        task = AgentTask(description="code")
        original_id = task.task_id
        ctx = AgentContext(agent.agent_id)
        result = await executor.execute(agent, task, ctx)
        assert result.task_id == original_id

    @pytest.mark.asyncio
    async def test_execute_preserves_description(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        task = AgentTask(description="my task")
        ctx = AgentContext(agent.agent_id)
        result = await executor.execute(agent, task, ctx)
        assert result.description == "my task"

    @pytest.mark.asyncio
    async def test_execute_batch_different_types(self):
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        assignments = [
            (
                Agent(name="coder", agent_type=AgentType.CODING, state=AgentState.ASSIGNED),
                AgentTask(description="code"),
            ),
            (
                Agent(name="researcher", agent_type=AgentType.RESEARCH, state=AgentState.ASSIGNED),
                AgentTask(description="research"),
            ),
        ]
        results = await executor.execute_batch(assignments)
        assert len(results) == 2


# ============================================================
# Agent Recovery / Checkpoint Tests (12)
# ============================================================


class TestAgentRecoveryCheckpoint:
    """Tests for agent recovery and checkpointing."""

    @pytest.mark.asyncio
    async def test_recover_agent(self):
        recovery = AgentRecovery()
        result = await recovery.recover("agent1", "timeout")
        assert result is True

    @pytest.mark.asyncio
    async def test_recover_task(self):
        recovery = AgentRecovery()
        task = AgentTask(description="t", state=AgentState.FAILED)
        result = await recovery.recover_task(task)
        assert result is not None
        assert result.state == AgentState.CREATED

    @pytest.mark.asyncio
    async def test_recover_task_not_failed(self):
        recovery = AgentRecovery()
        task = AgentTask(description="t", state=AgentState.COMPLETED)
        result = await recovery.recover_task(task)
        assert result is None

    def test_add_recovery_strategy(self):
        recovery = AgentRecovery()
        recovery.add_recovery_strategy(AgentType.CODING, lambda: None)
        assert AgentType.CODING in recovery._strategies

    @pytest.mark.asyncio
    async def test_recovery_log(self):
        recovery = AgentRecovery()
        await recovery.recover("agent1", "error")
        assert len(recovery._recovery_log) == 1

    def test_checkpoint_create(self):
        cp = AgentCheckpoint()
        cid = cp.create("agent1", {"state": "running"})
        assert cid is not None

    def test_checkpoint_restore(self):
        cp = AgentCheckpoint()
        cid = cp.create("agent1", {"x": 42})
        state = cp.restore(cid)
        assert state == {"x": 42}

    def test_checkpoint_restore_nonexistent(self):
        cp = AgentCheckpoint()
        assert cp.restore("fake") is None

    def test_checkpoint_list_for_agent(self):
        cp = AgentCheckpoint()
        cp.create("agent1", {"a": 1})
        cp.create("agent1", {"b": 2})
        cp.create("agent2", {"c": 3})
        ids = cp.list_for_agent("agent1")
        assert len(ids) == 2

    def test_checkpoint_list_empty(self):
        cp = AgentCheckpoint()
        assert cp.list_for_agent("nobody") == []

    @pytest.mark.asyncio
    async def test_recover_resets_task_result(self):
        recovery = AgentRecovery()
        task = AgentTask(description="t", state=AgentState.FAILED, result={"error": "bad"})
        result = await recovery.recover_task(task)
        assert result.result == {}

    def test_checkpoint_multiple_agents(self):
        cp = AgentCheckpoint()
        c1 = cp.create("a1", {"s": 1})
        c2 = cp.create("a2", {"s": 2})
        assert cp.restore(c1) == {"s": 1}
        assert cp.restore(c2) == {"s": 2}


# ============================================================
# Agent Metrics / Telemetry Tests (10)
# ============================================================


class TestAgentMetricsTelemetry:
    """Tests for agent metrics and telemetry."""

    def test_record_task(self):
        m = AgentMetrics()
        m.record_task("a1", 100.0, True)
        stats = m.get_agent_stats("a1")
        assert stats["total"] == 1

    def test_agent_stats_empty(self):
        m = AgentMetrics()
        stats = m.get_agent_stats("unknown")
        assert stats["total"] == 0

    def test_global_stats(self):
        m = AgentMetrics()
        m.record_task("a1", 50.0, True)
        m.record_task("a2", 100.0, False)
        stats = m.get_global_stats()
        assert stats["total_tasks"] == 2
        assert stats["total_successes"] == 1

    def test_throughput(self):
        m = AgentMetrics()
        m.record_task("a1", 50.0, True)
        throughput = m.get_throughput()
        assert throughput >= 0.0

    def test_telemetry_emit(self):
        t = AgentTelemetry()
        event = AgentEvent(event_type=AgentEventType.CREATED, agent_id="a1")
        t.emit(event)
        events = t.get_events()
        assert len(events) == 1

    def test_telemetry_filter_by_agent(self):
        t = AgentTelemetry()
        t.emit(AgentEvent(event_type=AgentEventType.CREATED, agent_id="a1"))
        t.emit(AgentEvent(event_type=AgentEventType.CREATED, agent_id="a2"))
        events = t.get_events(agent_id="a1")
        assert len(events) == 1

    def test_telemetry_limit(self):
        t = AgentTelemetry()
        for _i in range(150):
            t.emit(AgentEvent(event_type=AgentEventType.STARTED, agent_id="a1"))
        events = t.get_events(limit=50)
        assert len(events) == 50

    def test_telemetry_summary(self):
        t = AgentTelemetry()
        t.emit(AgentEvent(event_type=AgentEventType.CREATED, agent_id="a1"))
        t.emit(AgentEvent(event_type=AgentEventType.COMPLETED, agent_id="a1"))
        summary = t.get_summary()
        assert summary["total_events"] == 2

    def test_metrics_avg_duration(self):
        m = AgentMetrics()
        m.record_task("a1", 100.0, True)
        m.record_task("a1", 200.0, True)
        stats = m.get_agent_stats("a1")
        assert stats["avg_duration_ms"] == 150.0

    def test_metrics_failures_counted(self):
        m = AgentMetrics()
        m.record_task("a1", 50.0, False)
        m.record_task("a1", 50.0, False)
        stats = m.get_agent_stats("a1")
        assert stats["failures"] == 2


# ============================================================
# Agent Permissions / Policies / Security Tests (15)
# ============================================================


class TestAgentPermissionsPoliciesSecurity:
    """Tests for permissions, policies, and security."""

    def test_grant_permission(self):
        p = AgentPermissions()
        p.grant("a1", Permission.READ)
        assert p.has_permission("a1", Permission.READ)

    def test_revoke_permission(self):
        p = AgentPermissions()
        p.grant("a1", Permission.READ)
        p.revoke("a1", Permission.READ)
        assert not p.has_permission("a1", Permission.READ)

    def test_has_permission_false(self):
        p = AgentPermissions()
        assert not p.has_permission("a1", Permission.ADMIN)

    def test_get_permissions(self):
        p = AgentPermissions()
        p.grant("a1", Permission.READ)
        p.grant("a1", Permission.WRITE)
        perms = p.get_permissions("a1")
        assert Permission.READ in perms
        assert Permission.WRITE in perms

    def test_get_permissions_empty(self):
        p = AgentPermissions()
        perms = p.get_permissions("unknown")
        assert perms == set()

    def test_policy_defaults(self):
        policy = AgentPolicy()
        assert policy.max_concurrent_tasks == 5
        assert policy.timeout_seconds == 300.0
        assert policy.allow_delegation is True

    def test_policy_engine_set_get(self):
        engine = PolicyEngine()
        policy = AgentPolicy(timeout_seconds=60.0)
        engine.set_policy(AgentType.CODING, policy)
        retrieved = engine.get_policy(AgentType.CODING)
        assert retrieved.timeout_seconds == 60.0

    def test_policy_engine_default(self):
        engine = PolicyEngine()
        policy = engine.get_policy(AgentType.CUSTOM)
        assert policy.max_concurrent_tasks == 5

    def test_policy_enforce_delegation(self):
        engine = PolicyEngine()
        policy = AgentPolicy(allow_delegation=False)
        engine.set_policy(AgentType.CODING, policy)
        agent = Agent(name="a", agent_type=AgentType.CODING)
        assert engine.enforce(agent, "delegate") is False

    def test_policy_enforce_network(self):
        engine = PolicyEngine()
        policy = AgentPolicy(allow_network=False)
        engine.set_policy(AgentType.CODING, policy)
        agent = Agent(name="a", agent_type=AgentType.CODING)
        assert engine.enforce(agent, "network") is False

    def test_policy_enforce_allowed(self):
        engine = PolicyEngine()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        assert engine.enforce(agent, "execute") is True

    def test_security_validate_action(self):
        perms = AgentPermissions()
        perms.grant("a1", Permission.EXECUTE)
        engine = PolicyEngine()
        sec = AgentSecurity(perms, engine)
        assert sec.validate_action("a1", "execute") is True

    def test_security_validate_action_denied(self):
        perms = AgentPermissions()
        engine = PolicyEngine()
        sec = AgentSecurity(perms, engine)
        assert sec.validate_action("a1", "execute") is False

    def test_security_validate_delegation(self):
        perms = AgentPermissions()
        perms.grant("a1", Permission.DELEGATE)
        engine = PolicyEngine()
        sec = AgentSecurity(perms, engine)
        assert sec.validate_delegation("a1", "a2") is True

    def test_security_validate_message(self):
        perms = AgentPermissions()
        perms.grant("a1", Permission.WRITE)
        engine = PolicyEngine()
        sec = AgentSecurity(perms, engine)
        msg = AgentMessage(source="a1", destination="a2")
        assert sec.validate_message(msg) is True


# ============================================================
# Agent Capability Mapper Tests (5)
# ============================================================


class TestAgentCapabilityMapper:
    """Tests for capability mapping."""

    def test_map_to_agent_type(self):
        mapper = AgentCapabilityMapper()
        assert mapper.map_to_agent_type("code_generation") == AgentType.CODING

    def test_map_to_agent_type_unknown(self):
        mapper = AgentCapabilityMapper()
        assert mapper.map_to_agent_type("teleportation") is None

    def test_map_from_agent(self):
        mapper = AgentCapabilityMapper()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        caps = mapper.map_from_agent(agent)
        assert "code_generation" in caps
        assert "debugging" in caps

    def test_register_mapping(self):
        mapper = AgentCapabilityMapper()
        mapper.register_mapping("flying", AgentType.CUSTOM)
        assert mapper.map_to_agent_type("flying") == AgentType.CUSTOM

    def test_map_from_agent_research(self):
        mapper = AgentCapabilityMapper()
        agent = Agent(name="r", agent_type=AgentType.RESEARCH)
        caps = mapper.map_from_agent(agent)
        assert "search" in caps


# ============================================================
# Agent Runtime Bridge Tests (8)
# ============================================================


class TestAgentRuntimeBridge:
    """Tests for the runtime bridge."""

    @pytest.mark.asyncio
    async def test_submit_to_runtime(self):
        from agents.agent_runtime_bridge import AgentRuntimeBridge
        from runtime.runtime_engine import RuntimeEngine

        bridge = AgentRuntimeBridge(engine=RuntimeEngine())
        task = AgentTask(description="run workflow", agent_id="a1")
        wf_id = await bridge.submit_to_runtime(task)
        assert wf_id is not None
        assert len(wf_id) > 0

    @pytest.mark.asyncio
    async def test_get_workflow_status(self):
        from agents.agent_runtime_bridge import AgentRuntimeBridge
        from runtime.runtime_engine import RuntimeEngine

        bridge = AgentRuntimeBridge(engine=RuntimeEngine())
        task = AgentTask(description="test", agent_id="a1")
        wf_id = await bridge.submit_to_runtime(task)
        status = await bridge.get_workflow_status(wf_id)
        assert status["workflow_id"] == wf_id

    @pytest.mark.asyncio
    async def test_get_workflow_status_not_found(self):
        from agents.agent_runtime_bridge import AgentRuntimeBridge
        from runtime.runtime_engine import RuntimeEngine

        bridge = AgentRuntimeBridge(engine=RuntimeEngine())
        status = await bridge.get_workflow_status("fake-id")
        assert status["state"] == "not_found"

    @pytest.mark.asyncio
    async def test_cancel_workflow(self):
        from agents.agent_runtime_bridge import AgentRuntimeBridge
        from runtime.runtime_engine import RuntimeEngine

        bridge = AgentRuntimeBridge(engine=RuntimeEngine())
        task = AgentTask(description="test", agent_id="a1")
        wf_id = await bridge.submit_to_runtime(task)
        result = await bridge.cancel_workflow(wf_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_workflow(self):
        from agents.agent_runtime_bridge import AgentRuntimeBridge
        from runtime.runtime_engine import RuntimeEngine

        bridge = AgentRuntimeBridge(engine=RuntimeEngine())
        result = await bridge.cancel_workflow("fake")
        assert result is False

    @pytest.mark.asyncio
    async def test_submit_creates_workflow(self):
        from agents.agent_runtime_bridge import AgentRuntimeBridge
        from runtime.runtime_engine import RuntimeEngine

        bridge = AgentRuntimeBridge(engine=RuntimeEngine())
        task = AgentTask(description="my task", agent_id="a1")
        wf_id = await bridge.submit_to_runtime(task)
        status = await bridge.get_workflow_status(wf_id)
        assert status["state"] != "not_found"

    @pytest.mark.asyncio
    async def test_cancel_after_cancel(self):
        from agents.agent_runtime_bridge import AgentRuntimeBridge
        from runtime.runtime_engine import RuntimeEngine

        bridge = AgentRuntimeBridge(engine=RuntimeEngine())
        task = AgentTask(description="test", agent_id="a1")
        wf_id = await bridge.submit_to_runtime(task)
        await bridge.cancel_workflow(wf_id)
        result = await bridge.cancel_workflow(wf_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_submit_multiple(self):
        from agents.agent_runtime_bridge import AgentRuntimeBridge
        from runtime.runtime_engine import RuntimeEngine

        bridge = AgentRuntimeBridge(engine=RuntimeEngine())
        t1 = AgentTask(description="task1", agent_id="a1")
        t2 = AgentTask(description="task2", agent_id="a2")
        wf1 = await bridge.submit_to_runtime(t1)
        wf2 = await bridge.submit_to_runtime(t2)
        assert wf1 != wf2


# ============================================================
# Integration Tests (10)
# ============================================================


class TestIntegration:
    """Integration tests for the multi-agent system."""

    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        agent = await mgr.create_agent("coder", AgentType.CODING)
        task = await mgr.assign_task(agent.agent_id, "write code")
        ctx = AgentContext(agent.agent_id, task.task_id)
        result = await executor.execute(agent, task, ctx)
        assert result.state == AgentState.COMPLETED
        await mgr.terminate_agent(agent.agent_id)
        assert registry.count == 0

    @pytest.mark.asyncio
    async def test_team_creation_and_coordination(self):
        registry = AgentRegistry()
        factory = AgentFactory()
        scheduler = AgentScheduler()
        negotiator = AgentNegotiator()
        coordinator = AgentCoordinator(registry, scheduler, negotiator)
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle)
        supervisor = AgentSupervisor()
        mgr = AgentManager(registry, factory, coordinator, executor, supervisor)
        a1 = await mgr.create_agent("planner", AgentType.PLANNER)
        a2 = await mgr.create_agent("coder", AgentType.CODING)
        plan = CoordinationPlan(
            mode=CoordinationMode.PARALLEL,
            agents=[a1.agent_id, a2.agent_id],
            tasks=["plan", "code"],
        )
        result = await mgr.execute_plan(plan)
        assert result["mode"] == "parallel"

    @pytest.mark.asyncio
    async def test_delegation_with_router(self):
        registry = AgentRegistry()
        agent = Agent(name="coder", agent_type=AgentType.CODING, capabilities=["python"])
        registry.register(agent)
        router = AgentRouter(registry)
        selector = AgentSelector(registry)
        delegator = AgentDelegator(registry, router, selector)
        task = AgentTask(description="write python")
        result = await delegator.delegate(task)
        assert result.agent_id == agent.agent_id

    @pytest.mark.asyncio
    async def test_recovery_after_failure(self):
        recovery = AgentRecovery()
        task = AgentTask(description="failed task", state=AgentState.FAILED)
        recovered = await recovery.recover_task(task)
        assert recovered is not None
        assert recovered.state == AgentState.CREATED

    @pytest.mark.asyncio
    async def test_checkpoint_and_restore(self):
        cp = AgentCheckpoint()
        ctx = AgentContext("agent1")
        ctx.set("progress", 50)
        cid = cp.create("agent1", ctx.snapshot())
        state = cp.restore(cid)
        new_ctx = AgentContext("agent1")
        new_ctx.restore(state)
        assert new_ctx.get("progress") == 50

    @pytest.mark.asyncio
    async def test_security_blocks_unauthorized(self):
        perms = AgentPermissions()
        engine = PolicyEngine()
        sec = AgentSecurity(perms, engine)
        assert sec.validate_action("attacker", "admin") is False

    @pytest.mark.asyncio
    async def test_metrics_after_execution(self):
        metrics = AgentMetrics()
        lc = AgentLifecycle()
        executor = AgentExecutor(lc)
        agent = Agent(name="a", agent_type=AgentType.CODING, state=AgentState.ASSIGNED)
        task = AgentTask(description="code")
        ctx = AgentContext(agent.agent_id)
        await executor.execute(agent, task, ctx)
        metrics.record_task(agent.agent_id, 100.0, True)
        stats = metrics.get_agent_stats(agent.agent_id)
        assert stats["total"] == 1

    @pytest.mark.asyncio
    async def test_telemetry_events_emitted(self):
        telemetry = AgentTelemetry()
        event = AgentEvent(event_type=AgentEventType.TASK_COMPLETED, agent_id="a1")
        telemetry.emit(event)
        summary = telemetry.get_summary()
        assert summary["total_events"] == 1

    @pytest.mark.asyncio
    async def test_supervisor_and_monitor(self):
        supervisor = AgentSupervisor()
        monitor = AgentMonitor()
        task = AgentTask(description="supervised task")
        await supervisor.supervise("agent1", task)
        monitor.record_start("agent1", task.task_id)
        assert "agent1" in supervisor.get_supervised()
        assert "agent1" in monitor.get_active()

    @pytest.mark.asyncio
    async def test_scheduler_assigns_task(self):
        reg = AgentRegistry()
        agent = Agent(name="a", agent_type=AgentType.CODING)
        reg.register(agent)
        scheduler = AgentScheduler()
        task = AgentTask(description="work")
        agent_id = scheduler.schedule(task, [agent])
        assert agent_id == agent.agent_id
        assert task.agent_id == agent.agent_id
