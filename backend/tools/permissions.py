"""Tool permission system.

Controls what tools can be executed, workspace restrictions,
command allow/deny lists, and resource limits.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

from config.logging import get_logger

logger = get_logger(__name__)


class PermissionLevel(IntEnum):
    """Permission levels for tool execution."""

    BLOCKED = 0  # Tool is completely blocked
    READ_ONLY = 10  # Only read operations allowed
    RESTRICTED = 20  # Limited write operations
    STANDARD = 50  # Normal operations within workspace
    ELEVATED = 80  # Can operate outside workspace with limits
    ADMIN = 100  # Full access (dangerous)


@dataclass
class ToolPermissions:
    """Permission configuration for the tool system.

    Controls:
        - Workspace boundaries (filesystem access)
        - Command allow/deny lists (terminal)
        - Execution timeouts and resource limits
        - Dangerous operation gating
    """

    # Workspace restriction
    workspace_root: str = field(default_factory=lambda: os.getcwd())
    allowed_paths: list[str] = field(default_factory=list)

    # Permission level
    level: PermissionLevel = PermissionLevel.STANDARD

    # Terminal command control
    command_allowlist: list[str] = field(
        default_factory=lambda: [
            "ls",
            "cat",
            "head",
            "tail",
            "grep",
            "find",
            "wc",
            "echo",
            "pwd",
            "git",
            "python",
            "python3",
            "pip",
            "node",
            "npm",
            "npx",
            "ruff",
            "mypy",
            "pytest",
            "cargo",
            "go",
            "rustc",
            "curl",
            "wget",
            "jq",
            "sed",
            "awk",
            "sort",
            "uniq",
            "diff",
            "mkdir",
            "cp",
            "mv",
            "rm",
            "touch",
            "chmod",
            "docker",
            "docker-compose",
            "make",
        ]
    )
    command_denylist: list[str] = field(
        default_factory=lambda: [
            "sudo",
            "su",
            "passwd",
            "shutdown",
            "reboot",
            "init",
            "mkfs",
            "fdisk",
            "dd",
            "mount",
            "umount",
            "iptables",
            "systemctl",
            "journalctl",
            "kill",
            "killall",
            "pkill",
        ]
    )

    # Resource limits
    max_timeout_seconds: int = 60
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10MB
    max_output_length: int = 100_000  # 100K chars
    max_concurrent_tools: int = 5

    # Safety
    safe_mode: bool = True  # Require confirmation for dangerous ops
    allow_network: bool = True
    allow_file_delete: bool = True

    def is_path_allowed(self, path: str) -> bool:
        """Check if a path is within the allowed workspace.

        Args:
            path: The path to check.

        Returns:
            True if path is allowed.
        """
        resolved = Path(path).resolve()
        workspace = Path(self.workspace_root).resolve()

        # Must be within workspace
        try:
            resolved.relative_to(workspace)
            return True
        except ValueError:
            pass

        # Check explicit allowed paths
        for allowed in self.allowed_paths:
            try:
                resolved.relative_to(Path(allowed).resolve())
                return True
            except ValueError:
                continue

        return False

    def is_command_allowed(self, command: str) -> bool:
        """Check if a terminal command is permitted.

        Args:
            command: The base command (first word).

        Returns:
            True if command is allowed.
        """
        base_cmd = command.strip().split()[0] if command.strip() else ""

        # Check denylist first
        if base_cmd in self.command_denylist:
            return False

        # If allowlist is configured, command must be in it
        if self.command_allowlist:
            return base_cmd in self.command_allowlist

        return True

    def check_file_size(self, size_bytes: int) -> bool:
        """Check if file size is within limits."""
        return size_bytes <= self.max_file_size_bytes

    def truncate_output(self, output: str) -> str:
        """Truncate output to maximum allowed length."""
        if len(output) <= self.max_output_length:
            return output
        half = self.max_output_length // 2
        return output[:half] + "\n\n... [truncated] ...\n\n" + output[-half:]
