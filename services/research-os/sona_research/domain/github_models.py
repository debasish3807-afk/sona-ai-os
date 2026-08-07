"""GitHub integration domain models."""

from dataclasses import dataclass, field
from enum import StrEnum


class GitHubEntityType(StrEnum):
    """Types of GitHub entities that can be indexed."""

    REPOSITORY = "repository"
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    BRANCH = "branch"
    RELEASE = "release"
    FILE = "file"


@dataclass(frozen=True)
class GitHubRepository:
    """Represents a GitHub repository."""

    owner: str
    name: str
    description: str = ""
    default_branch: str = "main"
    language: str = ""
    stars: int = 0
    url: str = ""


@dataclass(frozen=True)
class GitHubCommit:
    """Represents a GitHub commit."""

    sha: str
    message: str
    author: str
    timestamp: str = ""
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0


@dataclass(frozen=True)
class GitHubPullRequest:
    """Represents a GitHub pull request."""

    number: int
    title: str
    body: str = ""
    state: str = "open"
    author: str = ""
    branch: str = ""
    base: str = "main"
    created_at: str = ""


@dataclass(frozen=True)
class GitHubIssue:
    """Represents a GitHub issue."""

    number: int
    title: str
    body: str = ""
    state: str = "open"
    labels: list[str] = field(default_factory=list)
    assignee: str = ""


@dataclass(frozen=True)
class GitHubRelease:
    """Represents a GitHub release."""

    tag: str
    name: str
    body: str = ""
    created_at: str = ""
    prerelease: bool = False
