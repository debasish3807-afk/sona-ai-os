"""Goal Manager — long-running goals, progress tracking, pause/resume."""

from __future__ import annotations

import time
import uuid

from config.logging import get_logger
from orchestration.schemas import Goal, GoalStatus

logger = get_logger(__name__)


class GoalManager:
    def __init__(self) -> None:
        self._goals: dict[str, Goal] = {}

    def create_goal(self, title: str, description: str = "", plan_id: str = "") -> Goal:
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            title=title,
            description=description,
            status=GoalStatus.ACTIVE,
            created_at=time.time(),
            plan_id=plan_id,
        )
        self._goals[goal.goal_id] = goal
        return goal

    def get_goal(self, goal_id: str) -> Goal | None:
        return self._goals.get(goal_id)

    def list_goals(self, status: GoalStatus | None = None) -> list[Goal]:
        goals = list(self._goals.values())
        if status:
            goals = [g for g in goals if g.status == status]
        return sorted(goals, key=lambda g: g.created_at, reverse=True)

    def update_progress(self, goal_id: str, progress: float) -> Goal | None:
        goal = self._goals.get(goal_id)
        if goal:
            goal.progress = max(0.0, min(1.0, progress))
        return goal

    def complete_goal(self, goal_id: str) -> bool:
        goal = self._goals.get(goal_id)
        if goal:
            goal.status = GoalStatus.COMPLETED
            goal.progress = 1.0
            return True
        return False

    def fail_goal(self, goal_id: str) -> bool:
        goal = self._goals.get(goal_id)
        if goal:
            goal.status = GoalStatus.FAILED
            return True
        return False

    def pause_goal(self, goal_id: str) -> bool:
        goal = self._goals.get(goal_id)
        if goal and goal.status == GoalStatus.ACTIVE:
            goal.status = GoalStatus.PAUSED
            return True
        return False

    def resume_goal(self, goal_id: str) -> bool:
        goal = self._goals.get(goal_id)
        if goal and goal.status == GoalStatus.PAUSED:
            goal.status = GoalStatus.ACTIVE
            return True
        return False

    def cancel_goal(self, goal_id: str) -> bool:
        goal = self._goals.get(goal_id)
        if goal and goal.status in (GoalStatus.ACTIVE, GoalStatus.PAUSED):
            goal.status = GoalStatus.CANCELLED
            return True
        return False

    def get_stats(self) -> dict[str, int]:
        total = len(self._goals)
        active = sum(1 for g in self._goals.values() if g.status == GoalStatus.ACTIVE)
        completed = sum(1 for g in self._goals.values() if g.status == GoalStatus.COMPLETED)
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "failed": sum(1 for g in self._goals.values() if g.status == GoalStatus.FAILED),
        }
