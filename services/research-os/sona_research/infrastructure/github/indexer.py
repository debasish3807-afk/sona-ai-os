"""GitHub repository indexer.

Indexes a repository's history into the knowledge system, building
a knowledge graph from commits, PRs, issues, and releases.
"""

import structlog

from sona_research.domain.events import RepositoryIndexedEvent
from sona_research.domain.github_models import (
    GitHubCommit,
    GitHubIssue,
    GitHubPullRequest,
    GitHubRelease,
    GitHubRepository,
)
from sona_research.domain.personal_models import (
    KnowledgeEdge,
    KnowledgeGraph,
    KnowledgeNode,
)
from sona_research.infrastructure.github.client import GitHubClient

logger = structlog.get_logger()


class GitHubIndexer:
    """Index GitHub repository data into a knowledge graph."""

    def __init__(self, client: GitHubClient) -> None:
        """Initialize the indexer with a GitHub client."""
        self._client = client
        self._graph = KnowledgeGraph()
        self._events: list[RepositoryIndexedEvent] = []

    @property
    def graph(self) -> KnowledgeGraph:
        """Access the built knowledge graph."""
        return self._graph

    @property
    def events(self) -> list[RepositoryIndexedEvent]:
        """Access emitted events."""
        return self._events

    async def index_repository(self, owner: str, repo: str) -> KnowledgeGraph:
        """Index an entire repository into the knowledge graph.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            The built knowledge graph.
        """
        logger.info("github_indexer.index_repository", owner=owner, repo=repo)

        repository = await self._client.get_repository(owner, repo)
        self._index_repo_node(repository)

        commits = await self._client.list_commits(owner, repo)
        for commit in commits:
            self._index_commit(repository, commit)

        prs = await self._client.list_pull_requests(owner, repo, state="all")
        for pr in prs:
            self._index_pull_request(repository, pr)

        issues = await self._client.list_issues(owner, repo, state="all")
        for issue in issues:
            self._index_issue(repository, issue)

        releases = await self._client.list_releases(owner, repo)
        for release in releases:
            self._index_release(repository, release)

        event = RepositoryIndexedEvent(
            owner=owner,
            repo=repo,
            commits_indexed=len(commits),
        )
        self._events.append(event)

        logger.info(
            "github_indexer.index_complete",
            nodes=len(self._graph.nodes),
            edges=len(self._graph.edges),
        )
        return self._graph

    def _index_repo_node(self, repo: GitHubRepository) -> None:
        """Add the repository as a node."""
        node = KnowledgeNode(
            node_id=f"repo:{repo.owner}/{repo.name}",
            label=f"{repo.owner}/{repo.name}",
            node_type="repository",
            properties={
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stars,
                "default_branch": repo.default_branch,
                "url": repo.url,
            },
        )
        self._graph.nodes[node.node_id] = node

    def _index_commit(self, repo: GitHubRepository, commit: GitHubCommit) -> None:
        """Add a commit as a node connected to the repository."""
        node = KnowledgeNode(
            node_id=f"commit:{commit.sha[:8]}",
            label=commit.message[:80],
            node_type="commit",
            properties={
                "sha": commit.sha,
                "author": commit.author,
                "timestamp": commit.timestamp,
                "files_changed": commit.files_changed,
                "additions": commit.additions,
                "deletions": commit.deletions,
            },
        )
        self._graph.nodes[node.node_id] = node

        edge = KnowledgeEdge(
            source_id=f"repo:{repo.owner}/{repo.name}",
            target_id=node.node_id,
            relationship="has_commit",
        )
        self._graph.edges.append(edge)

        # Link author
        author_id = f"author:{commit.author}"
        if author_id not in self._graph.nodes:
            author_node = KnowledgeNode(
                node_id=author_id,
                label=commit.author,
                node_type="person",
            )
            self._graph.nodes[author_id] = author_node

        author_edge = KnowledgeEdge(
            source_id=author_id,
            target_id=node.node_id,
            relationship="authored",
        )
        self._graph.edges.append(author_edge)

    def _index_pull_request(self, repo: GitHubRepository, pr: GitHubPullRequest) -> None:
        """Add a pull request as a node connected to the repository."""
        node = KnowledgeNode(
            node_id=f"pr:{repo.owner}/{repo.name}#{pr.number}",
            label=pr.title,
            node_type="pull_request",
            properties={
                "number": pr.number,
                "state": pr.state,
                "author": pr.author,
                "branch": pr.branch,
                "base": pr.base,
                "created_at": pr.created_at,
            },
        )
        self._graph.nodes[node.node_id] = node

        edge = KnowledgeEdge(
            source_id=f"repo:{repo.owner}/{repo.name}",
            target_id=node.node_id,
            relationship="has_pull_request",
        )
        self._graph.edges.append(edge)

    def _index_issue(self, repo: GitHubRepository, issue: GitHubIssue) -> None:
        """Add an issue as a node connected to the repository."""
        node = KnowledgeNode(
            node_id=f"issue:{repo.owner}/{repo.name}#{issue.number}",
            label=issue.title,
            node_type="issue",
            properties={
                "number": issue.number,
                "state": issue.state,
                "labels": issue.labels,
                "assignee": issue.assignee,
            },
        )
        self._graph.nodes[node.node_id] = node

        edge = KnowledgeEdge(
            source_id=f"repo:{repo.owner}/{repo.name}",
            target_id=node.node_id,
            relationship="has_issue",
        )
        self._graph.edges.append(edge)

    def _index_release(self, repo: GitHubRepository, release: GitHubRelease) -> None:
        """Add a release as a node connected to the repository."""
        node = KnowledgeNode(
            node_id=f"release:{repo.owner}/{repo.name}@{release.tag}",
            label=release.name or release.tag,
            node_type="release",
            properties={
                "tag": release.tag,
                "created_at": release.created_at,
                "prerelease": release.prerelease,
            },
        )
        self._graph.nodes[node.node_id] = node

        edge = KnowledgeEdge(
            source_id=f"repo:{repo.owner}/{repo.name}",
            target_id=node.node_id,
            relationship="has_release",
        )
        self._graph.edges.append(edge)
