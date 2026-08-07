"""Tests for GitHub repository indexer."""

import pytest

from sona_research.domain.github_models import (
    GitHubCommit,
    GitHubIssue,
    GitHubPullRequest,
    GitHubRelease,
    GitHubRepository,
)
from sona_research.infrastructure.github.client import GitHubClient
from sona_research.infrastructure.github.indexer import GitHubIndexer


@pytest.fixture
def populated_client() -> GitHubClient:
    c = GitHubClient()
    c.add_repository(
        GitHubRepository(owner="org", name="project", description="A project", language="Python")
    )
    c.add_commits(
        "org",
        "project",
        [
            GitHubCommit(sha="aaa111", message="Init", author="alice"),
            GitHubCommit(sha="bbb222", message="Add tests", author="bob"),
        ],
    )
    c.add_pull_requests(
        "org",
        "project",
        [
            GitHubPullRequest(number=1, title="Feature X", state="merged", author="alice"),
        ],
    )
    c.add_issues(
        "org",
        "project",
        [
            GitHubIssue(number=1, title="Bug report", state="open", labels=["bug"]),
        ],
    )
    c.add_releases(
        "org",
        "project",
        [
            GitHubRelease(tag="v1.0", name="Release 1.0"),
        ],
    )
    return c


@pytest.fixture
def indexer(populated_client: GitHubClient) -> GitHubIndexer:
    return GitHubIndexer(populated_client)


class TestGitHubIndexerBasic:
    @pytest.mark.asyncio
    async def test_index_creates_repo_node(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        assert "repo:org/project" in graph.nodes
        assert graph.nodes["repo:org/project"].node_type == "repository"

    @pytest.mark.asyncio
    async def test_index_creates_commit_nodes(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        commit_nodes = [n for n in graph.nodes.values() if n.node_type == "commit"]
        assert len(commit_nodes) == 2

    @pytest.mark.asyncio
    async def test_index_creates_pr_nodes(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        pr_nodes = [n for n in graph.nodes.values() if n.node_type == "pull_request"]
        assert len(pr_nodes) == 1

    @pytest.mark.asyncio
    async def test_index_creates_issue_nodes(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        issue_nodes = [n for n in graph.nodes.values() if n.node_type == "issue"]
        assert len(issue_nodes) == 1

    @pytest.mark.asyncio
    async def test_index_creates_release_nodes(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        release_nodes = [n for n in graph.nodes.values() if n.node_type == "release"]
        assert len(release_nodes) == 1


class TestGitHubIndexerEdges:
    @pytest.mark.asyncio
    async def test_commit_edges_to_repo(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        repo_edges = [e for e in graph.edges if e.relationship == "has_commit"]
        assert len(repo_edges) == 2

    @pytest.mark.asyncio
    async def test_pr_edge_to_repo(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        pr_edges = [e for e in graph.edges if e.relationship == "has_pull_request"]
        assert len(pr_edges) == 1

    @pytest.mark.asyncio
    async def test_issue_edge_to_repo(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        issue_edges = [e for e in graph.edges if e.relationship == "has_issue"]
        assert len(issue_edges) == 1

    @pytest.mark.asyncio
    async def test_release_edge_to_repo(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        release_edges = [e for e in graph.edges if e.relationship == "has_release"]
        assert len(release_edges) == 1

    @pytest.mark.asyncio
    async def test_author_edges(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        author_edges = [e for e in graph.edges if e.relationship == "authored"]
        assert len(author_edges) == 2


class TestGitHubIndexerAuthors:
    @pytest.mark.asyncio
    async def test_creates_author_nodes(self, indexer: GitHubIndexer) -> None:
        graph = await indexer.index_repository("org", "project")
        author_nodes = [n for n in graph.nodes.values() if n.node_type == "person"]
        assert len(author_nodes) == 2

    @pytest.mark.asyncio
    async def test_deduplicates_authors(self) -> None:
        c = GitHubClient()
        c.add_repository(GitHubRepository(owner="o", name="r"))
        c.add_commits(
            "o",
            "r",
            [
                GitHubCommit(sha="a1", message="m1", author="same_dev"),
                GitHubCommit(sha="a2", message="m2", author="same_dev"),
            ],
        )
        indexer = GitHubIndexer(c)
        graph = await indexer.index_repository("o", "r")
        author_nodes = [n for n in graph.nodes.values() if n.node_type == "person"]
        assert len(author_nodes) == 1


class TestGitHubIndexerEvents:
    @pytest.mark.asyncio
    async def test_emits_indexed_event(self, indexer: GitHubIndexer) -> None:
        await indexer.index_repository("org", "project")
        assert len(indexer.events) == 1
        event = indexer.events[0]
        assert event.owner == "org"
        assert event.repo == "project"
        assert event.commits_indexed == 2

    @pytest.mark.asyncio
    async def test_empty_repo_event(self) -> None:
        c = GitHubClient()
        c.add_repository(GitHubRepository(owner="o", name="empty"))
        indexer = GitHubIndexer(c)
        await indexer.index_repository("o", "empty")
        assert indexer.events[0].commits_indexed == 0
