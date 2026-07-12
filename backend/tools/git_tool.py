"""Git Tool — local git operations within workspace repositories.

Provides safe git operations restricted to workspace boundaries.
All commands are executed via asyncio subprocess with timeout control.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from tools.base import BaseTool, ToolCategory, ToolMetadata, ToolParam, ToolResult
from tools.permissions import ToolPermissions


async def _run_git(args: list[str], cwd: str, timeout: int = 30) -> tuple[str, str, int]:
    """Run a git command and return (stdout, stderr, exit_code)."""
    cmd = ["git"] + args
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        return "", "Git command timed out", 1

    stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
    stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
    return stdout, stderr, proc.returncode or 0


def _validate_repo(path: str, permissions: ToolPermissions) -> str | None:
    """Validate path is an allowed git repository. Returns error or None."""
    resolved = str(Path(path).resolve())
    if not permissions.is_path_allowed(resolved):
        return f"Access denied: {path} is outside workspace"
    if not os.path.isdir(os.path.join(resolved, ".git")):
        return f"Not a git repository: {path}"
    return None


class GitStatusTool(BaseTool):
    """Show working tree status."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_status",
            description="Show git working tree status (modified, staged, untracked files)",
            category=ToolCategory.GIT,
            parameters=[ToolParam("repo_path", "string", "Path to git repository", required=False)],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        repo = str(params.get("repo_path", self._permissions.workspace_root))
        err = _validate_repo(repo, self._permissions)
        if err:
            return ToolResult(success=False, error=err)

        stdout, stderr, code = await _run_git(["status", "--short", "--branch"], repo)
        if code != 0:
            return ToolResult(success=False, error=stderr or "git status failed")
        return ToolResult(success=True, output=stdout, data={"repo": repo})


class GitAddTool(BaseTool):
    """Stage files for commit."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_add",
            description="Stage files for the next commit",
            category=ToolCategory.GIT,
            parameters=[
                ToolParam("files", "string", "Files to stage (space-separated, or '.' for all)"),
                ToolParam("repo_path", "string", "Path to git repository", required=False),
            ],
        )

    async def execute(self, **params: Any) -> ToolResult:
        files = str(params.get("files", "."))
        repo = str(params.get("repo_path", self._permissions.workspace_root))
        err = _validate_repo(repo, self._permissions)
        if err:
            return ToolResult(success=False, error=err)

        args = ["add"] + files.split()
        stdout, stderr, code = await _run_git(args, repo)
        if code != 0:
            return ToolResult(success=False, error=stderr or "git add failed")
        return ToolResult(success=True, output=stdout or f"Staged: {files}")


class GitCommitTool(BaseTool):
    """Create a commit."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_commit",
            description="Commit staged changes with a message",
            category=ToolCategory.GIT,
            parameters=[
                ToolParam("message", "string", "Commit message"),
                ToolParam("repo_path", "string", "Path to git repository", required=False),
            ],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        message = str(params.get("message", ""))
        repo = str(params.get("repo_path", self._permissions.workspace_root))
        if not message:
            return ToolResult(success=False, error="Parameter 'message' is required")

        err = _validate_repo(repo, self._permissions)
        if err:
            return ToolResult(success=False, error=err)

        stdout, stderr, code = await _run_git(["commit", "-m", message], repo)
        if code != 0:
            return ToolResult(success=False, error=stderr or "git commit failed")
        return ToolResult(success=True, output=stdout)


class GitBranchTool(BaseTool):
    """List or create branches."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_branch",
            description="List branches or create a new branch",
            category=ToolCategory.GIT,
            parameters=[
                ToolParam("name", "string", "New branch name (omit to list)", required=False),
                ToolParam("repo_path", "string", "Path to git repository", required=False),
            ],
        )

    async def execute(self, **params: Any) -> ToolResult:
        name = params.get("name")
        repo = str(params.get("repo_path", self._permissions.workspace_root))
        err = _validate_repo(repo, self._permissions)
        if err:
            return ToolResult(success=False, error=err)

        if name:
            stdout, stderr, code = await _run_git(["branch", str(name)], repo)
        else:
            stdout, stderr, code = await _run_git(["branch", "-a"], repo)

        if code != 0:
            return ToolResult(success=False, error=stderr or "git branch failed")
        return ToolResult(success=True, output=stdout)


class GitCheckoutTool(BaseTool):
    """Switch branches or restore files."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_checkout",
            description="Switch to a branch or create and switch with -b",
            category=ToolCategory.GIT,
            parameters=[
                ToolParam("target", "string", "Branch name or commit to checkout"),
                ToolParam(
                    "create",
                    "boolean",
                    "Create new branch (-b flag)",
                    required=False,
                    default=False,
                ),
                ToolParam("repo_path", "string", "Path to git repository", required=False),
            ],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        target = str(params.get("target", ""))
        create = bool(params.get("create", False))
        repo = str(params.get("repo_path", self._permissions.workspace_root))

        if not target:
            return ToolResult(success=False, error="Parameter 'target' is required")

        err = _validate_repo(repo, self._permissions)
        if err:
            return ToolResult(success=False, error=err)

        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(target)

        stdout, stderr, code = await _run_git(args, repo)
        if code != 0:
            return ToolResult(success=False, error=stderr or "git checkout failed")
        return ToolResult(success=True, output=stdout or stderr or f"Switched to {target}")


