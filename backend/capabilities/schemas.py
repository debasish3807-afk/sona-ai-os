"""Capability schemas — data models for the Dynamic Capability Fabric."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class CapabilityCategory(str, Enum):
    """Classification of capability types."""

    TOOL = "tool"
    PROVIDER = "provider"
    INTEGRATION = "integration"
    ENGINE = "engine"
    PLUGIN = "plugin"
    WORKFLOW = "workflow"


class CapabilityState(str, Enum):
    """Lifecycle states for a capability."""

    DISCOVERED = "discovered"
    REGISTERED = "registered"
    VALIDATED = "validated"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UPGRADING = "upgrading"
    DISABLED = "disabled"
    UNLOADED = "unloaded"
    REMOVED = "removed"


@dataclass
class Capability:
    """Core data model for a registered capability."""

    name: str
    version: str
    description: str
    author: str
    category: CapabilityCategory
    entrypoint: str
    capability_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    cost: float = 0.0
    latency_ms: float = 0.0
    confidence: float = 1.0
    priority: int = 50
    health_status: str = "healthy"
    resource_requirements: dict[str, Any] = field(default_factory=dict)
    supported_models: list[str] = field(default_factory=list)
    supported_platforms: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize capability to dictionary."""
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category.value,
            "entrypoint": self.entrypoint,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "permissions": self.permissions,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "confidence": self.confidence,
            "priority": self.priority,
            "health_status": self.health_status,
            "resource_requirements": self.resource_requirements,
            "supported_models": self.supported_models,
            "supported_platforms": self.supported_platforms,
            "metadata": self.metadata,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }
