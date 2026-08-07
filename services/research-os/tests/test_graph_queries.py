"""Tests for knowledge graph queries and traversal."""

import pytest

from sona_research.domain.personal_models import KnowledgeEdge, KnowledgeNode
from sona_research.infrastructure.knowledge_graph.runtime import KnowledgeGraphRuntime


@pytest.fixture
async def populated_graph() -> KnowledgeGraphRuntime:
    """Create a graph with a project structure."""
    kg = KnowledgeGraphRuntime()

    # Add nodes
    nodes = [
        KnowledgeNode(node_id="proj", label="My Project", node_type="project"),
        KnowledgeNode(node_id="auth", label="Auth Module", node_type="module"),
        KnowledgeNode(node_id="api", label="API Module", node_type="module"),
        KnowledgeNode(node_id="db", label="Database", node_type="infrastructure"),
        KnowledgeNode(
            node_id="alice", label="Alice", node_type="person", properties={"role": "lead"}
        ),
        KnowledgeNode(
            node_id="bob", label="Bob", node_type="person", properties={"role": "developer"}
        ),
        KnowledgeNode(node_id="python", label="Python", node_type="technology"),
        KnowledgeNode(node_id="fastapi", label="FastAPI", node_type="technology"),
        KnowledgeNode(node_id="postgres", label="PostgreSQL", node_type="technology"),
    ]
    for node in nodes:
        await kg.add_node(node)

    # Add edges
    edges = [
        KnowledgeEdge(source_id="proj", target_id="auth", relationship="contains"),
        KnowledgeEdge(source_id="proj", target_id="api", relationship="contains"),
        KnowledgeEdge(source_id="proj", target_id="db", relationship="uses"),
        KnowledgeEdge(source_id="alice", target_id="proj", relationship="leads"),
        KnowledgeEdge(source_id="bob", target_id="auth", relationship="works_on"),
        KnowledgeEdge(source_id="bob", target_id="api", relationship="works_on"),
        KnowledgeEdge(source_id="api", target_id="fastapi", relationship="built_with"),
        KnowledgeEdge(source_id="auth", target_id="python", relationship="built_with"),
        KnowledgeEdge(source_id="db", target_id="postgres", relationship="built_with"),
    ]
    for edge in edges:
        await kg.add_edge(edge)

    return kg


class TestGraphQueryByType:
    @pytest.mark.asyncio
    async def test_query_modules(self, populated_graph: KnowledgeGraphRuntime) -> None:
        modules = await populated_graph.query_by_type("module")
        assert len(modules) == 2

    @pytest.mark.asyncio
    async def test_query_people(self, populated_graph: KnowledgeGraphRuntime) -> None:
        people = await populated_graph.query_by_type("person")
        assert len(people) == 2

    @pytest.mark.asyncio
    async def test_query_technologies(self, populated_graph: KnowledgeGraphRuntime) -> None:
        techs = await populated_graph.query_by_type("technology")
        assert len(techs) == 3

    @pytest.mark.asyncio
    async def test_query_empty_type(self, populated_graph: KnowledgeGraphRuntime) -> None:
        result = await populated_graph.query_by_type("nonexistent")
        assert result == []


class TestGraphQueryByProperty:
    @pytest.mark.asyncio
    async def test_query_by_role(self, populated_graph: KnowledgeGraphRuntime) -> None:
        leads = await populated_graph.query_by_property("role", "lead")
        assert len(leads) == 1
        assert leads[0].label == "Alice"

    @pytest.mark.asyncio
    async def test_query_developers(self, populated_graph: KnowledgeGraphRuntime) -> None:
        devs = await populated_graph.query_by_property("role", "developer")
        assert len(devs) == 1
        assert devs[0].label == "Bob"

    @pytest.mark.asyncio
    async def test_query_no_match(self, populated_graph: KnowledgeGraphRuntime) -> None:
        result = await populated_graph.query_by_property("role", "manager")
        assert result == []


class TestGraphTraversal:
    @pytest.mark.asyncio
    async def test_project_neighbors(self, populated_graph: KnowledgeGraphRuntime) -> None:
        neighbors = await populated_graph.get_neighbors("proj")
        assert len(neighbors) == 4  # auth, api, db, alice

    @pytest.mark.asyncio
    async def test_filtered_neighbors(self, populated_graph: KnowledgeGraphRuntime) -> None:
        contained = await populated_graph.get_neighbors("proj", relationship="contains")
        assert len(contained) == 2

    @pytest.mark.asyncio
    async def test_bob_works_on(self, populated_graph: KnowledgeGraphRuntime) -> None:
        neighbors = await populated_graph.get_neighbors("bob", relationship="works_on")
        labels = {n.label for n in neighbors}
        assert "Auth Module" in labels
        assert "API Module" in labels


class TestGraphPathFinding:
    @pytest.mark.asyncio
    async def test_direct_path(self, populated_graph: KnowledgeGraphRuntime) -> None:
        path = await populated_graph.find_path("proj", "auth")
        assert path is not None
        assert path == ["proj", "auth"]

    @pytest.mark.asyncio
    async def test_indirect_path(self, populated_graph: KnowledgeGraphRuntime) -> None:
        path = await populated_graph.find_path("alice", "auth")
        assert path is not None
        assert len(path) == 3  # alice -> proj -> auth

    @pytest.mark.asyncio
    async def test_longer_path(self, populated_graph: KnowledgeGraphRuntime) -> None:
        path = await populated_graph.find_path("alice", "postgres")
        assert path is not None
        assert len(path) >= 3

    @pytest.mark.asyncio
    async def test_bob_to_fastapi(self, populated_graph: KnowledgeGraphRuntime) -> None:
        path = await populated_graph.find_path("bob", "fastapi")
        assert path is not None
        assert "api" in path


class TestGraphSummary:
    @pytest.mark.asyncio
    async def test_summary_counts(self, populated_graph: KnowledgeGraphRuntime) -> None:
        summary = await populated_graph.export_summary()
        assert summary["total_nodes"] == 9
        assert summary["total_edges"] == 9

    @pytest.mark.asyncio
    async def test_summary_types(self, populated_graph: KnowledgeGraphRuntime) -> None:
        summary = await populated_graph.export_summary()
        node_types = summary["node_types"]
        assert node_types["module"] == 2  # type: ignore[index]
        assert node_types["person"] == 2  # type: ignore[index]
        assert node_types["technology"] == 3  # type: ignore[index]

    @pytest.mark.asyncio
    async def test_summary_relationships(self, populated_graph: KnowledgeGraphRuntime) -> None:
        summary = await populated_graph.export_summary()
        rels = summary["relationships"]
        assert rels["contains"] == 2  # type: ignore[index]
        assert rels["built_with"] == 3  # type: ignore[index]
