"""Capability Composer — compose capabilities into pipelines."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from capabilities.exceptions import CapabilityNotFoundError
from capabilities.registry import CapabilityRegistry
from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ComposedCapability:
    """A composed pipeline of multiple capabilities."""

    composition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mode: str = "sequential"
    capabilities: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "composition_id": self.composition_id,
            "mode": self.mode,
            "capabilities": self.capabilities,
            "created_at": self.created_at,
        }


class CapabilityComposer:
    """Composes capabilities into sequential, parallel, or conditional pipelines."""

    def compose_sequential(
        self, capability_ids: list[str], registry: CapabilityRegistry
    ) -> ComposedCapability:
        """Compose capabilities to execute in sequence.

        Args:
            capability_ids: Ordered list of capability IDs.
            registry: The capability registry.

        Returns:
            A ComposedCapability in sequential mode.

        Raises:
            CapabilityNotFoundError: If any capability is not registered.
        """
        self._validate_ids(capability_ids, registry)
        composed = ComposedCapability(mode="sequential", capabilities=capability_ids)
        logger.info("composed_sequential", count=len(capability_ids))
        return composed

    def compose_parallel(
        self, capability_ids: list[str], registry: CapabilityRegistry
    ) -> ComposedCapability:
        """Compose capabilities to execute in parallel.

        Args:
            capability_ids: List of capability IDs to run concurrently.
            registry: The capability registry.

        Returns:
            A ComposedCapability in parallel mode.

        Raises:
            CapabilityNotFoundError: If any capability is not registered.
        """
        self._validate_ids(capability_ids, registry)
        composed = ComposedCapability(mode="parallel", capabilities=capability_ids)
        logger.info("composed_parallel", count=len(capability_ids))
        return composed

    def compose_conditional(
        self, conditions: list[tuple[str, str]], registry: CapabilityRegistry
    ) -> ComposedCapability:
        """Compose capabilities with conditional execution.

        Args:
            conditions: List of (condition_expr, capability_id) tuples.
            registry: The capability registry.

        Returns:
            A ComposedCapability in conditional mode.

        Raises:
            CapabilityNotFoundError: If any capability is not registered.
        """
        cap_ids = [cap_id for _, cap_id in conditions]
        self._validate_ids(cap_ids, registry)
        composed = ComposedCapability(mode="conditional", capabilities=cap_ids)
        logger.info("composed_conditional", count=len(conditions))
        return composed

    def _validate_ids(self, capability_ids: list[str], registry: CapabilityRegistry) -> None:
        """Validate that all capability IDs exist in the registry."""
        for cap_id in capability_ids:
            if not registry.has(cap_id):
                raise CapabilityNotFoundError(cap_id)
