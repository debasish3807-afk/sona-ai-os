"""Routing policy evaluation engine.

Evaluates routing policies against incoming requests to determine
whether routing should be allowed, denied, or modified.
"""

import re

import structlog

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.domain.policies import PolicyAction, PolicyEvaluation, RoutingPolicy

logger = structlog.get_logger(__name__)

# Default policies
_DEFAULT_POLICIES: list[RoutingPolicy] = [
    RoutingPolicy(
        name="allow_all_chat",
        condition="intent == chat",
        action=PolicyAction.ALLOW,
        priority=100,
    ),
    RoutingPolicy(
        name="allow_all_research",
        condition="intent == research",
        action=PolicyAction.ALLOW,
        priority=100,
    ),
    RoutingPolicy(
        name="allow_all_code",
        condition="intent == code",
        action=PolicyAction.ALLOW,
        priority=100,
    ),
    RoutingPolicy(
        name="allow_all_memory",
        condition="intent == memory",
        action=PolicyAction.ALLOW,
        priority=100,
    ),
    RoutingPolicy(
        name="allow_all_system",
        condition="intent == system",
        action=PolicyAction.ALLOW,
        priority=100,
    ),
    RoutingPolicy(
        name="allow_all_automation",
        condition="intent == automation",
        action=PolicyAction.ALLOW,
        priority=100,
    ),
]


class PolicyEngine:
    """Evaluates routing policies against requests.

    Loads policies, evaluates their conditions against the current request,
    and returns the resulting policy actions in priority order.
    """

    def __init__(self, policies: list[RoutingPolicy] | None = None) -> None:
        """Initialize the policy engine.

        Args:
            policies: List of routing policies (uses defaults if None).
        """
        self._policies = sorted(
            policies or _DEFAULT_POLICIES,
            key=lambda p: p.priority,
        )

    def evaluate(
        self,
        intent: IntentCategory,
        content: str,
        context: dict[str, str | int | float | bool] | None = None,
    ) -> list[PolicyEvaluation]:
        """Evaluate all policies against a request.

        Args:
            intent: The classified intent category.
            content: The user input text.
            context: Optional additional context for policy evaluation.

        Returns:
            List of PolicyEvaluation results for matched policies.
        """
        evaluations: list[PolicyEvaluation] = []

        for policy in self._policies:
            matched = self._evaluate_condition(policy.condition, intent, content, context)
            if matched:
                evaluation = PolicyEvaluation(
                    policy_name=policy.name,
                    action=policy.action,
                    matched=True,
                    reason=f"Condition '{policy.condition}' matched",
                )
                evaluations.append(evaluation)

                logger.debug(
                    "policy_matched",
                    policy=policy.name,
                    action=str(policy.action),
                    intent=str(intent),
                )

        return evaluations

    def get_effective_action(
        self,
        intent: IntentCategory,
        content: str,
        context: dict[str, str | int | float | bool] | None = None,
    ) -> PolicyAction:
        """Get the highest-priority action that applies.

        Evaluates all policies and returns the action from the
        highest-priority (lowest number) matching policy.

        Args:
            intent: The classified intent category.
            content: The user input text.
            context: Optional additional context.

        Returns:
            The effective PolicyAction (ALLOW if no policies match).
        """
        evaluations = self.evaluate(intent, content, context)

        if not evaluations:
            return PolicyAction.ALLOW

        # Policies are already sorted by priority, return first match
        return evaluations[0].action

    def add_policy(self, policy: RoutingPolicy) -> None:
        """Add a policy and re-sort by priority.

        Args:
            policy: The routing policy to add.
        """
        self._policies.append(policy)
        self._policies.sort(key=lambda p: p.priority)

    def _evaluate_condition(
        self,
        condition: str,
        intent: IntentCategory,
        content: str,
        context: dict[str, str | int | float | bool] | None = None,
    ) -> bool:
        """Evaluate a policy condition expression.

        Supports simple conditions like:
        - "intent == code"
        - "intent != chat"
        - "content contains dangerous"
        - "always"

        Args:
            condition: The condition expression to evaluate.
            intent: Current intent category.
            content: Current content.
            context: Additional context variables.

        Returns:
            True if the condition matches.
        """
        condition = condition.strip().lower()

        # Always match
        if condition == "always":
            return True

        # Intent comparison: "intent == code"
        intent_match = re.match(r"intent\s*(==|!=)\s*(\w+)", condition)
        if intent_match:
            operator = intent_match.group(1)
            value = intent_match.group(2)
            if operator == "==":
                return str(intent) == value
            return str(intent) != value

        # Content contains: "content contains word"
        content_match = re.match(r"content\s+contains\s+(.+)", condition)
        if content_match:
            search_term = content_match.group(1).strip()
            return search_term.lower() in content.lower()

        # Context variable check
        if context:
            ctx_match = re.match(r"(\w+)\s*(==|!=|>|<)\s*(.+)", condition)
            if ctx_match:
                var_name = ctx_match.group(1)
                operator = ctx_match.group(2)
                value = ctx_match.group(3).strip()
                if var_name in context:
                    return self._compare(context[var_name], operator, value)

        return False

    def _compare(
        self,
        left: str | int | float | bool,
        operator: str,
        right: str,
    ) -> bool:
        """Compare two values with the given operator."""
        try:
            if isinstance(left, bool):
                right_val: str | int | float | bool = right.lower() in ("true", "1", "yes")
                return left == right_val
            if isinstance(left, int):
                right_num = int(right)
                if operator == "==":
                    return left == right_num
                if operator == "!=":
                    return left != right_num
                if operator == ">":
                    return left > right_num
                if operator == "<":
                    return left < right_num
            elif isinstance(left, float):
                right_float = float(right)
                if operator == "==":
                    return left == right_float
                if operator == "!=":
                    return left != right_float
                if operator == ">":
                    return left > right_float
                if operator == "<":
                    return left < right_float
            else:
                # String comparison
                if operator == "==":
                    return str(left) == right
                if operator == "!=":
                    return str(left) != right
        except (ValueError, TypeError):
            pass
        return False
