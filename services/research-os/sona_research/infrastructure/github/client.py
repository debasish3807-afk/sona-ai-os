"""Simulated GitHub API client.

Provides a GitHub client that simulates API responses for development
and testing without requiring real API credentials.
"""

import structlog

from sona_research.domain.github_models import (
    GitHubCommit,
    GitHubIssue,
    GitHubPullRequest,
    GitHubRelease,
    GitHubRepository,
)

logger = structlog.get_logger()


class GitHubClient:
    """Simulated GitHub API client for repository data retrieval."""

    def __init__(self) -> None:
        """Initialize the GitHub client."""
        self._repositories: dict[str, GitHubRepository] = {}
        self._commits: dict[str, list[GitHubCommit]] = {}
        self._pull_requests: dict[str, list[GitHubPullRequest]] = {}
        self._issues: dict[str, list[GitHubIssue]] = {}
        self._branches: dict[str, list[str]] = {}
        self._releases: dict[str, list[GitHubRelease]] = {}
        self._files: dict[str, dict[str, str]] = {}

    def _repo_key(self, owner: str, repo: str) -> str:
        """Generate a storage key for a repository."""
        return f"{owner}/{repo}"

    def add_repository(self, repo: GitHubRepository) -> None:
        """Add a repository to the simulated store."""
        key = self._repo_key(repo.owner, repo.name)
        self._repositories[key] = repo

    def add_commits(self, owner: str, repo: str, commits: list[GitHubCommit]) -> None:
        """Add commits to a repository in the simulated store."""
        key = self._repo_key(owner, repo)
        self._commits.setdefault(key, []).extend(commits)

    def add_pull_requests(self, owner: str, repo: str, prs: list[GitHubPullRequest]) -> None:
        """Add pull requests to a repository in the simulated store."""
        key = self._repo_key(owner, repo)
        self._pull_requests.setdefault(key, []).extend(prs)

    def add_issues(self, owner: str, repo: str, issues: list[GitHubIssue]) -> None:
        """Add issues to a repository in the simulated store."""
        key = self._repo_key(owner, repo)
        self._issues.setdefault(key, []).extend(issues)

    def add_branches(self, owner: str, repo: str, branches: list[str]) -> None:
        """Add branches to a repository in the simulated store."""
        key = self._repo_key(owner, repo)
        self._branches.setdefault(key, []).extend(branches)

    def add_releases(self, owner: str, repo: str, releases: list[GitHubRelease]) -> None:
        """Add releases to a repository in the simulated store."""
        key = self._repo_key(owner, repo)
        self._releases.setdefault(key, []).extend(releases)

    def add_file(self, owner: str, repo: str, path: str, content: str) -> None:
        """Add a file to a repository in the simulated store."""
        key = self._repo_key(owner, repo)
        self._files.setdefault(key, {})[path] = content

    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        """Get repository information."""
        key = self._repo_key(owner, repo)
        logger.info("github.get_repository", owner=owner, repo=repo)
        if key in self._repositories:
            return self._repositories[key]
        return GitHubRepository(
            owner=owner,
            name=repo,
            url=f"https://github.com/{owner}/{repo}",
        )

    async def list_commits(self, owner: str, repo: str, limit: int = 30) -> list[GitHubCommit]:
        """List commits for a repository."""
        key = self._repo_key(owner, repo)
        logger.info("github.list_commits", owner=owner, repo=repo, limit=limit)
        commits = self._commits.get(key, [])
        return commits[:limit]

    async def list_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> list[GitHubPullRequest]:
        """List pull requests for a repository, filtered by state."""
        key = self._repo_key(owner, repo)
        logger.info("github.list_pull_requests", owner=owner, repo=repo, state=state)
        prs = self._pull_requests.get(key, [])
        if state == "all":
            return prs
        return [pr for pr in prs if pr.state == state]

    async def list_issues(self, owner: str, repo: str, state: str = "open") -> list[GitHubIssue]:
        """List issues for a repository, filtered by state."""
        key = self._repo_key(owner, repo)
        logger.info("github.list_issues", owner=owner, repo=repo, state=state)
        issues = self._issues.get(key, [])
        if state == "all":
            return issues
        return [issue for issue in issues if issue.state == state]

    async def list_branches(self, owner: str, repo: str) -> list[str]:
        """List branches for a repository."""
        key = self._repo_key(owner, repo)
        logger.info("github.list_branches", owner=owner, repo=repo)
        return self._branches.get(key, ["main"])

    async def list_releases(self, owner: str, repo: str) -> list[GitHubRelease]:
        """List releases for a repository."""
        key = self._repo_key(owner, repo)
        logger.info("github.list_releases", owner=owner, repo=repo)
        return self._releases.get(key, [])

    async def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """Get file content from a repository."""
        key = self._repo_key(owner, repo)
        logger.info("github.get_file_content", owner=owner, repo=repo, path=path)
        files = self._files.get(key, {})
        if path in files:
            return files[path]
        return ""
