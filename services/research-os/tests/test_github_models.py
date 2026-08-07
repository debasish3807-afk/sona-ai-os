"""Tests for GitHub integration domain models."""

from dataclasses import FrozenInstanceError

import pytest

from sona_research.domain.github_models import (
    GitHubCommit,
    GitHubEntityType,
    GitHubIssue,
    GitHubPullRequest,
    GitHubRelease,
    GitHubRepository,
)


class TestGitHubEntityType:
    def test_all_types_defined(self) -> None:
        assert GitHubEntityType.REPOSITORY == "repository"
        assert GitHubEntityType.COMMIT == "commit"
        assert GitHubEntityType.PULL_REQUEST == "pull_request"
        assert GitHubEntityType.ISSUE == "issue"
        assert GitHubEntityType.BRANCH == "branch"
        assert GitHubEntityType.RELEASE == "release"
        assert GitHubEntityType.FILE == "file"

    def test_type_count(self) -> None:
        assert len(GitHubEntityType) == 7

    def test_is_str_enum(self) -> None:
        assert str(GitHubEntityType.REPOSITORY) == "repository"


class TestGitHubRepository:
    def test_creation_minimal(self) -> None:
        repo = GitHubRepository(owner="octocat", name="hello-world")
        assert repo.owner == "octocat"
        assert repo.name == "hello-world"

    def test_creation_full(self) -> None:
        repo = GitHubRepository(
            owner="octocat",
            name="hello-world",
            description="A test repo",
            default_branch="main",
            language="Python",
            stars=100,
            url="https://github.com/octocat/hello-world",
        )
        assert repo.description == "A test repo"
        assert repo.language == "Python"
        assert repo.stars == 100

    def test_defaults(self) -> None:
        repo = GitHubRepository(owner="x", name="y")
        assert repo.description == ""
        assert repo.default_branch == "main"
        assert repo.language == ""
        assert repo.stars == 0
        assert repo.url == ""

    def test_is_frozen(self) -> None:
        repo = GitHubRepository(owner="x", name="y")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            repo.owner = "z"  # type: ignore[misc]


class TestGitHubCommit:
    def test_creation_minimal(self) -> None:
        commit = GitHubCommit(sha="abc123", message="Fix bug", author="dev")
        assert commit.sha == "abc123"
        assert commit.message == "Fix bug"
        assert commit.author == "dev"

    def test_creation_full(self) -> None:
        commit = GitHubCommit(
            sha="abc123def456",
            message="Implement feature X",
            author="developer",
            timestamp="2024-01-01T00:00:00Z",
            files_changed=5,
            additions=100,
            deletions=20,
        )
        assert commit.files_changed == 5
        assert commit.additions == 100
        assert commit.deletions == 20

    def test_defaults(self) -> None:
        commit = GitHubCommit(sha="x", message="m", author="a")
        assert commit.timestamp == ""
        assert commit.files_changed == 0
        assert commit.additions == 0
        assert commit.deletions == 0

    def test_is_frozen(self) -> None:
        commit = GitHubCommit(sha="x", message="m", author="a")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            commit.sha = "y"  # type: ignore[misc]


class TestGitHubPullRequest:
    def test_creation_minimal(self) -> None:
        pr = GitHubPullRequest(number=1, title="Add feature")
        assert pr.number == 1
        assert pr.title == "Add feature"

    def test_creation_full(self) -> None:
        pr = GitHubPullRequest(
            number=42,
            title="Implement auth",
            body="This adds OAuth2",
            state="merged",
            author="dev",
            branch="feature/auth",
            base="develop",
            created_at="2024-01-01",
        )
        assert pr.state == "merged"
        assert pr.branch == "feature/auth"
        assert pr.base == "develop"

    def test_defaults(self) -> None:
        pr = GitHubPullRequest(number=1, title="T")
        assert pr.body == ""
        assert pr.state == "open"
        assert pr.author == ""
        assert pr.branch == ""
        assert pr.base == "main"
        assert pr.created_at == ""

    def test_is_frozen(self) -> None:
        pr = GitHubPullRequest(number=1, title="T")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            pr.title = "X"  # type: ignore[misc]


class TestGitHubIssue:
    def test_creation_minimal(self) -> None:
        issue = GitHubIssue(number=1, title="Bug report")
        assert issue.number == 1
        assert issue.title == "Bug report"

    def test_creation_with_labels(self) -> None:
        issue = GitHubIssue(
            number=5,
            title="Feature request",
            body="Please add X",
            state="open",
            labels=["enhancement", "v2"],
            assignee="dev1",
        )
        assert issue.labels == ["enhancement", "v2"]
        assert issue.assignee == "dev1"

    def test_defaults(self) -> None:
        issue = GitHubIssue(number=1, title="T")
        assert issue.body == ""
        assert issue.state == "open"
        assert issue.labels == []
        assert issue.assignee == ""

    def test_is_frozen(self) -> None:
        issue = GitHubIssue(number=1, title="T")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            issue.title = "X"  # type: ignore[misc]


class TestGitHubRelease:
    def test_creation_minimal(self) -> None:
        release = GitHubRelease(tag="v1.0.0", name="Version 1.0")
        assert release.tag == "v1.0.0"
        assert release.name == "Version 1.0"

    def test_creation_full(self) -> None:
        release = GitHubRelease(
            tag="v2.0.0-beta",
            name="Beta Release",
            body="Release notes here",
            created_at="2024-06-01",
            prerelease=True,
        )
        assert release.prerelease is True
        assert release.body == "Release notes here"

    def test_defaults(self) -> None:
        release = GitHubRelease(tag="v1", name="R")
        assert release.body == ""
        assert release.created_at == ""
        assert release.prerelease is False

    def test_is_frozen(self) -> None:
        release = GitHubRelease(tag="v1", name="R")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            release.tag = "v2"  # type: ignore[misc]
