"""Task routing for AI kernel.

Routes incoming tasks to the appropriate handlers, agents, or
providers based on task type, capabilities, and routing rules.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from kernel.task_manager import Task, TaskType


class RouteStatus(str, Enum):
    """Result status of a routing decision."""

    ROUTED = "routed"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"
    BLOCKED = "blocked"


# Type alias for route handler functions
RouteHandler = Callable[[Task], Coroutine[Any, Any, dict[str, Any]]]


@dataclass
class RouteRule:
    """A routing rule that maps tasks to handlers.

    Attributes:
        rule_id: Unique rule identifier.
        name: Human-readable rule name.
        task_types: Task types this rule applies to.
        handler_id: Identifier of the target handler.
        priority: Rule evaluation priority (lower = first).
        condition: Optional condition function for dynamic matching.
        enabled: Whether this rule is active.
        metadata: Additional rule metadata.
    """

    name: str
    handler_id: str
    task_types: list[TaskType] = field(default_factory=list)
    rule_id: str = field(default_factory=lambda: str(uuid4()))
    priority: int = 50
    condition: Callable[[Task], bool] | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteDecision:
    """Result of a routing decision.

    Attributes:
        status: Whether routing succeeded.
        handler_id: Selected handler identifier.
        rule_id: The rule that matched.
        reason: Explanation of the routing decision.
        alternatives: Alternative handlers considered.
        metadata: Additional routing metadata.
    """

    status: RouteStatus
    handler_id: str | None = None
    rule_id: str | None = None
    reason: str = ""
    alternatives: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskRouter(ABC):
    """Abstract interface for task routing.

    Evaluates incoming tasks against registered rules and
    determines the appropriate handler for execution.
    """

    @abstractmethod
    async def route(self, task: Task) -> RouteDecision:
        """Route a task to the appropriate handler.

        Evaluates all applicable rules in priority order
        and returns the routing decision.

        Args:
            task: The task to route.

        Returns:
            RouteDecision with the selected handler.
        """
        ...

    @abstractmethod
    async def register_rule(self, rule: RouteRule) -> str:
        """Register a new routing rule.

        Args:
            rule: The routing rule to register.

        Returns:
            The rule_id of the registered rule.

        Raises:
            ValueError: If a rule with the same ID exists.
        """
        ...

    @abstractmethod
    async def unregister_rule(self, rule_id: str) -> bool:
        """Remove a routing rule.

        Args:
            rule_id: The rule to remove.

        Returns:
            True if the rule was found and removed.
        """
        ...

    @abstractmethod
    async def register_handler(
        self,
        handler_id: str,
        handler: RouteHandler,
    ) -> None:
        """Register a task handler.

        Args:
            handler_id: Unique identifier for the handler.
            handler: Async callable that processes tasks.

        Raises:
            ValueError: If a handler with the same ID exists.
        """
        ...

    @abstractmethod
    async def unregister_handler(self, handler_id: str) -> bool:
        """Remove a registered handler.

        Args:
            handler_id: The handler to remove.

        Returns:
            True if the handler was found and removed.
        """
        ...

    @abstractmethod
    async def execute(self, task: Task) -> dict[str, Any]:
        """Route and execute a task.

        Combines routing with execution: finds the appropriate
        handler and invokes it with the task.

        Args:
            task: The task to route and execute.

        Returns:
            Execution result from the handler.

        Raises:
            ValueError: If no suitable handler is found.
        """
        ...

    @abstractmethod
    def list_rules(self) -> list[RouteRule]:
        """List all registered routing rules.

        Returns:
            List of active routing rules.
        """
        ...

    @abstractmethod
    def list_handlers(self) -> list[str]:
        """List all registered handler IDs.

        Returns:
            List of handler identifier strings.
        """
        ...