class GitPullTool(BaseTool):
    """Pull changes from remote."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_pull",
            description="Pull latest changes from remote",
            category=ToolCategory.GIT,
            parameters=[
                ToolParam("remote", "string", "Remote name", required=False, default="origin"),
                ToolParam("branch", "string", "Branch name", required=False),
                ToolParam("repo_path", "string", "Path to git repository", required=False),
            ],
        )

    async def execute(self, **params: Any) -> ToolResult:
        remote = str(params.get("remote", "origin"))
        branch = params.get("branch")
        repo = str(params.get("repo_path", self._permissions.workspace_root))
        err = _validate_repo(repo, self._permissions)
        if err:
            return ToolResult(success=False, error=err)

        args = ["pull", remote]
        if branch:
            args.append(str(branch))

        stdout, stderr, code = await _run_git(args, repo, timeout=60)
        if code != 0:
            return ToolResult(success=False, error=stderr or "git pull failed")
        return ToolResult(success=True, output=stdout or "Already up to date.")


class GitPushTool(BaseTool):
    """Push commits to remote."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_push",
            description="Push local commits to remote",
            category=ToolCategory.GIT,
            parameters=[
                ToolParam("remote", "string", "Remote name", required=False, default="origin"),
                ToolParam("branch", "string", "Branch name", required=False),
                ToolParam("repo_path", "string", "Path to git repository", required=False),
            ],
            dangerous=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        remote = str(params.get("remote", "origin"))
        branch = params.get("branch")
        repo = str(params.get("repo_path", self._permissions.workspace_root))
        err = _validate_repo(repo, self._permissions)
        if err:
            return ToolResult(success=False, error=err)

        args = ["push", remote]
        if branch:
            args.append(str(branch))

        stdout, stderr, code = await _run_git(args, repo, timeout=60)
        if code != 0:
            return ToolResult(success=False, error=stderr or "git push failed")
        return ToolResult(success=True, output=stdout or stderr or "Pushed successfully")


class GitDiffTool(BaseTool):
    """Show changes between commits or working tree."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_diff",
            description="Show file changes (unstaged by default, --staged for staged)",
            category=ToolCategory.GIT,
            parameters=[
                ToolParam(
                    "staged", "boolean", "Show staged changes", required=False, default=False
                ),
                ToolParam("file", "string", "Specific file to diff", required=False),
                ToolParam("repo_path", "string", "Path to git repository", required=False),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        staged = bool(params.get("staged", False))
        file_path = params.get("file")
        repo = str(params.get("repo_path", self._permissions.workspace_root))
        err = _validate_repo(repo, self._permissions)
        if err:
            return ToolResult(success=False, error=err)

        args = ["diff"]
        if staged:
            args.append("--staged")
        if file_path:
            args.extend(["--", str(file_path)])

        stdout, stderr, code = await _run_git(args, repo)
        if code != 0:
            return ToolResult(success=False, error=stderr or "git diff failed")
        return ToolResult(success=True, output=stdout or "(no changes)")


class GitLogTool(BaseTool):
    """Show commit history."""

    def __init__(self, permissions: ToolPermissions) -> None:
        self._permissions = permissions

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git_log",
            description="Show commit history (most recent first)",
            category=ToolCategory.GIT,
            parameters=[
                ToolParam(
                    "count", "integer", "Number of commits to show", required=False, default=10
                ),
                ToolParam(
                    "oneline", "boolean", "One line per commit", required=False, default=True
                ),
                ToolParam("repo_path", "string", "Path to git repository", required=False),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        count = int(params.get("count", 10))
        oneline = bool(params.get("oneline", True))
        repo = str(params.get("repo_path", self._permissions.workspace_root))
        err = _validate_repo(repo, self._permissions)
        if err:
            return ToolResult(success=False, error=err)

        args = ["log", f"-{count}"]
        if oneline:
            args.append("--oneline")

        stdout, stderr, code = await _run_git(args, repo)
        if code != 0:
            return ToolResult(success=False, error=stderr or "git log failed")
        return ToolResult(success=True, output=stdout)


def register_git_tools(permissions: ToolPermissions) -> list[BaseTool]:
    """Create and return all git tool instances."""
    return [
        GitStatusTool(permissions),
        GitAddTool(permissions),
        GitCommitTool(permissions),
        GitBranchTool(permissions),
        GitCheckoutTool(permissions),
        GitPullTool(permissions),
        GitPushTool(permissions),
        GitDiffTool(permissions),
        GitLogTool(permissions),
    ]
