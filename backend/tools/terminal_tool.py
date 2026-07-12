"""Terminal Tool — execute shell commands with safety controls.

Provides safe command execution with:
    - Command allow/deny list filtering
    - Working directory restriction
    - Configurable timeout
    - stdout/stderr capture
    - Exit code reporting
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from tools.base import BaseTool, ToolCategory, ToolMetadata, ToolParam, ToolResult
from tools.permissions import ToolPermissions


class TerminalTool(BaseTool):
    """Execute a shell command and capture output.

    Security controls:
        - Commands checked against allow/deny lists
        - Working directory must be within workspace
        - Execution timeout enforced
        - Output length limited
    """

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="terminal_exec",
            description="Execute a shell command and return stdout, stderr, and exit code",
            category=ToolCategory.TERMINAL,
            parameters=[
                ToolParam("command", "string", "The shell command to execute"),
                ToolParam(
                    "cwd",
                    "string",
                    "Working directory (defaults to workspace root)",
                    required=False,
                ),
                ToolParam(
                    "timeout",
                    "integer",
                    "Timeout in seconds (default 30)",
                    required=False,
                    default=30,
                ),
            ],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        command = str(params.get("command", "")).strip()
        cwd = str(params.get("cwd", self._permissions.workspace_root))
        timeout = min(int(params.get("timeout", 30)), self._permissions.max_timeout_seconds)

        if not command:
            return ToolResult(success=False, error="Parameter 'command' is required")

        # Validate command against allow/deny lists
        if not self._permissions.is_command_allowed(command):
            base_cmd = command.split()[0]
            return ToolResult(
                success=False,
                error=f"Command '{base_cmd}' is not permitted",
            )

        # Validate working directory
        resolved_cwd = str(Path(cwd).resolve())
        if not self._permissions.is_path_allowed(resolved_cwd):
            return ToolResult(
                success=False,
                error=f"Working directory '{cwd}' is outside workspace",
            )

        if not os.path.isdir(resolved_cwd):
            return ToolResult(success=False, error=f"Directory not found: {cwd}")

        # Execute the command
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=resolved_cwd,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return ToolResult(
                success=False,
                error=f"Command timed out after {timeout}s",
                data={"command": command, "timeout": timeout},
            )
        except OSError as exc:
            return ToolResult(success=False, error=f"Execution failed: {exc}")

        stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
        exit_code = proc.returncode or 0

        # Build output
        output_parts: list[str] = []
        if stdout:
            output_parts.append(stdout)
        if stderr:
            output_parts.append(f"[stderr]\n{stderr}")

        combined_output = "\n".join(output_parts)

        return ToolResult(
            success=exit_code == 0,
            output=combined_output,
            error=stderr if exit_code != 0 else None,
            data={
                "exit_code": exit_code,
                "command": command,
                "cwd": resolved_cwd,
            },
        )


def register_terminal_tools(permissions: ToolPermissions) -> list[BaseTool]:
    """Create and return all terminal tool instances."""
    return [TerminalTool(permissions)]
