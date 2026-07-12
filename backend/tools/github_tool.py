"""GitHub Tool — interact with GitHub repositories via the API.

Provides read-only access to repository information, branches,
pull requests, issues, and commits. Uses GITHUB_TOKEN env var
for authenticated requests (higher rate limits).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from tools.base import BaseTool, ToolCategory, ToolMetadata, ToolParam, ToolResult


def _get_github_client() -> httpx.AsyncClient:
    """Create an httpx client with optional GitHub token auth."""
    headers: dict[str, str] = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "SonaAIOS/0.8",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.AsyncClient(
        base_url="https://api.github.com",
        headers=headers,
        timeout=30.0,
    )


class GitHubRepoInfoTool(BaseTool):
    """Get repository information from GitHub."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="github_repo_info",
            description="Get information about a GitHub repository (stars, forks, description, language)",
            category=ToolCategory.GITHUB,
            parameters=[
                ToolParam("owner", "string", "Repository owner (user or org)"),
                ToolParam("repo", "string", "Repository name"),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        owner = str(params.get("owner", ""))
        repo = str(params.get("repo", ""))
        if not owner or not repo:
            return ToolResult(success=False, error="Both 'owner' and 'repo' are required")

        async with _get_github_client() as client:
            resp = await client.get(f"/repos/{owner}/{repo}")
            if resp.status_code == 404:
                return ToolResult(success=False, error=f"Repository not found: {owner}/{repo}")
            if resp.status_code != 200:
                return ToolResult(success=False, error=f"GitHub API error: {resp.status_code}")

            data = resp.json()
            info = {
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "language": data.get("language"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "open_issues": data.get("open_issues_count"),
                "default_branch": data.get("default_branch"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "topics": data.get("topics", []),
                "private": data.get("private"),
            }
            output = "\n".join(f"{k}: {v}" for k, v in info.items() if v is not None)
            return ToolResult(success=True, output=output, data=info)


class GitHubBranchesTool(BaseTool):
    """List branches for a repository."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="github_branches",
            description="List branches for a GitHub repository",
            category=ToolCategory.GITHUB,
            parameters=[
                ToolParam("owner", "string", "Repository owner"),
                ToolParam("repo", "string", "Repository name"),
                ToolParam("limit", "integer", "Max branches to return", required=False, default=30),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        owner = str(params.get("owner", ""))
        repo = str(params.get("repo", ""))
        limit = int(params.get("limit", 30))
        if not owner or not repo:
            return ToolResult(success=False, error="Both 'owner' and 'repo' are required")

        async with _get_github_client() as client:
            resp = await client.get(f"/repos/{owner}/{repo}/branches", params={"per_page": limit})
            if resp.status_code != 200:
                return ToolResult(success=False, error=f"GitHub API error: {resp.status_code}")

            branches = resp.json()
            names = [b["name"] for b in branches]
            return ToolResult(
                success=True,
                output="\n".join(names),
                data={"branches": names, "count": len(names)},
            )


class GitHubPullRequestsTool(BaseTool):
    """List pull requests for a repository."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="github_pull_requests",
            description="List pull requests for a GitHub repository",
            category=ToolCategory.GITHUB,
            parameters=[
                ToolParam("owner", "string", "Repository owner"),
                ToolParam("repo", "string", "Repository name"),
                ToolParam(
                    "state", "string", "Filter: open, closed, all", required=False, default="open"
                ),
                ToolParam("limit", "integer", "Max PRs to return", required=False, default=10),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        owner = str(params.get("owner", ""))
        repo = str(params.get("repo", ""))
        state = str(params.get("state", "open"))
        limit = int(params.get("limit", 10))
        if not owner or not repo:
            return ToolResult(success=False, error="Both 'owner' and 'repo' are required")

        async with _get_github_client() as client:
            resp = await client.get(
                f"/repos/{owner}/{repo}/pulls",
                params={"state": state, "per_page": limit},
            )
            if resp.status_code != 200:
                return ToolResult(success=False, error=f"GitHub API error: {resp.status_code}")

            prs = resp.json()
            lines: list[str] = []
            for pr in prs:
                lines.append(
                    f"#{pr['number']} [{pr['state']}] {pr['title']} (@{pr['user']['login']})"
                )

            return ToolResult(
                success=True,
                output="\n".join(lines) or "No pull requests found",
                data={"count": len(prs), "state": state},
            )


class GitHubIssuesTool(BaseTool):
    """List issues for a repository."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="github_issues",
            description="List issues for a GitHub repository",
            category=ToolCategory.GITHUB,
            parameters=[
                ToolParam("owner", "string", "Repository owner"),
                ToolParam("repo", "string", "Repository name"),
                ToolParam(
                    "state", "string", "Filter: open, closed, all", required=False, default="open"
                ),
                ToolParam("limit", "integer", "Max issues to return", required=False, default=10),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        owner = str(params.get("owner", ""))
        repo = str(params.get("repo", ""))
        state = str(params.get("state", "open"))
        limit = int(params.get("limit", 10))
        if not owner or not repo:
            return ToolResult(success=False, error="Both 'owner' and 'repo' are required")

        async with _get_github_client() as client:
            resp = await client.get(
                f"/repos/{owner}/{repo}/issues",
                params={"state": state, "per_page": limit},
            )
            if resp.status_code != 200:
                return ToolResult(success=False, error=f"GitHub API error: {resp.status_code}")

            issues = [i for i in resp.json() if "pull_request" not in i]
            lines: list[str] = []
            for issue in issues:
                labels = ", ".join(lbl["name"] for lbl in issue.get("labels", []))
                label_str = f" [{labels}]" if labels else ""
                lines.append(f"#{issue['number']} {issue['title']}{label_str}")

            return ToolResult(
                success=True,
                output="\n".join(lines) or "No issues found",
                data={"count": len(issues), "state": state},
            )


class GitHubCommitsTool(BaseTool):
    """List recent commits for a repository."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="github_commits",
            description="List recent commits for a GitHub repository",
            category=ToolCategory.GITHUB,
            parameters=[
                ToolParam("owner", "string", "Repository owner"),
                ToolParam("repo", "string", "Repository name"),
                ToolParam("branch", "string", "Branch name", required=False),
                ToolParam("limit", "integer", "Max commits to return", required=False, default=10),
            ],
            read_only=True,
        )

    async def execute(self, **params: Any) -> ToolResult:
        owner = str(params.get("owner", ""))
        repo = str(params.get("repo", ""))
        branch = params.get("branch")
        limit = int(params.get("limit", 10))
        if not owner or not repo:
            return ToolResult(success=False, error="Both 'owner' and 'repo' are required")

        query_params: dict[str, Any] = {"per_page": limit}
        if branch:
            query_params["sha"] = branch

        async with _get_github_client() as client:
            resp = await client.get(
                f"/repos/{owner}/{repo}/commits",
                params=query_params,
            )
            if resp.status_code != 200:
                return ToolResult(success=False, error=f"GitHub API error: {resp.status_code}")

            commits = resp.json()
            lines: list[str] = []
            for c in commits:
                sha_short = c["sha"][:7]
                msg = c["commit"]["message"].split("\n")[0]
                author = c["commit"]["author"]["name"]
                lines.append(f"{sha_short} {msg} ({author})")

            return ToolResult(
                success=True,
                output="\n".join(lines),
                data={"count": len(commits)},
            )


def register_github_tools() -> list[BaseTool]:
    """Create and return all GitHub tool instances."""
    return [
        GitHubRepoInfoTool(),
        GitHubBranchesTool(),
        GitHubPullRequestsTool(),
        GitHubIssuesTool(),
        GitHubCommitsTool(),
    ]
