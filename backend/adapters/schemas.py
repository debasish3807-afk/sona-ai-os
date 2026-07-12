"""Schemas for the runtime integration layer."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ServiceStatus(Enum):
    """Lifecycle status of a runtime service."""

    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"
    RECOVERING = "recovering"


class BootPhase(Enum):
    """Phases of the boot sequence."""

    PRE_BOOT = "pre_boot"
    KERNEL_INIT = "kernel_init"
    SERVICE_DISCOVERY = "service_discovery"
    SERVICE_REGISTRATION = "service_registration"
    SERVICE_START = "service_start"
    READY = "ready"
    SHUTDOWN = "shutdown"


@dataclass
class RuntimeService:
    """Descriptor for a registered runtime service."""

    service_id: str
    name: str
    adapter_type: str
    status: ServiceStatus = ServiceStatus.REGISTERED
    priority: int = 50
    dependencies: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "service_id": self.service_id,
            "name": self.name,
            "adapter_type": self.adapter_type,
            "status": self.status.value,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "version": self.version,
            "registered_at": self.registered_at,
            "last_heartbeat": self.last_heartbeat,
            "metadata": self.metadata,
        }


@dataclass
class BootEvent:
    """Record of a boot-sequence phase transition."""

    phase: BootPhase
    message: str
    timestamp: float = field(default_factory=time.time)
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "phase": self.phase.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "success": self.success,
        }


@dataclass
class PersistenceRecord:
    """Single persistence entry."""

    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: str = ""
    key: str = ""
    value: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "record_id": self.record_id,
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
        }
