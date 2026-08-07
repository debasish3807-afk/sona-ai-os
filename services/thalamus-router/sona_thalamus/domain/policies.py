"""Routing policies and rules.

Policies define conditions under which routing decisions are modified,
blocked, or redirected. They enable configurable governance over the
routing layer.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class PolicyAction(StrEnum):
    """Actions that a routing policy can prescribe."""

    ALLOW = "allow"
    DENY = "deny"
    REDIRECT = "redirect"
    REQUIRE_APPROVAL = "require_approval"
    RATE_LIMIT = "rate_limit"


@dataclass(frozen=True)
class RoutingPolicy:
    """A single routing policy rule.

    Attributes:
        name: Human-readable policy name.
        condition: Expression describing when this policy applies.
        action: The action to take when the condition matches.
        target: Redirect target (used when action is REDIRECT).
        priority: Evaluation priority (lower = evaluated first).
        metadata: Additional policy metadata.
    """

    name: str
    condition: str
    action: PolicyAction
    target: str | None = None
    priority: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyEvaluation:
    """Result of evaluating a single policy against a request.

    Attributes:
        policy_name: Name of the evaluated policy.
        action: The action determined by evaluation.
        matched: Whether the policy condition matched.
        reason: Explanation of why the policy matched or didn't.
    """

    policy_name: str
    action: PolicyAction
    matched: bool
    reason: str = ""
