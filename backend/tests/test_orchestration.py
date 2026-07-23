"""Tests for Phase 29: Autonomous Agent Orchestration & Task Planning Engine."""

import pytest

from orchestration.event_bus import EventBus
from orchestration.goal_manager import GoalManager
from orchestration.orchestrator import AgentOrchestrator
from orchestration.schemas import (
    AgentSpec,
    ExecutableTask,
    GoalStatus,
    PlanStatus,
    PlanStep,
    ToolDefinition,
)
from orchestration.task_planner import TaskPlanner
from orchestration.tool_orchestrator import ToolOrchestrator
from orchestration.workflow_engine import WorkflowEngine, WorkflowStep


class TestTaskPlanner:
    def test_create_plan(self):
        p = TaskPlanner()
        plan = p.create_plan("test goal")
        assert plan.goal == "test goal"
        assert plan.status == PlanStatus.PENDING

    def test_decompose_and_get_next(self):
        p = TaskPlanner()
        plan = p.create_plan("deploy")
        steps = [
            PlanStep(step_id="s1", description="build", depends_on=["s0"]),
            PlanStep(step_id="s0", description="test"),
        ]
        p.decompose(plan.plan_id, steps)
        next_steps = p.get_next_steps(plan.plan_id)
        assert len(next_steps) == 1
        assert next_steps[0].step_id == "s0"

    def test_mark_complete(self):
        p = TaskPlanner()
        plan = p.create_plan("build")
        p.decompose(plan.plan_id, [PlanStep(step_id="s1", description="build")])
        p.mark_step(plan.plan_id, "s1", PlanStatus.COMPLETED)
        assert p.get_plan(plan.plan_id).status == PlanStatus.COMPLETED

    def test_replan(self):
        p = TaskPlanner()
        plan = p.create_plan("build")
        p.decompose(plan.plan_id, [PlanStep(step_id="s1")])
        alt = PlanStep(step_id="s2", description="alt")
        p.re_plan(plan.plan_id, "s1", alt)
        assert any(s.step_id == "s2" for s in p.get_plan(plan.plan_id).steps)

    def test_stats(self):
        p = TaskPlanner()
        p.create_plan("g1")
        stats = p.get_stats()
        assert stats["total"] >= 1


class TestAgentOrchestrator:
    def test_spawn(self):
        o = AgentOrchestrator()
        aid = o.spawn(AgentSpec(agent_type="coder"))
        assert aid.startswith("coder-")

    def test_spawn_batch(self):
        o = AgentOrchestrator()
        ids = o.spawn_batch([AgentSpec(agent_type="a"), AgentSpec(agent_type="b")])
        assert len(ids) == 2

    def test_execute_task(self):
        o = AgentOrchestrator()
        task = ExecutableTask(task_id="t1", agent_type="coder")
        result = o.execute_task(task)
        assert result["status"] == "completed"

    def test_context(self):
        o = AgentOrchestrator()
        o.set_context("key", "val")
        assert o.get_context("key") == "val"


class TestToolOrchestrator:
    def test_register_and_execute(self):
        t = ToolOrchestrator()
        tid = t.register_tool(ToolDefinition(name="test", description="a tool"))
        assert tid == "test"
        result = t.execute("test", {})
        assert result["success"] is True

    def test_tool_not_found(self):
        t = ToolOrchestrator()
        result = t.execute("nonexistent", {})
        assert result["success"] is False

    def test_history(self):
        t = ToolOrchestrator()
        t.register_tool(ToolDefinition(name="ht"))
        t.execute("ht", {"a": 1})
        assert len(t.history()) == 1

    def test_stats(self):
        t = ToolOrchestrator()
        t.register_tool(ToolDefinition(name="st"))
        t.execute("st", {})
        stats = t.get_stats()
        assert stats["total"] == 1


class TestWorkflowEngine:
    def test_create_and_execute(self):
        w = WorkflowEngine()
        wf = w.create_workflow("test", [WorkflowStep(name="step1")])
        result = w.execute(wf.workflow_id)
        assert result["success"] is True

    def test_conditional_skip(self):
        w = WorkflowEngine()
        wf = w.create_workflow("cond", [WorkflowStep(name="skip", condition="0 == 1")])
        result = w.execute(wf.workflow_id)
        assert result["success"] is True
        step = w.get_workflow(wf.workflow_id).steps[0]
        assert step.status.name == "SKIPPED"


class TestGoalManager:
    def test_create_and_complete(self):
        g = GoalManager()
        goal = g.create_goal("test goal", "description")
        assert goal.title == "test goal"
        assert g.complete_goal(goal.goal_id)
        assert g.get_goal(goal.goal_id).status == GoalStatus.COMPLETED

    def test_pause_resume(self):
        g = GoalManager()
        goal = g.create_goal("pause test")
        assert g.pause_goal(goal.goal_id)
        assert g.get_goal(goal.goal_id).status == GoalStatus.PAUSED
        assert g.resume_goal(goal.goal_id)
        assert g.get_goal(goal.goal_id).status == GoalStatus.ACTIVE

    def test_progress(self):
        g = GoalManager()
        goal = g.create_goal("progress")
        g.update_progress(goal.goal_id, 0.5)
        assert g.get_goal(goal.goal_id).progress == 0.5

    def test_stats(self):
        g = GoalManager()
        g.create_goal("s1")
        g.create_goal("s2")
        assert g.get_stats()["total"] == 2


class TestEventBus:
    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        bus = EventBus()
        received = []

        async def handler(**kwargs):
            received.append(kwargs)

        bus.subscribe("test_event", handler)
        count = await bus.publish("test_event", {"data": 1})
        assert count == 1
        assert len(received) == 1

    def test_history(self):
        import asyncio

        bus = EventBus()

        async def handler(**kwargs):
            pass

        bus.subscribe("e1", handler)
        asyncio.run(bus.publish("e1"))
        assert len(bus.get_history()) == 1
