"""Microkernel schemas — core data types for the microkernel runtime."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any


class KernelStatus(str, Enum):
    """Lifecycle status of the microkernel."""

    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"


class MessagePriority(IntEnum):
    """Priority levels for IPC messages."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class ProcessState(str, Enum):
    """Lifecycle state of a supervised process."""

    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    CRASHED = "crashed"
    RECOVERING = "recovering"


class SandboxType(str, Enum):
    """Types of sandboxed execution environments."""

    TERMINAL = "terminal"
    PYTHON = "python"
    FILESYSTEM = "filesystem"
    BROWSER = "browser"
    DOCKER = "docker"
    PLUGIN = "plugin"


@dataclass
class IPCMessage:
    """Inter-process communication message."""

    source: str
    destination: str
    payload: dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = ""
    request_id: str = ""
    timestamp: float = field(default_factory=time.time)
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"
    ttl_seconds: float = 30.0
    acknowledged: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "priority": int(self.priority),
            "source": self.source,
            "destination": self.destination,
            "payload": self.payload,
            "metadata": self.metadata,
            "version": self.version,
            "ttl_seconds": self.ttl_seconds,
            "acknowledged": self.acknowledged,
        }


@dataclass
class ServiceInfo:
    """Metadata for a registered microkernel service."""

    service_id: str
    name: str
    version: str
    registered_at: float
    last_heartbeat: float
    status: str = "active"
    capabilities: list[str] = field(default_factory=list)
    health: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "service_id": self.service_id,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "capabilities": self.capabilities,
            "health": self.health,
            "registered_at": self.registered_at,
            "last_heartbeat": self.last_heartbeat,
        }


@dataclass
class ResourceBudget:
    """Resource limits for a process or allocation."""

    cpu_percent: float = 100.0
    memory_mb: int = 512
    gpu_percent: float = 0.0
    disk_mb: int = 1024
    network_mbps: float = 100.0
    token_budget: int = 100000
    timeout_seconds: float = 300.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "gpu_percent": self.gpu_percent,
            "disk_mb": self.disk_mb,
            "network_mbps": self.network_mbps,
            "token_budget": self.token_budget,
            "timeout_seconds": self.timeout_seconds,
        }
