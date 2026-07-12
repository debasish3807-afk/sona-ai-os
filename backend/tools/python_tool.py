"""Python Tool — safe sandboxed code execution with output capture.

Executes Python code in a subprocess with:
    - Isolated process (no access to parent memory)
    - Configurable timeout
    - stdout/stderr capture
    - Resource limiting via timeout
    - Restricted imports (configurable deny list)
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from typing import Any

from tools.base import BaseTool, ToolCategory, ToolMetadata, ToolParam, ToolResult
from tools.permissions import ToolPermissions

# Imports that are blocked in sandboxed execution
BLOCKED_MODULES = [
    "subprocess",
    "os.system",
    "shutil.rmtree",
    "ctypes",
    "multiprocessing",
    "signal",
    "socket",
    "http.server",
    "xmlrpc",
]

SANDBOX_WRAPPER = """
import sys
import io
import json

_stdout_buffer = io.StringIO()
_stderr_buffer = io.StringIO()
sys.stdout = _stdout_buffer
sys.stderr = _stderr_buffer

_error = None

try:
{indented_code}
except Exception as _exc:
    _error = type(_exc).__name__ + ": " + str(_exc)

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

output = dict(
    stdout=_stdout_buffer.getvalue(),
    stderr=_stderr_buffer.getvalue(),
    error=_error,
)
print("__SANDBOX_RESULT__" + json.dumps(output))
"""


class PythonExecTool(BaseTool):
    """Execute Python code in a sandboxed subprocess."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="python_exec",
            description="Execute Python code safely in a sandboxed subprocess and capture output",
            category=ToolCategory.PYTHON,
            parameters=[
                ToolParam("code", "string", "Python code to execute"),
                ToolParam(
                    "timeout", "integer", "Execution timeout in seconds", required=False, default=15
                ),
            ],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        code = str(params.get("code", ""))
        timeout = min(int(params.get("timeout", 15)), self._permissions.max_timeout_seconds)

        if not code:
            return ToolResult(success=False, error="Parameter 'code' is required")

        # Check for blocked imports
        for blocked in BLOCKED_MODULES:
            if blocked in code:
                return ToolResult(
                    success=False,
                    error=f"Blocked module detected: '{blocked}' is not allowed in sandbox",
                )

        # Indent user code for the wrapper
        indented = "\n".join("    " + line for line in code.splitlines())
        wrapper = SANDBOX_WRAPPER.replace("{indented_code}", indented)

        # Write to temp file and execute in subprocess
        tmp_dir = tempfile.mkdtemp(prefix="sona_py_")
        script_path = os.path.join(tmp_dir, "sandbox_script.py")

        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(wrapper)

            proc = await asyncio.create_subprocess_exec(
                "python3",
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._permissions.workspace_root,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except TimeoutError:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
                return ToolResult(
                    success=False,
                    error=f"Execution timed out after {timeout}s",
                    data={"timeout": timeout},
                )

            raw_stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            raw_stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

            # Parse sandbox result
            if "__SANDBOX_RESULT__" in raw_stdout:
                marker_pos = raw_stdout.index("__SANDBOX_RESULT__")
                json_str = raw_stdout[marker_pos + len("__SANDBOX_RESULT__") :]
                try:
                    result_data = json.loads(json_str.strip())
                    stdout = result_data.get("stdout", "")
                    stderr = result_data.get("stderr", "")
                    error = result_data.get("error")

                    if error:
                        return ToolResult(
                            success=False,
                            output=stdout,
                            error=error,
                            data={"stderr": stderr},
                        )
                    return ToolResult(
                        success=True,
                        output=stdout or "(no output)",
                        data={"stderr": stderr} if stderr else {},
                    )
                except json.JSONDecodeError:
                    pass

            # Fallback: process crashed or wrapper failed
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    output=raw_stdout,
                    error=raw_stderr or f"Process exited with code {proc.returncode}",
                )

            return ToolResult(success=True, output=raw_stdout or "(no output)")

        finally:
            # Clean up temp file
            try:
                os.remove(script_path)
                os.rmdir(tmp_dir)
            except OSError:
                pass


def register_python_tools(permissions: ToolPermissions) -> list[BaseTool]:
    """Create and return all Python tool instances."""
    return [PythonExecTool(permissions)]
