"""Tests for GitHub to knowledge graph integration."""

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
def full_repo_client() -> GitHubClient:
    c = GitHubClient()
    c.add_repository(
        GitHubRepository(
            owner="acme",
            name="webapp",
            description="ACME Web App",
            language="TypeScript",
            stars=500,
            url="https://github.com/acme/webapp",
        )
    )
    c.add_commits(
        "acme",
        "webapp",
        [
            GitHubCommit(
                sha="a1b2c3d4", message="Initial setup", author="alice", timestamp="2024-01-01"
            ),
            GitHubCommit(
                sha="e5f6g7h8", message="Add user auth", author="bob", timestamp="2024-01-15"
            ),
            GitHubCommit(
                sha="i9j0k1l2", message="Fix login bug", author="alice", timestamp="2024-01-20"
            ),
            GitHubCommit(
                sha="m3n4o5p6", message="Add API docs", author="charlie", timestamp="2024-02-01"
            ),
        ],
    )
    c.add_pull_requests(
        "acme",
        "webapp",
        [
            GitHubPullRequest(
                number=1, title="Setup project structure", state="merged", author="alice"
            ),
            GitHubPullRequest(number=2, title="Implement auth flow", state="merged", author="bob"),
            GitHubPullRequest(number=3, title="Add dark mode", state="open", author="charlie"),
        ],
    )
    c.add_issues(
        "acme",
        "webapp",
        [
            GitHubIssue(number=1, title="Login fails on Safari", state="closed", labels=["bug"]),
            GitHubIssue(number=2, title="Add search feature", state="open", labels=["enhancement"]),
            GitHubIssue(
                number=3, title="Improve performance", state="open", labels=["performance"]
            ),
        ],
    )
    c.add_releases(
        "acme",
        "webapp",
        [
            GitHubRelease(tag="v1.0.0", name="First Release", created_at="2024-01-30"),
            GitHubRelease(tag="v2.0.0-rc1", name="RC1", prerelease=True, created_at="2024-02-15"),
        ],
    )
    return c


class TestGitHubToGraphNodeCreation:
    @pytest.mark.asyncio
    async def test_total_node_count(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        # 1 repo + 4 commits + 3 PRs + 3 issues + 2 releases + 3 authors = 16
        assert len(graph.nodes) == 16

    @pytest.mark.asyncio
    async def test_repo_node_properties(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        repo_node = graph.nodes["repo:acme/webapp"]
        assert repo_node.properties["language"] == "TypeScript"
        assert repo_node.properties["stars"] == 500

    @pytest.mark.asyncio
    async def test_commit_node_properties(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        # Find commit node by sha prefix
        commit_nodes = [n for n in graph.nodes.values() if n.node_type == "commit"]
        assert len(commit_nodes) == 4
        # Check first commit
        init_commit = graph.nodes["commit:a1b2c3d4"]
        assert init_commit.properties["author"] == "alice"

    @pytest.mark.asyncio
    async def test_pr_node_properties(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        pr_node = graph.nodes["pr:acme/webapp#1"]
        assert pr_node.label == "Setup project structure"
        assert pr_node.properties["state"] == "merged"

    @pytest.mark.asyncio
    async def test_issue_node_properties(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        issue_node = graph.nodes["issue:acme/webapp#2"]
        assert issue_node.label == "Add search feature"
        assert issue_node.properties["labels"] == ["enhancement"]

    @pytest.mark.asyncio
    async def test_release_node_properties(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        release_node = graph.nodes["release:acme/webapp@v2.0.0-rc1"]
        assert release_node.properties["prerelease"] is True


class TestGitHubToGraphEdgeCreation:
    @pytest.mark.asyncio
    async def test_total_edge_count(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        # 4 has_commit + 4 authored + 3 has_pull_request + 3 has_issue + 2 has_release = 16
        assert len(graph.edges) == 16

    @pytest.mark.asyncio
    async def test_all_commits_linked_to_repo(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        commit_edges = [e for e in graph.edges if e.relationship == "has_commit"]
        assert len(commit_edges) == 4
        assert all(e.source_id == "repo:acme/webapp" for e in commit_edges)

    @pytest.mark.asyncio
    async def test_authored_edges(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        authored = [e for e in graph.edges if e.relationship == "authored"]
        assert len(authored) == 4

    @pytest.mark.asyncio
    async def test_author_deduplication(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        graph = await indexer.index_repository("acme", "webapp")
        person_nodes = [n for n in graph.nodes.values() if n.node_type == "person"]
        # alice, bob, charlie = 3 unique authors
        assert len(person_nodes) == 3


class TestGitHubToGraphEvents:
    @pytest.mark.asyncio
    async def test_event_emitted(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        await indexer.index_repository("acme", "webapp")
        assert len(indexer.events) == 1
        event = indexer.events[0]
        assert event.owner == "acme"
        assert event.repo == "webapp"
        assert event.commits_indexed == 4

    @pytest.mark.asyncio
    async def test_graph_property_accessible(self, full_repo_client: GitHubClient) -> None:
        indexer = GitHubIndexer(full_repo_client)
        await indexer.index_repository("acme", "webapp")
        assert len(indexer.graph.nodes) == 16
        assert len(indexer.graph.edges) == 16
