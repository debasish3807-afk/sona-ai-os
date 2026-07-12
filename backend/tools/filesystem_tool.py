"""Filesystem Tool — read, write, edit, delete, copy, move, search, mkdir, ls.

Provides safe filesystem operations restricted to the workspace boundary.
All paths are validated against the permission system before execution.
"""

from __future__ import annotations

import fnmatch
import os
import shutil
from pathlib import Path
from typing import Any

from tools.base import BaseTool, ToolCategory, ToolMetadata, ToolParam, ToolResult
from tools.permissions import ToolPermissions


class FileReadTool(BaseTool):
    """Read file contents."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_read",
            description="Read the contents of a file",
            category=ToolCategory.FILESYSTEM,
            parameters=[
                ToolParam("path", "string", "Path to the file to read"),
                ToolParam(
                    "offset", "integer", "Line offset (0-indexed)", required=False, default=0
                ),
                ToolParam("limit", "integer", "Max lines to read", required=False, default=2000),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        path = str(params.get("path", ""))
        offset = int(params.get("offset", 0))
        limit = int(params.get("limit", 2000))

        if not path:
            return ToolResult(success=False, error="Parameter 'path' is required")

        resolved = str(Path(path).resolve())
        if not self._permissions.is_path_allowed(resolved):
            return ToolResult(success=False, error=f"Access denied: {path} is outside workspace")

        if not os.path.isfile(resolved):
            return ToolResult(success=False, error=f"File not found: {path}")

        size = os.path.getsize(resolved)
        if not self._permissions.check_file_size(size):
            return ToolResult(success=False, error=f"File too large: {size} bytes")

        try:
            with open(resolved, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            selected = lines[offset : offset + limit]
            content = "".join(selected)
            return ToolResult(
                success=True,
                output=content,
                data={"total_lines": len(lines), "offset": offset, "lines_read": len(selected)},
            )
        except OSError as exc:
            return ToolResult(success=False, error=f"Read error: {exc}")


class FileWriteTool(BaseTool):
    """Write content to a file (create or overwrite)."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_write",
            description="Write content to a file (creates or overwrites)",
            category=ToolCategory.FILESYSTEM,
            parameters=[
                ToolParam("path", "string", "Path to the file"),
                ToolParam("content", "string", "Content to write"),
            ],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        path = str(params.get("path", ""))
        content = str(params.get("content", ""))

        if not path:
            return ToolResult(success=False, error="Parameter 'path' is required")

        resolved = str(Path(path).resolve())
        if not self._permissions.is_path_allowed(resolved):
            return ToolResult(success=False, error=f"Access denied: {path} is outside workspace")

        try:
            os.makedirs(os.path.dirname(resolved), exist_ok=True)
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(
                success=True,
                output=f"Written {len(content)} bytes to {path}",
                data={"bytes_written": len(content), "path": path},
            )
        except OSError as exc:
            return ToolResult(success=False, error=f"Write error: {exc}")


class FileEditTool(BaseTool):
    """Edit a file by replacing text."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_edit",
            description="Edit a file by replacing old_text with new_text",
            category=ToolCategory.FILESYSTEM,
            parameters=[
                ToolParam("path", "string", "Path to the file"),
                ToolParam("old_text", "string", "Text to find and replace"),
                ToolParam("new_text", "string", "Replacement text"),
            ],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        path = str(params.get("path", ""))
        old_text = str(params.get("old_text", ""))
        new_text = str(params.get("new_text", ""))

        if not path or not old_text:
            return ToolResult(success=False, error="Parameters 'path' and 'old_text' are required")

        resolved = str(Path(path).resolve())
        if not self._permissions.is_path_allowed(resolved):
            return ToolResult(success=False, error=f"Access denied: {path} is outside workspace")

        if not os.path.isfile(resolved):
            return ToolResult(success=False, error=f"File not found: {path}")

        try:
            with open(resolved, encoding="utf-8") as f:
                content = f.read()

            if old_text not in content:
                return ToolResult(success=False, error="old_text not found in file")

            new_content = content.replace(old_text, new_text, 1)
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult(success=True, output=f"Edited {path}: replaced text")
        except OSError as exc:
            return ToolResult(success=False, error=f"Edit error: {exc}")


class FileDeleteTool(BaseTool):
    """Delete a file."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_delete",
            description="Delete a file from the filesystem",
            category=ToolCategory.FILESYSTEM,
            parameters=[ToolParam("path", "string", "Path to the file to delete")],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        path = str(params.get("path", ""))
        if not path:
            return ToolResult(success=False, error="Parameter 'path' is required")

        resolved = str(Path(path).resolve())
        if not self._permissions.is_path_allowed(resolved):
            return ToolResult(success=False, error=f"Access denied: {path} is outside workspace")

        if not self._permissions.allow_file_delete:
            return ToolResult(success=False, error="File deletion is disabled")

        if not os.path.exists(resolved):
            return ToolResult(success=False, error=f"Path not found: {path}")

        try:
            if os.path.isfile(resolved):
                os.remove(resolved)
            else:
                shutil.rmtree(resolved)
            return ToolResult(success=True, output=f"Deleted: {path}")
        except OSError as exc:
            return ToolResult(success=False, error=f"Delete error: {exc}")


