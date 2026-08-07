"""Personal AI Runtime - top-level orchestrator.

Combines all subsystems into a unified runtime:
- GitHub integration
- Workspace indexing
- Notes management
- Task management
- Knowledge graph
- Project memory
- Metrics
"""

from typing import Any

import structlog

from sona_research.domain.github_models import GitHubRepository
from sona_research.domain.personal_models import (
    KnowledgeNode,
    Note,
    NoteType,
    Task,
    TaskPriority,
    TaskStatus,
)
from sona_research.domain.workspace_models import IndexedDocument
from sona_research.infrastructure.github.client import GitHubClient
from sona_research.infrastructure.github.indexer import GitHubIndexer
from sona_research.infrastructure.knowledge_graph.runtime import KnowledgeGraphRuntime
from sona_research.infrastructure.metrics import PersonalAIMetrics
from sona_research.infrastructure.notes.runtime import NotesRuntime
from sona_research.infrastructure.project_memory import ProjectMemory
from sona_research.infrastructure.tasks.runtime import TasksRuntime
from sona_research.infrastructure.workspace.indexer import WorkspaceIndexer
from sona_research.infrastructure.workspace.scanner import WorkspaceScanner

logger = structlog.get_logger()


class PersonalAIRuntime:
    """Unified Personal AI Runtime combining all subsystems.

    Provides a single entry point for all personal AI operations,
    coordinating between notes, tasks, knowledge graph, workspace,
    and GitHub integrations.
    """

    def __init__(
        self,
        notes: NotesRuntime,
        tasks: TasksRuntime,
        knowledge_graph: KnowledgeGraphRuntime,
        workspace_scanner: WorkspaceScanner,
        workspace_indexer: WorkspaceIndexer,
        github_client: GitHubClient,
        project_memory: ProjectMemory,
        metrics: PersonalAIMetrics,
    ) -> None:
        """Initialize the Personal AI Runtime.

        Args:
            notes: Notes runtime instance.
            tasks: Tasks runtime instance.
            knowledge_graph: Knowledge graph runtime instance.
            workspace_scanner: Workspace scanner instance.
            workspace_indexer: Workspace indexer instance.
            github_client: GitHub client instance.
            project_memory: Project memory instance.
            metrics: Metrics collector instance.
        """
        self.notes = notes
        self.tasks = tasks
        self.knowledge_graph = knowledge_graph
        self.workspace_scanner = workspace_scanner
        self.workspace_indexer = workspace_indexer
        self.github_client = github_client
        self.project_memory = project_memory
        self.metrics = metrics
        self._github_indexer = GitHubIndexer(github_client)

    # --- Note Operations ---

    async def create_note(
        self,
        title: str,
        content: str,
        note_type: NoteType = NoteType.QUICK,
        tags: list[str] | None = None,
    ) -> Note:
        """Create a note and track metrics.

        Args:
            title: Note title.
            content: Note content.
            note_type: Type of note.
            tags: Optional tags.

        Returns:
            The created Note.
        """
        note = await self.notes.create_note(title, content, note_type, tags)
        self.metrics.record_note_created()
        self.metrics.update_notes_count(await self.notes.count())
        return note

    async def search_notes(self, query: str) -> list[Note]:
        """Search notes with metrics tracking.

        Args:
            query: Search query.

        Returns:
            Matching notes.
        """
        self.metrics.record_search_performed("notes")
        return await self.notes.search_notes(query)

    # --- Task Operations ---

    async def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee: str = "",
        due_date: str = "",
        tags: list[str] | None = None,
    ) -> Task:
        """Create a task and track metrics.

        Args:
            title: Task title.
            description: Task description.
            priority: Task priority.
            assignee: Person assigned.
            due_date: Due date string.
            tags: Optional tags.

        Returns:
            The created Task.
        """
        task = await self.tasks.create_task(title, description, priority, assignee, due_date, tags)
        self.metrics.record_task_created(priority.value)
        count = await self.tasks.count()
        self.metrics.update_tasks_count(count)
        return task

    async def complete_task(self, task_id: str) -> Task:
        """Complete a task and track metrics.

        Args:
            task_id: The task identifier.

        Returns:
            The completed Task.
        """
        task = await self.tasks.complete_task(task_id)
        done_count = await self.tasks.count(TaskStatus.DONE)
        self.metrics.update_tasks_count(done_count, "done")
        return task

    # --- Knowledge Graph Operations ---

    async def add_knowledge(
        self, label: str, node_type: str, properties: dict[str, Any] | None = None
    ) -> KnowledgeNode:
        """Add a knowledge node and track metrics.

        Args:
            label: Node label.
            node_type: Type of knowledge node.
            properties: Optional properties.

        Returns:
            The created KnowledgeNode.
        """
        node = KnowledgeNode(
            node_id=f"{node_type}:{label.lower().replace(' ', '_')}",
            label=label,
            node_type=node_type,
            properties=properties or {},
        )
        await self.knowledge_graph.add_node(node)
        self.metrics.record_graph_node_added(node_type)
        node_count = await self.knowledge_graph.node_count()
        edge_count = await self.knowledge_graph.edge_count()
        self.metrics.update_graph_size(node_count, edge_count)
        return node

    # --- Workspace Operations ---

    async def index_workspace(self, root_path: str = "/") -> list[IndexedDocument]:
        """Scan and index workspace documents.

        Args:
            root_path: Root path to scan.

        Returns:
            List of indexed documents.
        """
        documents = await self.workspace_scanner.scan(root_path)
        indexed = await self.workspace_indexer.index_batch(documents)

        for doc in indexed:
            self.metrics.record_document_indexed(doc.format.value)

        return indexed

    async def search_workspace(self, query: str) -> list[IndexedDocument]:
        """Search indexed workspace documents.

        Args:
            query: Search query.

        Returns:
            Matching indexed documents.
        """
        self.metrics.record_search_performed("workspace")
        return await self.workspace_indexer.search(query)

    # --- GitHub Operations ---

    async def index_github_repository(self, owner: str, repo: str) -> dict[str, int]:
        """Index a GitHub repository into the knowledge graph.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            Dictionary with indexing statistics.
        """
        self.metrics.record_github_operation("index_repository")
        graph = await self._github_indexer.index_repository(owner, repo)

        node_count = len(graph.nodes)
        edge_count = len(graph.edges)

        return {
            "nodes_indexed": node_count,
            "edges_created": edge_count,
        }

    async def get_repository_info(self, owner: str, repo: str) -> GitHubRepository:
        """Get repository information.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            GitHubRepository instance.
        """
        self.metrics.record_github_operation("get_repository")
        return await self.github_client.get_repository(owner, repo)

    # --- Summary Operations ---

    async def get_runtime_summary(self) -> dict[str, object]:
        """Get a complete summary of the runtime state.

        Returns:
            Dictionary with counts and status of all subsystems.
        """
        notes_count = await self.notes.count()
        tasks_count = await self.tasks.count()
        node_count = await self.knowledge_graph.node_count()
        edge_count = await self.knowledge_graph.edge_count()
        project_summary = await self.project_memory.get_summary()

        return {
            "notes": notes_count,
            "tasks": tasks_count,
            "knowledge_graph": {
                "nodes": node_count,
                "edges": edge_count,
            },
            "project_memory": project_summary,
        }
