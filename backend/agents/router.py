"""Agent task routing.

Routes incoming tasks to the most appropriate agent based on
capabilities, availability, priority, and custom routing rules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from agents.base import BaseAgent
from agents.capabilities import AgentCapability, CapabilityRequirement
from agents.context import ExecutionContext


class RouteStrategy(str, Enum):
    """Strategies for agent selection."""

    BEST_MATCH = "best_match"
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    PRIORITY = "priority"
    RANDOM = "random"


class RouteOutcome(str, Enum):
    """Result of a routing decision."""

    ROUTED = "routed"
    NO_MATCH = "no_match"
    ALL_BUSY = "all_busy"
    BLOCKED = "blocked"


@dataclass
class RouteRule:
    """A rule for routing tasks to agents.

    Attributes:
        rule_id: Unique rule identifier.
        name: Human-readable rule name.
        target_agent_id: Target agent (or None for capability match).
        capabilities: Required capabilities.
        condition: Optional dynamic condition function.
        priority: Rule evaluation priority.
        enabled: Whether this rule is active.
    """

    name: str
    rule_id: str = field(default_factory=lambda: str(uuid4()))
    target_agent_id: Optional[str] = None
    capabilities: List[AgentCapability] = field(default_factory=list)
    condition: Optional[Callable[[ExecutionContext], bool]] = None
    priority: int = 50
    enabled: bool = True


@dataclass
class RouteDecision:
    """Result of a routing evaluation.

    Attributes:
        outcome: Whether routing succeeded.
        agent: The selected agent (if routed).
        rule_id: The rule that matched.
        alternatives: Other agents considered.
        reason: Explanation for the decision.
        metadata: Additional routing metadata.
    """

    outcome: RouteOutcome
    agent: Optional[BaseAgent] = None
    rule_id: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)



class AgentRouter(ABC):
    """Abstract interface for agent task routing.

    Evaluates tasks against routing rules and selects the optimal
    agent for execution.
    """

    @abstractmethod
    async def route(self, context: ExecutionContext) -> RouteDecision:
        """Route a task to the best agent.

        Args:
            context: The execution context to route.

        Returns:
            RouteDecision with the selected agent.
        """
        ...

    @abstractmethod
    async def route_with_requirements(
        self,
        context: ExecutionContext,
        requirement: CapabilityRequirement,
    ) -> RouteDecision:
        """Route with explicit capability requirements.

        Args:
            context: The execution context.
            requirement: Capability requirements.

        Returns:
            RouteDecision with the selected agent.
        """
        ...

    @abstractmethod
    async def add_rule(self, rule: RouteRule) -> str:
        """Add a routing rule.

        Args:
            rule: The rule to add.

        Returns:
            The rule_id.
        """
        ...

    @abstractmethod
    async def remove_rule(self, rule_id: str) -> bool:
        """Remove a routing rule.

        Args:
            rule_id: The rule to remove.

        Returns:
            True if found and removed.
        """
        ...

    @abstractmethod
    def list_rules(self) -> List[RouteRule]:
        """List all active routing rules."""
        ...

    @abstractmethod
    async def set_strategy(self, strategy: RouteStrategy) -> None:
        """Set the default routing strategy.

        Args:
            strategy: The selection strategy.
        """
        ...

    @abstractmethod
    async def get_candidates(
        self, context: ExecutionContext
    ) -> List[BaseAgent]:
        """Get all candidate agents for a task (without selecting).

        Args:
            context: The execution context.

        Returns:
            List of candidate agents.
        """
        ...