class FileCopyTool(BaseTool):
    """Copy a file or directory."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_copy",
            description="Copy a file or directory to a new location",
            category=ToolCategory.FILESYSTEM,
            parameters=[
                ToolParam("source", "string", "Source path"),
                ToolParam("destination", "string", "Destination path"),
            ],
        )

    async def execute(self, **params: Any) -> ToolResult:
        source = str(params.get("source", ""))
        destination = str(params.get("destination", ""))

        if not source or not destination:
            return ToolResult(success=False, error="Both 'source' and 'destination' are required")

        src_resolved = str(Path(source).resolve())
        dst_resolved = str(Path(destination).resolve())

        if not self._permissions.is_path_allowed(src_resolved):
            return ToolResult(success=False, error=f"Access denied: {source}")
        if not self._permissions.is_path_allowed(dst_resolved):
            return ToolResult(success=False, error=f"Access denied: {destination}")

        if not os.path.exists(src_resolved):
            return ToolResult(success=False, error=f"Source not found: {source}")

        try:
            if os.path.isdir(src_resolved):
                shutil.copytree(src_resolved, dst_resolved)
            else:
                os.makedirs(os.path.dirname(dst_resolved), exist_ok=True)
                shutil.copy2(src_resolved, dst_resolved)
            return ToolResult(success=True, output=f"Copied {source} → {destination}")
        except OSError as exc:
            return ToolResult(success=False, error=f"Copy error: {exc}")


class FileMoveTool(BaseTool):
    """Move/rename a file or directory."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_move",
            description="Move or rename a file or directory",
            category=ToolCategory.FILESYSTEM,
            parameters=[
                ToolParam("source", "string", "Source path"),
                ToolParam("destination", "string", "Destination path"),
            ],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        source = str(params.get("source", ""))
        destination = str(params.get("destination", ""))

        if not source or not destination:
            return ToolResult(success=False, error="Both 'source' and 'destination' are required")

        src_resolved = str(Path(source).resolve())
        dst_resolved = str(Path(destination).resolve())

        if not self._permissions.is_path_allowed(src_resolved):
            return ToolResult(success=False, error=f"Access denied: {source}")
        if not self._permissions.is_path_allowed(dst_resolved):
            return ToolResult(success=False, error=f"Access denied: {destination}")

        if not os.path.exists(src_resolved):
            return ToolResult(success=False, error=f"Source not found: {source}")

        try:
            os.makedirs(os.path.dirname(dst_resolved), exist_ok=True)
            shutil.move(src_resolved, dst_resolved)
            return ToolResult(success=True, output=f"Moved {source} → {destination}")
        except OSError as exc:
            return ToolResult(success=False, error=f"Move error: {exc}")


