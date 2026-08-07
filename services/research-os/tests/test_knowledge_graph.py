"""Tests for knowledge graph runtime."""

import pytest

from sona_research.domain.personal_models import KnowledgeEdge, KnowledgeNode
from sona_research.infrastructure.knowledge_graph.runtime import KnowledgeGraphRuntime


@pytest.fixture
def kg() -> KnowledgeGraphRuntime:
    return KnowledgeGraphRuntime()


class TestKnowledgeGraphNodes:
    @pytest.mark.asyncio
    async def test_add_node(self, kg: KnowledgeGraphRuntime) -> None:
        node = KnowledgeNode(node_id="n1", label="Python", node_type="concept")
        result = await kg.add_node(node)
        assert result.node_id == "n1"
        assert await kg.node_count() == 1

    @pytest.mark.asyncio
    async def test_get_node(self, kg: KnowledgeGraphRuntime) -> None:
        node = KnowledgeNode(node_id="n1", label="Python", node_type="concept")
        await kg.add_node(node)
        retrieved = await kg.get_node("n1")
        assert retrieved is not None
        assert retrieved.label == "Python"

    @pytest.mark.asyncio
    async def test_get_nonexistent_node(self, kg: KnowledgeGraphRuntime) -> None:
        result = await kg.get_node("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_remove_node(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="n1", label="A", node_type="t"))
        removed = await kg.remove_node("n1")
        assert removed is True
        assert await kg.node_count() == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, kg: KnowledgeGraphRuntime) -> None:
        removed = await kg.remove_node("nope")
        assert removed is False

    @pytest.mark.asyncio
    async def test_remove_node_removes_edges(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        await kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relationship="r"))
        await kg.remove_node("a")
        assert await kg.edge_count() == 0


class TestKnowledgeGraphEdges:
    @pytest.mark.asyncio
    async def test_add_edge(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        edge = KnowledgeEdge(source_id="a", target_id="b", relationship="relates")
        result = await kg.add_edge(edge)
        assert result.relationship == "relates"
        assert await kg.edge_count() == 1

    @pytest.mark.asyncio
    async def test_add_edge_missing_source(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        with pytest.raises(ValueError, match="Source node not found"):
            await kg.add_edge(KnowledgeEdge(source_id="x", target_id="b", relationship="r"))

    @pytest.mark.asyncio
    async def test_add_edge_missing_target(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        with pytest.raises(ValueError, match="Target node not found"):
            await kg.add_edge(KnowledgeEdge(source_id="a", target_id="x", relationship="r"))

    @pytest.mark.asyncio
    async def test_get_edges_for_node(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="c", label="C", node_type="t"))
        await kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relationship="r1"))
        await kg.add_edge(KnowledgeEdge(source_id="a", target_id="c", relationship="r2"))
        edges = await kg.get_edges_for_node("a")
        assert len(edges) == 2


class TestKnowledgeGraphNeighbors:
    @pytest.mark.asyncio
    async def test_get_neighbors(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="c", label="C", node_type="t"))
        await kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relationship="r"))
        await kg.add_edge(KnowledgeEdge(source_id="c", target_id="a", relationship="r"))
        neighbors = await kg.get_neighbors("a")
        assert len(neighbors) == 2

    @pytest.mark.asyncio
    async def test_get_neighbors_filtered(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="c", label="C", node_type="t"))
        await kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relationship="knows"))
        await kg.add_edge(KnowledgeEdge(source_id="a", target_id="c", relationship="works_with"))
        neighbors = await kg.get_neighbors("a", relationship="knows")
        assert len(neighbors) == 1
        assert neighbors[0].node_id == "b"


class TestKnowledgeGraphPathFinding:
    @pytest.mark.asyncio
    async def test_find_direct_path(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        await kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relationship="r"))
        path = await kg.find_path("a", "b")
        assert path == ["a", "b"]

    @pytest.mark.asyncio
    async def test_find_indirect_path(self, kg: KnowledgeGraphRuntime) -> None:
        for nid in ["a", "b", "c"]:
            await kg.add_node(KnowledgeNode(node_id=nid, label=nid, node_type="t"))
        await kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relationship="r"))
        await kg.add_edge(KnowledgeEdge(source_id="b", target_id="c", relationship="r"))
        path = await kg.find_path("a", "c")
        assert path == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_no_path(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        path = await kg.find_path("a", "b")
        assert path is None

    @pytest.mark.asyncio
    async def test_same_node_path(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        path = await kg.find_path("a", "a")
        assert path == ["a"]

    @pytest.mark.asyncio
    async def test_nonexistent_node(self, kg: KnowledgeGraphRuntime) -> None:
        path = await kg.find_path("x", "y")
        assert path is None


class TestKnowledgeGraphQueries:
    @pytest.mark.asyncio
    async def test_query_by_type(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="p1", label="Alice", node_type="person"))
        await kg.add_node(KnowledgeNode(node_id="p2", label="Bob", node_type="person"))
        await kg.add_node(KnowledgeNode(node_id="c1", label="Python", node_type="concept"))
        people = await kg.query_by_type("person")
        assert len(people) == 2

    @pytest.mark.asyncio
    async def test_query_by_property(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(
            KnowledgeNode(
                node_id="p1", label="Alice", node_type="person", properties={"role": "developer"}
            )
        )
        await kg.add_node(
            KnowledgeNode(
                node_id="p2", label="Bob", node_type="person", properties={"role": "manager"}
            )
        )
        devs = await kg.query_by_property("role", "developer")
        assert len(devs) == 1
        assert devs[0].label == "Alice"


class TestKnowledgeGraphMerge:
    @pytest.mark.asyncio
    async def test_merge_nodes(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="c", label="C", node_type="t"))
        await kg.add_edge(KnowledgeEdge(source_id="b", target_id="c", relationship="r"))
        result = await kg.merge_nodes("a", "b")
        assert result is not None
        assert await kg.node_count() == 2
        # Edge should now point from a to c
        edges = await kg.get_edges_for_node("a")
        assert len(edges) == 1
        assert edges[0].target_id == "c"

    @pytest.mark.asyncio
    async def test_merge_nonexistent(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        result = await kg.merge_nodes("a", "nonexistent")
        assert result is None


class TestKnowledgeGraphSummary:
    @pytest.mark.asyncio
    async def test_export_summary(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="p1", label="A", node_type="person"))
        await kg.add_node(KnowledgeNode(node_id="c1", label="B", node_type="concept"))
        await kg.add_edge(KnowledgeEdge(source_id="p1", target_id="c1", relationship="knows"))
        summary = await kg.export_summary()
        assert summary["total_nodes"] == 2
        assert summary["total_edges"] == 1
        assert summary["node_types"] == {"person": 1, "concept": 1}
        assert summary["relationships"] == {"knows": 1}

    @pytest.mark.asyncio
    async def test_events_emitted(self, kg: KnowledgeGraphRuntime) -> None:
        await kg.add_node(KnowledgeNode(node_id="a", label="A", node_type="t"))
        await kg.add_node(KnowledgeNode(node_id="b", label="B", node_type="t"))
        await kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relationship="r"))
        assert len(kg.events) == 3  # 2 node events + 1 edge event
