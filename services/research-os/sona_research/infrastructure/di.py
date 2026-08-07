"""Dependency injection factory for the Personal AI Runtime.

Creates fully-configured runtime instances with all dependencies wired.
"""

from sona_research.infrastructure.github.client import GitHubClient
from sona_research.infrastructure.knowledge_graph.runtime import KnowledgeGraphRuntime
from sona_research.infrastructure.metrics import PersonalAIMetrics
from sona_research.infrastructure.notes.runtime import NotesRuntime
from sona_research.infrastructure.personal_ai_runtime import PersonalAIRuntime
from sona_research.infrastructure.project_memory import ProjectMemory
from sona_research.infrastructure.tasks.runtime import TasksRuntime
from sona_research.infrastructure.workspace.indexer import WorkspaceIndexer
from sona_research.infrastructure.workspace.scanner import WorkspaceScanner


def create_personal_ai_runtime() -> PersonalAIRuntime:
    """Create a fully-configured Personal AI Runtime instance.

    Wires all dependencies and returns a ready-to-use runtime.

    Returns:
        A configured PersonalAIRuntime instance.
    """
    notes = NotesRuntime()
    tasks = TasksRuntime()
    knowledge_graph = KnowledgeGraphRuntime()
    workspace_scanner = WorkspaceScanner()
    workspace_indexer = WorkspaceIndexer()
    github_client = GitHubClient()
    project_memory = ProjectMemory(knowledge_graph)
    metrics = PersonalAIMetrics()

    return PersonalAIRuntime(
        notes=notes,
        tasks=tasks,
        knowledge_graph=knowledge_graph,
        workspace_scanner=workspace_scanner,
        workspace_indexer=workspace_indexer,
        github_client=github_client,
        project_memory=project_memory,
        metrics=metrics,
    )
