"""Capability Sandbox — resource and access restrictions for capabilities."""

from __future__ import annotations

import os
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class CapabilitySandbox:
    """Enforces resource limits and access restrictions on capabilities.

    Controls filesystem access, network access, timeouts,
    and memory limits for capability execution.
    """

    def __init__(
        self,
        workspace_root: str,
        max_timeout: int = 60,
        max_memory_mb: int = 512,
        allowed_paths: list[str] | None = None,
        allowed_hosts: list[str] | None = None,
    ) -> None:
        self._workspace_root = os.path.abspath(workspace_root)
        self._max_timeout = max_timeout
        self._max_memory_mb = max_memory_mb
        self._allowed_paths = allowed_paths or [self._workspace_root]
        self._allowed_hosts = allowed_hosts or []

    def validate_path(self, path: str) -> bool:
        """Validate that a filesystem path is within allowed boundaries.

        Args:
            path: The path to validate.

        Returns:
            True if the path is allowed, False otherwise.
        """
        abs_path = os.path.abspath(path)
        for allowed in self._allowed_paths:
            if abs_path.startswith(os.path.abspath(allowed)):
                return True
        logger.warning("sandbox_path_denied", path=path)
        return False

    def validate_network(self, host: str) -> bool:
        """Validate that a network host is in the allowed list.

        Args:
            host: The hostname to validate.

        Returns:
            True if the host is allowed, False if restricted.
        """
        if not self._allowed_hosts:
            return True
        allowed = host in self._allowed_hosts
        if not allowed:
            logger.warning("sandbox_host_denied", host=host)
        return allowed

    def enforce_timeout(self, timeout: int) -> int:
        """Enforce timeout limits, capping at the maximum.

        Args:
            timeout: Requested timeout in seconds.

        Returns:
            The enforced timeout (minimum of requested and max).
        """
        return min(timeout, self._max_timeout)

    def enforce_memory(self, requested_mb: int) -> int:
        """Enforce memory limits, capping at the maximum.

        Args:
            requested_mb: Requested memory in megabytes.

        Returns:
            The enforced memory limit.
        """
        return min(requested_mb, self._max_memory_mb)

    def get_restrictions(self) -> dict[str, Any]:
        """Get current sandbox restriction configuration.

        Returns:
            Dictionary of all sandbox restrictions.
        """
        return {
            "workspace_root": self._workspace_root,
            "max_timeout": self._max_timeout,
            "max_memory_mb": self._max_memory_mb,
            "allowed_paths": self._allowed_paths,
            "allowed_hosts": self._allowed_hosts,
        }