class FileSearchTool(BaseTool):
    """Search for files by pattern."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_search",
            description="Search for files matching a glob pattern",
            category=ToolCategory.FILESYSTEM,
            parameters=[
                ToolParam("pattern", "string", "Glob pattern (e.g., '*.py', '**/*.md')"),
                ToolParam("directory", "string", "Directory to search in", required=False),
                ToolParam("max_results", "integer", "Max results", required=False, default=50),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        pattern = str(params.get("pattern", ""))
        directory = str(params.get("directory", self._permissions.workspace_root))
        max_results = int(params.get("max_results", 50))

        if not pattern:
            return ToolResult(success=False, error="Parameter 'pattern' is required")

        resolved_dir = str(Path(directory).resolve())
        if not self._permissions.is_path_allowed(resolved_dir):
            return ToolResult(success=False, error=f"Access denied: {directory}")

        matches: list[str] = []
        try:
            for root, _dirs, files in os.walk(resolved_dir):
                if len(matches) >= max_results:
                    break
                for name in files:
                    if fnmatch.fnmatch(name, pattern):
                        matches.append(os.path.join(root, name))
                        if len(matches) >= max_results:
                            break
        except OSError as exc:
            return ToolResult(success=False, error=f"Search error: {exc}")

        return ToolResult(
            success=True,
            output="\n".join(matches),
            data={
                "count": len(matches),
                "pattern": pattern,
                "truncated": len(matches) >= max_results,
            },
        )


class MkdirTool(BaseTool):
    """Create a directory."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="mkdir",
            description="Create a directory (and parent directories if needed)",
            category=ToolCategory.FILESYSTEM,
            parameters=[ToolParam("path", "string", "Directory path to create")],
        )

    async def execute(self, **params: Any) -> ToolResult:
        path = str(params.get("path", ""))
        if not path:
            return ToolResult(success=False, error="Parameter 'path' is required")

        resolved = str(Path(path).resolve())
        if not self._permissions.is_path_allowed(resolved):
            return ToolResult(success=False, error=f"Access denied: {path}")

        try:
            os.makedirs(resolved, exist_ok=True)
            return ToolResult(success=True, output=f"Created directory: {path}")
        except OSError as exc:
            return ToolResult(success=False, error=f"Mkdir error: {exc}")


class ListDirTool(BaseTool):
    """List directory contents."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="list_dir",
            description="List contents of a directory",
            category=ToolCategory.FILESYSTEM,
            parameters=[
                ToolParam("path", "string", "Directory path to list"),
                ToolParam(
                    "recursive", "boolean", "List recursively", required=False, default=False
                ),
                ToolParam("max_depth", "integer", "Max recursion depth", required=False, default=2),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        path = str(params.get("path", "."))
        recursive = bool(params.get("recursive", False))
        max_depth = int(params.get("max_depth", 2))

        resolved = str(Path(path).resolve())
        if not self._permissions.is_path_allowed(resolved):
            return ToolResult(success=False, error=f"Access denied: {path}")

        if not os.path.isdir(resolved):
            return ToolResult(success=False, error=f"Not a directory: {path}")

        entries: list[str] = []
        try:
            if recursive:
                self._walk_dir(resolved, entries, depth=0, max_depth=max_depth)
            else:
                for entry in sorted(os.listdir(resolved)):
                    full = os.path.join(resolved, entry)
                    marker = "/" if os.path.isdir(full) else ""
                    entries.append(f"{entry}{marker}")
        except OSError as exc:
            return ToolResult(success=False, error=f"List error: {exc}")

        return ToolResult(
            success=True,
            output="\n".join(entries),
            data={"count": len(entries), "path": path},
        )

    def _walk_dir(self, path: str, entries: list[str], depth: int, max_depth: int) -> None:
        """Recursively list directory with depth limit."""
        if depth >= max_depth:
            return
        try:
            for entry in sorted(os.listdir(path)):
                full = os.path.join(path, entry)
                indent = "  " * depth
                if os.path.isdir(full):
                    entries.append(f"{indent}{entry}/")
                    self._walk_dir(full, entries, depth + 1, max_depth)
                else:
                    entries.append(f"{indent}{entry}")
        except OSError:
            pass


def register_filesystem_tools(permissions: ToolPermissions) -> list[BaseTool]:
    """Create and return all filesystem tool instances."""
    return [
        FileReadTool(permissions),
        FileWriteTool(permissions),
        FileEditTool(permissions),
        FileDeleteTool(permissions),
        FileCopyTool(permissions),
        FileMoveTool(permissions),
        FileSearchTool(permissions),
        MkdirTool(permissions),
        ListDirTool(permissions),
    ]
