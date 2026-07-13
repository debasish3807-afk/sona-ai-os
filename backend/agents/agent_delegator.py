"""Task delegation to agents."""

from __future__ import annotations

from agents.agent_registry import AgentRegistry
from agents.agent_router import AgentRouter
from agents.agent_selector import AgentSelector
from agents.exceptions import DelegationError
from agents.schemas import Agent, AgentTask
from config.logging import get_logger

logger = get_logger(__name__)


class AgentDelegator:
    """Delegates tasks to appropriate agents."""

    def __init__(
        self,
        registry: AgentRegistry,
        router: AgentRouter,
        selector: AgentSelector,
    ) -> None:
        self._registry = registry
        self._router = router
        self._selector = selector
        self._strategies: dict[str, str] = {
            "best_match": "route",
            "team": "select_team",
            "round_robin": "route",
        }

    async def delegate(self, task: AgentTask, strategy: str = "best_match") -> Agent:
        """Delegate a task to the best agent using the given strategy."""
        if strategy not in self._strategies:
            raise DelegationError(f"Unknown strategy: {strategy}")

        candidates = self._router.route(task.description)
        if not candidates:
            raise DelegationError("No agents available for delegation")

        selected = candidates[0]
        task.agent_id = selected.agent_id
        logger.info(
            "task_delegated",
            task_id=task.task_id,
            agent_id=selected.agent_id,
            strategy=strategy,
        )
        return selected

    async def delegate_to_team(self, task: AgentTask, team_size: int = 3) -> list[Agent]:
        """Delegate a task to a team of agents."""
        candidates = self._router.route(task.description)
        team = candidates[:team_size]
        if not team:
            raise DelegationError("No agents available for team delegation")
        logger.info("task_delegated_to_team", task_id=task.task_id, team_size=len(team))
        return team
