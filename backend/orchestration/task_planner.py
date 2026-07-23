"""Multi-Agent Task Planner — goal decomposition, dependency graphs, dynamic planning."""

from __future__ import annotations

import time
import uuid

from config.logging import get_logger
from orchestration.schemas import Plan, PlanStatus, PlanStep

logger = get_logger(__name__)


class TaskPlanner:
    def __init__(self) -> None:
        self._plans: dict[str, Plan] = {}

    def create_plan(self, goal: str, owner: str = "") -> Plan:
        plan = Plan(
            plan_id=str(uuid.uuid4()),
            goal=goal,
            status=PlanStatus.PENDING,
            created_at=time.time(),
            owner=owner,
        )
        self._plans[plan.plan_id] = plan
        return plan

    def decompose(self, plan_id: str, steps: list[PlanStep]) -> Plan | None:
        plan = self._plans.get(plan_id)
        if plan is None:
            return None
        plan.steps = sorted(steps, key=lambda s: s.priority)
        return plan

    def get_next_steps(self, plan_id: str) -> list[PlanStep]:
        plan = self._plans.get(plan_id)
        if not plan or plan.status == PlanStatus.COMPLETED:
            return []
        ready = []
        for step in plan.steps:
            if step.status != PlanStatus.PENDING:
                continue
            if all(self._is_step_completed(plan, dep) for dep in step.depends_on):
                ready.append(step)
        return sorted(ready, key=lambda s: s.priority)

    def mark_step(self, plan_id: str, step_id: str, status: PlanStatus) -> None:
        plan = self._plans.get(plan_id)
        if plan:
            for s in plan.steps:
                if s.step_id == step_id:
                    s.status = status
                    break
            if all(s.status == PlanStatus.COMPLETED for s in plan.steps):
                plan.status = PlanStatus.COMPLETED
            elif any(s.status == PlanStatus.FAILED for s in plan.steps):
                plan.status = PlanStatus.FAILED

    def re_plan(self, plan_id: str, failed_step: str, alternative: PlanStep) -> Plan | None:
        plan = self._plans.get(plan_id)
        if plan:
            plan.steps = [s for s in plan.steps if s.step_id != failed_step]
            plan.steps.append(alternative)
            plan.status = PlanStatus.PENDING
        return plan

    def get_plan(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    def list_plans(self) -> list[Plan]:
        return sorted(self._plans.values(), key=lambda p: p.created_at, reverse=True)

    @staticmethod
    def _is_step_completed(plan: Plan, step_id: str) -> bool:
        for s in plan.steps:
            if s.step_id == step_id:
                return s.status in (PlanStatus.COMPLETED, PlanStatus.CANCELLED)
        return True

    def get_stats(self) -> dict[str, int]:
        total = len(self._plans)
        completed = sum(1 for p in self._plans.values() if p.status == PlanStatus.COMPLETED)
        return {"total": total, "completed": completed, "active": total - completed}
