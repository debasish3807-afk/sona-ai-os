"""Tests for GitHub client."""

import pytest

from sona_research.domain.github_models import (
    GitHubCommit,
    GitHubIssue,
    GitHubPullRequest,
    GitHubRelease,
    GitHubRepository,
)
from sona_research.infrastructure.github.client import GitHubClient


@pytest.fixture
def client() -> GitHubClient:
    c = GitHubClient()
    c.add_repository(
        GitHubRepository(
            owner="test", name="repo", description="Test repo", language="Python", stars=42
        )
    )
    c.add_commits(
        "test",
        "repo",
        [
            GitHubCommit(sha="abc123", message="Initial commit", author="dev1"),
            GitHubCommit(sha="def456", message="Add feature", author="dev2", files_changed=3),
            GitHubCommit(sha="ghi789", message="Fix bug", author="dev1", additions=10, deletions=5),
        ],
    )
    c.add_pull_requests(
        "test",
        "repo",
        [
            GitHubPullRequest(number=1, title="Feature A", state="open", author="dev1"),
            GitHubPullRequest(number=2, title="Feature B", state="merged", author="dev2"),
            GitHubPullRequest(number=3, title="Fix C", state="closed", author="dev1"),
        ],
    )
    c.add_issues(
        "test",
        "repo",
        [
            GitHubIssue(number=1, title="Bug 1", state="open", labels=["bug"]),
            GitHubIssue(number=2, title="Feature req", state="open", labels=["enhancement"]),
            GitHubIssue(number=3, title="Old bug", state="closed"),
        ],
    )
    c.add_branches("test", "repo", ["main", "develop", "feature/auth"])
    c.add_releases(
        "test",
        "repo",
        [
            GitHubRelease(tag="v1.0.0", name="First Release"),
            GitHubRelease(tag="v2.0.0-beta", name="Beta", prerelease=True),
        ],
    )
    c.add_file("test", "repo", "README.md", "# Test Repo")
    c.add_file("test", "repo", "src/main.py", "print('hello')")
    return c


class TestGitHubClientGetRepository:
    @pytest.mark.asyncio
    async def test_get_existing_repository(self, client: GitHubClient) -> None:
        repo = await client.get_repository("test", "repo")
        assert repo.owner == "test"
        assert repo.name == "repo"
        assert repo.description == "Test repo"
        assert repo.language == "Python"
        assert repo.stars == 42

    @pytest.mark.asyncio
    async def test_get_nonexistent_repository(self, client: GitHubClient) -> None:
        repo = await client.get_repository("unknown", "repo")
        assert repo.owner == "unknown"
        assert repo.name == "repo"
        assert repo.url == "https://github.com/unknown/repo"


class TestGitHubClientListCommits:
    @pytest.mark.asyncio
    async def test_list_all_commits(self, client: GitHubClient) -> None:
        commits = await client.list_commits("test", "repo")
        assert len(commits) == 3

    @pytest.mark.asyncio
    async def test_list_commits_with_limit(self, client: GitHubClient) -> None:
        commits = await client.list_commits("test", "repo", limit=2)
        assert len(commits) == 2

    @pytest.mark.asyncio
    async def test_list_commits_empty_repo(self, client: GitHubClient) -> None:
        commits = await client.list_commits("unknown", "repo")
        assert commits == []


class TestGitHubClientListPullRequests:
    @pytest.mark.asyncio
    async def test_list_open_prs(self, client: GitHubClient) -> None:
        prs = await client.list_pull_requests("test", "repo", state="open")
        assert len(prs) == 1
        assert prs[0].title == "Feature A"

    @pytest.mark.asyncio
    async def test_list_all_prs(self, client: GitHubClient) -> None:
        prs = await client.list_pull_requests("test", "repo", state="all")
        assert len(prs) == 3

    @pytest.mark.asyncio
    async def test_list_merged_prs(self, client: GitHubClient) -> None:
        prs = await client.list_pull_requests("test", "repo", state="merged")
        assert len(prs) == 1
        assert prs[0].number == 2


class TestGitHubClientListIssues:
    @pytest.mark.asyncio
    async def test_list_open_issues(self, client: GitHubClient) -> None:
        issues = await client.list_issues("test", "repo", state="open")
        assert len(issues) == 2

    @pytest.mark.asyncio
    async def test_list_all_issues(self, client: GitHubClient) -> None:
        issues = await client.list_issues("test", "repo", state="all")
        assert len(issues) == 3

    @pytest.mark.asyncio
    async def test_list_closed_issues(self, client: GitHubClient) -> None:
        issues = await client.list_issues("test", "repo", state="closed")
        assert len(issues) == 1
        assert issues[0].title == "Old bug"


class TestGitHubClientBranches:
    @pytest.mark.asyncio
    async def test_list_branches(self, client: GitHubClient) -> None:
        branches = await client.list_branches("test", "repo")
        assert "main" in branches
        assert "develop" in branches
        assert len(branches) == 3

    @pytest.mark.asyncio
    async def test_list_branches_empty(self, client: GitHubClient) -> None:
        branches = await client.list_branches("unknown", "repo")
        assert branches == ["main"]


class TestGitHubClientReleases:
    @pytest.mark.asyncio
    async def test_list_releases(self, client: GitHubClient) -> None:
        releases = await client.list_releases("test", "repo")
        assert len(releases) == 2
        assert releases[0].tag == "v1.0.0"

    @pytest.mark.asyncio
    async def test_list_releases_empty(self, client: GitHubClient) -> None:
        releases = await client.list_releases("unknown", "repo")
        assert releases == []


class TestGitHubClientFileContent:
    @pytest.mark.asyncio
    async def test_get_file_content(self, client: GitHubClient) -> None:
        content = await client.get_file_content("test", "repo", "README.md")
        assert content == "# Test Repo"

    @pytest.mark.asyncio
    async def test_get_nonexistent_file(self, client: GitHubClient) -> None:
        content = await client.get_file_content("test", "repo", "missing.txt")
        assert content == ""
