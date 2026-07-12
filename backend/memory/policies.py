"""Memory lifecycle and retention policies.

This module defines the policy framework for governing memory lifecycle,
retention, capacity management, consolidation triggers, and pinning rules.
Policies are declarative configurations that the PolicyEngine evaluates
and enforces.

Classes:
    RetentionPolicy: Rules for how long memories are retained.
    CapacityPolicy: Rules for maximum storage utilization.
    ConsolidationPolicy: Rules for when/how memories are consolidated.
    PinPolicy: Rules governing memory pinning behavior.
    MemoryPolicySet: Complete set of policies for a memory system.
    PolicyEngine: Abstract engine for evaluating and enforcing policies.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from .types import MemoryEntry, MemoryScope, MemoryType


class ExpiryAction(str, Enum):
    """Action to take when a memory reaches its retention limit.

    Attributes:
        ARCHIVE: Move to long-term archive storage.
        DELETE: Permanently remove the entry.
        CONSOLIDATE: Merge with related entries into a summary.
    """

    ARCHIVE = "archive"
    DELETE = "delete"
    CONSOLIDATE = "consolidate"


class EvictionStrategy(str, Enum):
    """Strategy for evicting entries when capacity is exceeded.

    Attributes:
        LRU: Least Recently Used - evict oldest accessed first.
        LFU: Least Frequently Used - evict least accessed first.
        IMPORTANCE: Evict lowest importance score first.
        OLDEST: Evict oldest created first.
    """

    LRU = "lru"
    LFU = "lfu"
    IMPORTANCE = "importance"
    OLDEST = "oldest"


class ConsolidationTrigger(str, Enum):
    """Condition that triggers memory consolidation.

    Attributes:
        TIME: Consolidate after a time interval elapses.
        COUNT: Consolidate when entry count exceeds threshold.
        SIZE: Consolidate when storage size exceeds threshold.
    """

    TIME = "time"
    COUNT = "count"
    SIZE = "size"


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """Defines how long memories of specific types are retained.

    A retention policy specifies the maximum age and count for memories,
    along with the action to take when limits are reached.

    Attributes:
        policy_id: Unique identifier for this policy (UUID4).
        name: Human-readable policy name.
        memory_types: Which memory types this policy applies to.
        max_age_seconds: Maximum age in seconds before expiry action.
        max_entries: Maximum number of entries before eviction.
        action: What to do when retention limits are reached.
        enabled: Whether this policy is currently active.
        priority: Policy evaluation priority (lower = evaluated first).
    """

    name: str
    memory_types: list[MemoryType]
    max_age_seconds: Optional[int] = None
    max_entries: Optional[int] = None
    action: ExpiryAction = ExpiryAction.DELETE
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    priority: int = 0


@dataclass(frozen=True, slots=True)
class CapacityPolicy:
    """Defines maximum storage capacity and eviction behavior.

    Capacity policies set upper bounds on memory utilization for specific
    scopes and define how to handle overflow.

    Attributes:
        policy_id: Unique identifier for this policy (UUID4).
        scope: The scope this capacity policy applies to.
        max_entries: Maximum number of entries allowed.
        max_size_bytes: Maximum total size in bytes allowed.
        eviction_strategy: Strategy for selecting entries to evict.
        warning_threshold: Percentage of capacity that triggers a warning (0.0-1.0).
        enabled: Whether this policy is currently active.
    """

    scope: MemoryScope
    max_entries: Optional[int] = None
    max_size_bytes: Optional[int] = None
    eviction_strategy: EvictionStrategy = EvictionStrategy.LRU
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    warning_threshold: float = 0.8
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ConsolidationPolicy:
    """Defines when and how memories should be consolidated.

    Consolidation merges multiple related memories into fewer, denser
    representations to manage growth and improve retrieval quality.

    Attributes:
        policy_id: Unique identifier for this policy (UUID4).
        trigger: The condition that triggers consolidation.
        threshold: Numeric threshold for the trigger condition.
        target_memory_type: The memory type to consolidate into.
        summarize: Whether to generate a summary during consolidation.
        source_types: Which memory types are candidates for consolidation.
        min_entries: Minimum entries required before consolidation runs.
        enabled: Whether this policy is currently active.
    """

    trigger: ConsolidationTrigger
    threshold: int
    target_memory_type: MemoryType = MemoryType.LONG_TERM
    summarize: bool = True
    source_types: list[MemoryType] = field(default_factory=lambda: [MemoryType.SHORT_TERM])
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    min_entries: int = 5
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class PinPolicy:
    """Defines rules governing memory pinning behavior.

    Pinned memories are exempt from eviction and expiration. This policy
    sets limits on pinning to prevent unbounded resource consumption.

    Attributes:
        max_pinned_per_scope: Maximum number of pinned entries per scope.
        pin_duration_seconds: Optional maximum duration a pin can last.
        allowed_memory_types: Which memory types can be pinned (None = all).
        require_min_importance: Minimum importance score required to pin.
    """

    max_pinned_per_scope: int = 100
    pin_duration_seconds: Optional[int] = None
    allowed_memory_types: Optional[list[MemoryType]] = None
    require_min_importance: float = 0.0


@dataclass(frozen=True, slots=True)
class MemoryPolicySet:
    """Complete set of policies governing a memory system instance.

    Aggregates all policy types into a single configuration object
    that can be loaded, validated, and applied by the PolicyEngine.

    Attributes:
        retention_policies: List of retention policies.
        capacity_policies: List of capacity policies.
        consolidation_policies: List of consolidation policies.
        pin_policy: The pin policy configuration.
    """

    retention_policies: list[RetentionPolicy] = field(default_factory=list)
    capacity_policies: list[CapacityPolicy] = field(default_factory=list)
    consolidation_policies: list[ConsolidationPolicy] = field(default_factory=list)
    pin_policy: PinPolicy = field(default_factory=PinPolicy)


@dataclass(frozen=True, slots=True)
class PolicyViolation:
    """Represents a detected policy violation.

    Attributes:
        policy_id: The ID of the violated policy.
        policy_name: Human-readable name of the violated policy.
        violation_type: Category of violation (retention, capacity, pin).
        message: Description of the violation.
        affected_entries: IDs of entries affected by the violation.
        detected_at: When the violation was detected.
    """

    policy_id: str
    policy_name: str
    violation_type: str
    message: str
    affected_entries: list[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PolicyEngine(ABC):
    """Abstract engine for evaluating and enforcing memory policies.

    The PolicyEngine is responsible for checking memory operations against
    configured policies, applying retention and capacity rules, and
    reporting violations.
    """

    @abstractmethod
    async def evaluate(
        self, entry: MemoryEntry, policy_set: MemoryPolicySet
    ) -> list[PolicyViolation]:
        """Evaluate a memory entry against all applicable policies.

        Args:
            entry: The memory entry to evaluate.
            policy_set: The complete set of policies to check against.

        Returns:
            List of policy violations found, empty if entry is compliant.
        """
        ...

    @abstractmethod
    async def apply_retention(
        self, policy_set: MemoryPolicySet, entries: list[MemoryEntry]
    ) -> list[str]:
        """Apply retention policies to a set of entries.

        Identifies entries that have exceeded their retention limits
        and returns their IDs for cleanup.

        Args:
            policy_set: The policies to enforce.
            entries: The entries to check.

        Returns:
            List of entry IDs that should be cleaned up.
        """
        ...

    @abstractmethod
    async def apply_capacity(
        self, policy_set: MemoryPolicySet, entries: list[MemoryEntry], scope: MemoryScope
    ) -> list[str]:
        """Apply capacity policies and identify entries for eviction.

        When capacity limits are exceeded, selects entries for eviction
        based on the configured eviction strategy.

        Args:
            policy_set: The policies to enforce.
            entries: Current entries in the scope.
            scope: The scope to check capacity for.

        Returns:
            List of entry IDs selected for eviction.
        """
        ...

    @abstractmethod
    async def check_violations(
        self, policy_set: MemoryPolicySet, entries: list[MemoryEntry]
    ) -> list[PolicyViolation]:
        """Check for any active policy violations in current state.

        Performs a comprehensive check of all policies against the
        current memory state.

        Args:
            policy_set: The policies to check.
            entries: All current entries to evaluate.

        Returns:
            List of active policy violations.
        """
        ...

    @abstractmethod
    async def get_expired(
        self, policy_set: MemoryPolicySet, entries: list[MemoryEntry]
    ) -> list[str]:
        """Get IDs of entries that have expired per retention policies.

        Args:
            policy_set: The policies defining expiration rules.
            entries: Entries to check for expiration.

        Returns:
            List of entry IDs that are past their expiration.
        """
        ...
