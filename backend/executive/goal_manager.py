"""Executive Intelligence layer — goal lifecycle management."""

from __future__ import annotations

import time

from config.logging import get_logger
from executive.exceptions import GoalError
from executive.schemas import Goal, GoalPriority, GoalState

logger = get_logger(__name__)


class GoalManager:
    """Manages creation, tracking, and lifecycle of goals."""

    def __init__(self) -> None:
        self._goals: dict[str, Goal] = {}
        self._completion_times: list[float] = []

    def create_goal(
        self,
        title: str,
        description: str,
        priority: GoalPriority = GoalPriority.MEDIUM,
        parent_id: str | None = None,
        dependencies: list[str] | None = None,
        success_criteria: list[str] | None = None,
        deadline: float | None = None,
        metadata: dict | None = None,
    ) -> Goal:
        """Create a new goal and register it."""
        goal = Goal(
            title=title,
            description=description,
            priority=priority,
            parent_id=parent_id,
            dependencies=dependencies or [],
            success_criteria=success_criteria or [],
            deadline=deadline,
            metadata=metadata or {},
        )
        self._goals[goal.goal_id] = goal
        logger.info("goal_created", goal_id=goal.goal_id, title=title)
        return goal

    def update_goal(self, goal_id: str, **updates: object) -> Goal:
        """Update goal fields. Raises GoalError if not found."""
        goal = self._goals.get(goal_id)
        if goal is None:
            raise GoalError(f"Goal not found: {goal_id}")
        for key, value in updates.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
        goal.updated_at = time.time()
        return goal

    def get_goal(self, goal_id: str) -> Goal | None:
        """Retrieve a goal by ID."""
        return self._goals.get(goal_id)

    def list_goals(
        self, state: GoalState | None = None, priority: GoalPriority | None = None
    ) -> list[Goal]:
        """List goals with optional state and priority filters."""
        results: list[Goal] = []
        for goal in self._goals.values():
            if state is not None and goal.state != state:
                continue
            if priority is not None and goal.priority != priority:
                continue
            results.append(goal)
        return results

    def complete_goal(self, goal_id: str) -> bool:
        """Mark a goal as completed."""
        goal = self._goals.get(goal_id)
        if goal is None:
            return False
        goal.state = GoalState.COMPLETED
        goal.progress = 1.0
        goal.updated_at = time.time()
        elapsed = goal.updated_at - goal.created_at
        self._completion_times.append(elapsed)
        logger.info("goal_completed", goal_id=goal_id)
        return True

    def fail_goal(self, goal_id: str, reason: str) -> bool:
        """Mark a goal as failed."""
        goal = self._goals.get(goal_id)
        if goal is None:
            return False
        goal.state = GoalState.FAILED
        goal.metadata["failure_reason"] = reason
        goal.updated_at = time.time()
        logger.warning("goal_failed", goal_id=goal_id, reason=reason)
        return True

    def cancel_goal(self, goal_id: str) -> bool:
        """Cancel a goal."""
        goal = self._goals.get(goal_id)
        if goal is None:
            return False
        goal.state = GoalState.CANCELLED
        goal.updated_at = time.time()
        logger.info("goal_cancelled", goal_id=goal_id)
        return True

    def split_goal(self, goal_id: str, sub_goals: list[dict]) -> list[Goal]:
        """Split a goal into sub-goals."""
        parent = self._goals.get(goal_id)
        if parent is None:
            raise GoalError(f"Goal not found: {goal_id}")
        created: list[Goal] = []
        for sg_data in sub_goals:
            child = self.create_goal(
                title=sg_data.get("title", "Sub-goal"),
                description=sg_data.get("description", ""),
                priority=parent.priority,
                parent_id=goal_id,
            )
            parent.sub_goals.append(child.goal_id)
            created.append(child)
        parent.updated_at = time.time()
        return created

    def merge_goals(self, goal_ids: list[str], merged_title: str) -> Goal:
        """Merge multiple goals into a single goal."""
        descriptions: list[str] = []
        for gid in goal_ids:
            goal = self._goals.get(gid)
            if goal is None:
                raise GoalError(f"Goal not found: {gid}")
            descriptions.append(goal.description)
            goal.state = GoalState.MERGED
            goal.updated_at = time.time()

        merged = self.create_goal(
            title=merged_title,
            description=" | ".join(descriptions),
            metadata={"merged_from": goal_ids},
        )
        return merged

    def get_metrics(self) -> dict:
        """Return goal management metrics."""
        by_state: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        for goal in self._goals.values():
            by_state[goal.state.value] = by_state.get(goal.state.value, 0) + 1
            by_priority[goal.priority.value] = by_priority.get(goal.priority.value, 0) + 1

        avg_completion = (
            sum(self._completion_times) / len(self._completion_times)
            if self._completion_times
            else 0.0
        )
        return {
            "total": len(self._goals),
            "by_state": by_state,
            "by_priority": by_priority,
            "avg_completion_time": avg_completion,
        }
