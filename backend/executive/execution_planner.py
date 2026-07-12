"""Executive Intelligence layer — execution plan creation and task graph assembly."""

from __future__ import annotations

from config.logging import get_logger
from executive.schemas import ApprovalStatus, Decision, ExecutionPlan, Goal
from executive.task_graph import TaskGraph, TaskNode

logger = get_logger(__name__)


class ExecutionPlanner:
    """Creates execution plans from decisions and builds task graphs."""

    def create_plan(self, decision: Decision, goal: Goal) -> ExecutionPlan:
        """Create a full execution plan from a decision."""
        if decision.selected is None:
            return ExecutionPlan(
                goal_id=goal.goal_id,
                strategy_id="",
                tasks=[],
                execution_mode="sequential",
            )

        strategy = decision.selected
        tasks = list(strategy.steps)
        mode = "parallel" if len(tasks) > 3 else "sequential"

        plan = ExecutionPlan(
            goal_id=goal.goal_id,
            strategy_id=strategy.strategy_id,
            tasks=tasks,
            execution_mode=mode,
            estimated_duration_ms=strategy.estimated_latency_ms,
            approval_status=ApprovalStatus.PENDING_APPROVAL,
        )
        logger.info(
            "execution_plan_created",
            plan_id=plan.plan_id,
            goal_id=goal.goal_id,
            mode=mode,
            task_count=len(tasks),
        )
        return plan

    def plan_sequential(self, steps: list[str]) -> TaskGraph:
        """Create a task graph with sequential dependencies."""
        graph = TaskGraph()
        prev_id: str | None = None
        for idx, step in enumerate(steps):
            node = TaskNode(name=step, capability_id=step, priority=idx)
            task_id = graph.add_task(node)
            if prev_id is not None:
                graph.add_dependency(task_id, prev_id)
            prev_id = task_id
        return graph

    def plan_parallel(self, steps: list[str]) -> TaskGraph:
        """Create a task graph with all tasks running in parallel."""
        graph = TaskGraph()
        for idx, step in enumerate(steps):
            node = TaskNode(name=step, capability_id=step, priority=idx)
            graph.add_task(node)
        return graph

    def plan_conditional(self, conditions: list[tuple[str, str]]) -> TaskGraph:
        """Create a task graph with conditional branching.

        Each condition is a (condition_step, action_step) pair where
        action_step depends on condition_step completing first.
        """
        graph = TaskGraph()
        for condition_step, action_step in conditions:
            cond_node = TaskNode(
                name=f"check:{condition_step}",
                capability_id=condition_step,
            )
            action_node = TaskNode(
                name=f"action:{action_step}",
                capability_id=action_step,
            )
            cond_id = graph.add_task(cond_node)
            action_id = graph.add_task(action_node)
            graph.add_dependency(action_id, cond_id)
        return graph

    def add_checkpoints(self, plan: ExecutionPlan, interval: int) -> ExecutionPlan:
        """Add checkpoint markers at regular intervals in the plan."""
        checkpoints: list[str] = []
        for idx, task in enumerate(plan.tasks):
            if (idx + 1) % interval == 0:
                checkpoints.append(f"checkpoint_after:{task}")
        plan.checkpoints = checkpoints
        return plan

    def add_rollback(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Add rollback path for recovery on failure."""
        rollback: list[str] = []
        for task in reversed(plan.tasks):
            rollback.append(f"undo:{task}")
        plan.rollback_path = rollback
        return plan
