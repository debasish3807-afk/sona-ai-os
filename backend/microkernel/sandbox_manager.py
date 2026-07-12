"""Sandbox Manager — creates and enforces isolated execution environments."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger
from microkernel.exceptions import SandboxError
from microkernel.schemas import SandboxType

logger = get_logger(__name__)


@dataclass
class SandboxConfig:
    """Configuration for a sandbox environment."""

    sandbox_type: SandboxType
    workspace_root: str
    allowed_paths: list[str] = field(default_factory=list)
    allowed_hosts: list[str] = field(default_factory=list)
    cpu_limit: float = 100.0
    memory_limit_mb: int = 512
    timeout_seconds: float = 60.0
    network_enabled: bool = True


@dataclass
class Sandbox:
    """A sandboxed execution environment."""

    config: SandboxConfig
    sandbox_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    process_id: str = ""
    created_at: float = field(default_factory=time.time)
    active: bool = True


class SandboxManager:
    """Manages sandboxed execution environments with resource enforcement.

    Creates isolated environments for code execution, validates
    filesystem and network access, and enforces resource limits.
    """

    def __init__(self) -> None:
        self._sandboxes: dict[str, Sandbox] = {}

    def create(self, config: SandboxConfig) -> Sandbox:
        """Create a new sandbox with the given configuration."""
        sandbox = Sandbox(config=config)
        self._sandboxes[sandbox.sandbox_id] = sandbox
        logger.info(
            "sandbox_created",
            sandbox_id=sandbox.sandbox_id,
            sandbox_type=config.sandbox_type.value,
        )
        return sandbox

    def destroy(self, sandbox_id: str) -> bool:
        """Destroy a sandbox and release its resources."""
        sandbox = self._sandboxes.get(sandbox_id)
        if sandbox is None:
            return False

        sandbox.active = False
        del self._sandboxes[sandbox_id]
        logger.info("sandbox_destroyed", sandbox_id=sandbox_id)
        return True

    def get(self, sandbox_id: str) -> Sandbox | None:
        """Retrieve a sandbox by ID."""
        return self._sandboxes.get(sandbox_id)

    def list_active(self) -> list[Sandbox]:
        """List all active sandboxes."""
        return [s for s in self._sandboxes.values() if s.active]

    def validate_path(self, sandbox_id: str, path: str) -> bool:
        """Check if a path is allowed within the sandbox."""
        sandbox = self._sandboxes.get(sandbox_id)
        if sandbox is None:
            return False

        allowed = sandbox.config.allowed_paths
        if not allowed:
            return path.startswith(sandbox.config.workspace_root)

        return any(path.startswith(p) for p in allowed)

    def validate_network(self, sandbox_id: str, host: str) -> bool:
        """Check if a network host is allowed within the sandbox."""
        sandbox = self._sandboxes.get(sandbox_id)
        if sandbox is None:
            return False

        if not sandbox.config.network_enabled:
            return False

        allowed = sandbox.config.allowed_hosts
        if not allowed:
            return True

        return host in allowed

    def enforce_limits(self, sandbox_id: str) -> dict[str, Any]:
        """Check and return remaining resource budget for a sandbox."""
        sandbox = self._sandboxes.get(sandbox_id)
        if sandbox is None:
            raise SandboxError("sandbox not found", component="sandbox_manager")

        elapsed = time.time() - sandbox.created_at
        remaining_time = max(0.0, sandbox.config.timeout_seconds - elapsed)

        return {
            "sandbox_id": sandbox_id,
            "cpu_limit": sandbox.config.cpu_limit,
            "memory_limit_mb": sandbox.config.memory_limit_mb,
            "remaining_time_seconds": remaining_time,
            "active": sandbox.active,
        }

    @property
    def count(self) -> int:
        """Number of active sandboxes."""
        return len(self._sandboxes)
