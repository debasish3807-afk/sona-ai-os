"""Provider capability system.

Defines capabilities that providers can declare and the system
for querying and matching capabilities during provider selection.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Capability(str, Enum):
    """Individual capabilities a provider may support."""

    # Core capabilities
    CHAT_COMPLETION = "chat_completion"
    TEXT_COMPLETION = "text_completion"
    STREAMING = "streaming"
    EMBEDDINGS = "embeddings"

    # Advanced capabilities
    FUNCTION_CALLING = "function_calling"
    TOOL_USE = "tool_use"
    VISION = "vision"
    JSON_MODE = "json_mode"
    CODE_GENERATION = "code_generation"
    LONG_CONTEXT = "long_context"

    # Specialized capabilities
    IMAGE_GENERATION = "image_generation"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    TEXT_TO_SPEECH = "text_to_speech"
    MULTI_MODAL = "multi_modal"

    # Operational capabilities
    BATCH_PROCESSING = "batch_processing"
    FINE_TUNING = "fine_tuning"
    CACHING = "caching"


class CapabilityLevel(str, Enum):
    """Proficiency level for a capability."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass(frozen=True)
class CapabilityDescriptor:
    """Detailed description of a single capability.

    Attributes:
        capability: The capability identifier.
        level: Proficiency level.
        version: Capability version (for evolving features).
        constraints: Limitations or constraints on the capability.
        metadata: Additional capability metadata.
    """

    capability: Capability
    level: CapabilityLevel = CapabilityLevel.BASIC
    version: str = "1.0"
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilitySet:
    """A set of capabilities declared by a provider.

    Provides methods for querying and matching against requirements.

    Attributes:
        provider_id: The provider these capabilities belong to.
        capabilities: Set of capability descriptors.
        metadata: Additional metadata.
    """

    provider_id: str
    capabilities: list[CapabilityDescriptor] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def capability_names(self) -> set[Capability]:
        """Get the set of capability identifiers."""
        return {cap.capability for cap in self.capabilities}

    def has_capability(self, capability: Capability) -> bool:
        """Check if a specific capability is present.

        Args:
            capability: The capability to check.

        Returns:
            True if the capability is declared.
        """
        return capability in self.capability_names

    def has_all(self, required: list[Capability]) -> bool:
        """Check if all required capabilities are present.

        Args:
            required: List of required capabilities.

        Returns:
            True if all required capabilities are declared.
        """
        return all(self.has_capability(cap) for cap in required)

    def has_any(self, capabilities: list[Capability]) -> bool:
        """Check if any of the given capabilities are present.

        Args:
            capabilities: List of capabilities to check.

        Returns:
            True if at least one capability is declared.
        """
        return any(self.has_capability(cap) for cap in capabilities)

    def get_descriptor(self, capability: Capability) -> CapabilityDescriptor | None:
        """Get the full descriptor for a capability.

        Args:
            capability: The capability to look up.

        Returns:
            CapabilityDescriptor or None if not found.
        """
        for desc in self.capabilities:
            if desc.capability == capability:
                return desc
        return None

    def match_score(self, required: list[Capability]) -> float:
        """Calculate a match score against requirements.

        Returns a score between 0.0 and 1.0 indicating how well
        this capability set matches the requirements.

        Args:
            required: Required capabilities.

        Returns:
            Match score (0.0 = no match, 1.0 = full match).
        """
        if not required:
            return 1.0
        matched = sum(1 for cap in required if self.has_capability(cap))
        return matched / len(required)


@dataclass
class CapabilityRequirement:
    """A set of capability requirements for provider selection.

    Attributes:
        required: Capabilities that must be present.
        preferred: Capabilities that are nice to have.
        excluded: Capabilities that must NOT be present.
        min_level: Minimum capability level required.
        metadata: Additional requirement context.
    """

    required: list[Capability] = field(default_factory=list)
    preferred: list[Capability] = field(default_factory=list)
    excluded: list[Capability] = field(default_factory=list)
    min_level: CapabilityLevel = CapabilityLevel.BASIC
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_satisfied_by(self, capability_set: CapabilitySet) -> bool:
        """Check if a capability set satisfies these requirements.

        Args:
            capability_set: The capabilities to check against.

        Returns:
            True if all required capabilities are met and no
            excluded capabilities are present.
        """
        # Check all required are present
        if not capability_set.has_all(self.required):
            return False

        # Check no excluded are present
        return all(not capability_set.has_capability(excluded) for excluded in self.excluded)

    def score(self, capability_set: CapabilitySet) -> float:
        """Score a capability set against these requirements.

        Considers both required and preferred capabilities.

        Args:
            capability_set: The capabilities to score.

        Returns:
            Score from 0.0 to 1.0.
        """
        if not self.is_satisfied_by(capability_set):
            return 0.0

        # Base score for meeting requirements
        base_score = 0.7

        # Bonus for preferred capabilities
        if self.preferred:
            preferred_score = capability_set.match_score(self.preferred)
            return base_score + (0.3 * preferred_score)

        return base_score
