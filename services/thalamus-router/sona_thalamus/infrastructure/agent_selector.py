"""Agent selection logic for THALAMUS routing.

Determines which agents (if any) should handle a request based on
intent classification, task complexity, and content signals.
"""

import structlog

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.task_classifier import TaskClassification, TaskType

logger = structlog.get_logger(__name__)

# Intent to default agent mapping
_INTENT_AGENTS: dict[IntentCategory, list[str]] = {
    IntentCategory.CODE: ["coding_agent"],
    IntentCategory.RESEARCH: ["research_agent"],
    IntentCategory.AUTOMATION: ["workflow_agent"],
    IntentCategory.MEMORY: [],
    IntentCategory.SYSTEM: [],
    IntentCategory.CHAT: [],
}

# Task types that trigger additional agents
_TASK_AGENTS: dict[TaskType, list[str]] = {
    TaskType.COMPOSITE: ["planner_agent"],
    TaskType.ANALYTICAL: ["reasoning_agent"],
    TaskType.CREATIVE: ["creative_agent"],
    TaskType.TECHNICAL: ["coding_agent"],
    TaskType.RESEARCH: ["research_agent"],
    TaskType.SIMPLE: [],
}


class AgentSelector:
    """Selects agents needed to handle a request.

    Combines intent-based defaults with task complexity analysis
    to determine the optimal set of agents for delegation.
    """

    def __init__(self, complexity_threshold: float = 0.5) -> None:
        """Initialize the agent selector.

        Args:
            complexity_threshold: Minimum complexity to add planner agent.
        """
        self._complexity_threshold = complexity_threshold

    def select(
        self,
        intent: IntentCategory,
        task: TaskClassification,
    ) -> list[str]:
        """Select agents needed for the given request.

        Args:
            intent: The classified intent category.
            task: The task classification result.

        Returns:
            List of agent type names that should handle the request.
        """
        agents: set[str] = set()

        # Add intent-based default agents
        intent_agents = _INTENT_AGENTS.get(intent, [])
        agents.update(intent_agents)

        # Add task-type-based agents
        task_agents = _TASK_AGENTS.get(task.task_type, [])
        agents.update(task_agents)

        # Add planner agent for complex tasks
        if task.complexity_score >= self._complexity_threshold:
            agents.add("planner_agent")

        result = sorted(agents)

        logger.debug(
            "agents_selected",
            intent=str(intent),
            task_type=str(task.task_type),
            complexity=task.complexity_score,
            agents=result,
        )

        return result
