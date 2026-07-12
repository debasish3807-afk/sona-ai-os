"""Agent capability system.

Defines capabilities that agents can declare and the matching
system for routing tasks to the most appropriate agent.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentCapability(str, Enum):
    """Capabilities an agent may support."""

    # Core capabilities
    CHAT = "chat"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"

    # Specialized capabilities
    PLANNING = "planning"
    AUTOMATION = "automation"
    WEB_BROWSING = "web_browsing"
    FILE_OPERATIONS = "file_operations"
    DATABASE_QUERY = "database_query"
    API_INTERACTION = "api_interaction"

    # Domain capabilities
    SECURITY_AUDIT = "security_audit"
    MEMORY_MANAGEMENT = "memory_management"
    VOICE_PROCESSING = "voice_processing"
    VISION_PROCESSING = "vision_processing"
    ANDROID_DEVELOPMENT = "android_development"
    WEB_DEVELOPMENT = "web_development"

    # Coordination
    TASK_DELEGATION = "task_delegation"
    MULTI_STEP_REASONING = "multi_step_reasoning"
    TOOL_USE = "tool_use"
    VERIFICATION = "verification"


class CapabilityLevel(str, Enum):
    """Proficiency level for a capability."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass(frozen=True)
class AgentCapabilityDescriptor:
    """Detailed descriptor for an agent capability.

    Attributes:
        capability: The capability identifier.
        level: Proficiency level.
        description: Human-readable description.
        constraints: Limitations or conditions.
        metadata: Additional metadata.
    """

    capability: AgentCapability
    level: CapabilityLevel = CapabilityLevel.BASIC
    description: str = ""
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapabilitySet:
    """Set of capabilities declared by an agent.

    Attributes:
        agent_id: The agent these capabilities belong to.
        capabilities: List of capability descriptors.
    """

    agent_id: str
    capabilities: list[AgentCapabilityDescriptor] = field(default_factory=list)

    @property
    def capability_names(self) -> set[AgentCapability]:
        """Get the set of capability identifiers."""
        return {cap.capability for cap in self.capabilities}

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if a specific capability is present."""
        return capability in self.capability_names

    def has_all(self, required: list[AgentCapability]) -> bool:
        """Check if all required capabilities are present."""
        return all(self.has_capability(c) for c in required)

    def has_any(self, capabilities: list[AgentCapability]) -> bool:
        """Check if any of the given capabilities are present."""
        return any(self.has_capability(c) for c in capabilities)

    def get_descriptor(self, capability: AgentCapability) -> AgentCapabilityDescriptor | None:
        """Get the descriptor for a specific capability."""
        for desc in self.capabilities:
            if desc.capability == capability:
                return desc
        return None

    def match_score(self, required: list[AgentCapability]) -> float:
        """Calculate match score against requirements (0.0 to 1.0)."""
        if not required:
            return 1.0
        matched = sum(1 for c in required if self.has_capability(c))
        return matched / len(required)


@dataclass
class CapabilityRequirement:
    """Requirements for agent capability matching.

    Attributes:
        required: Capabilities that must be present.
        preferred: Nice-to-have capabilities.
        min_level: Minimum proficiency level.
        metadata: Additional requirement context.
    """

    required: list[AgentCapability] = field(default_factory=list)
    preferred: list[AgentCapability] = field(default_factory=list)
    min_level: CapabilityLevel = CapabilityLevel.BASIC
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_satisfied_by(self, capability_set: AgentCapabilitySet) -> bool:
        """Check if a capability set satisfies these requirements."""
        return capability_set.has_all(self.required)

    def score(self, capability_set: AgentCapabilitySet) -> float:
        """Score a capability set (0.0 to 1.0)."""
        if not self.is_satisfied_by(capability_set):
            return 0.0
        base = 0.7
        if self.preferred:
            pref_score = capability_set.match_score(self.preferred)
            return base + (0.3 * pref_score)
        return base
