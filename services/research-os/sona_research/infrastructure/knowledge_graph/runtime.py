"""Knowledge graph runtime for personal knowledge management.

Provides a personal knowledge graph with nodes, edges, traversal,
queries, and path finding.
"""

from collections import deque

import structlog

from sona_research.domain.events import KnowledgeGraphUpdatedEvent
from sona_research.domain.personal_models import (
    KnowledgeEdge,
    KnowledgeGraph,
    KnowledgeNode,
)

logger = structlog.get_logger()


class KnowledgeGraphRuntime:
    """Runtime for managing a personal knowledge graph.

    Supports adding nodes and edges, querying by type, finding neighbors,
    path finding between nodes, and merging duplicates.
    """

    def __init__(self) -> None:
        """Initialize the knowledge graph runtime."""
        self._graph = KnowledgeGraph()
        self._events: list[KnowledgeGraphUpdatedEvent] = []

    @property
    def graph(self) -> KnowledgeGraph:
        """Access the underlying knowledge graph."""
        return self._graph

    @property
    def events(self) -> list[KnowledgeGraphUpdatedEvent]:
        """Access emitted events."""
        return self._events

    async def add_node(self, node: KnowledgeNode) -> KnowledgeNode:
        """Add a node to the knowledge graph.

        Args:
            node: The node to add.

        Returns:
            The added node.
        """
        self._graph.nodes[node.node_id] = node
        self._events.append(KnowledgeGraphUpdatedEvent(nodes_added=1, edges_added=0))
        logger.info("knowledge_graph.node_added", node_id=node.node_id)
        return node

    async def add_edge(self, edge: KnowledgeEdge) -> KnowledgeEdge:
        """Add an edge to the knowledge graph.

        Args:
            edge: The edge to add.

        Returns:
            The added edge.

        Raises:
            ValueError: If source or target node does not exist.
        """
        if edge.source_id not in self._graph.nodes:
            raise ValueError(f"Source node not found: {edge.source_id}")
        if edge.target_id not in self._graph.nodes:
            raise ValueError(f"Target node not found: {edge.target_id}")

        self._graph.edges.append(edge)
        self._events.append(KnowledgeGraphUpdatedEvent(nodes_added=0, edges_added=1))
        logger.info(
            "knowledge_graph.edge_added",
            source=edge.source_id,
            target=edge.target_id,
            relationship=edge.relationship,
        )
        return edge

    async def get_node(self, node_id: str) -> KnowledgeNode | None:
        """Get a node by ID.

        Args:
            node_id: The node identifier.

        Returns:
            The KnowledgeNode if found, None otherwise.
        """
        return self._graph.nodes.get(node_id)

    async def get_neighbors(
        self, node_id: str, relationship: str | None = None
    ) -> list[KnowledgeNode]:
        """Get all neighbors of a node (connected by edges).

        Args:
            node_id: The node to find neighbors for.
            relationship: Optional relationship type filter.

        Returns:
            List of neighboring nodes.
        """
        neighbor_ids: set[str] = set()

        for edge in self._graph.edges:
            if edge.source_id == node_id:
                if relationship is None or edge.relationship == relationship:
                    neighbor_ids.add(edge.target_id)
            elif edge.target_id == node_id:
                if relationship is None or edge.relationship == relationship:
                    neighbor_ids.add(edge.source_id)

        return [self._graph.nodes[nid] for nid in neighbor_ids if nid in self._graph.nodes]

    async def find_path(self, start_id: str, end_id: str, max_depth: int = 10) -> list[str] | None:
        """Find a path between two nodes using BFS.

        Args:
            start_id: Starting node ID.
            end_id: Target node ID.
            max_depth: Maximum search depth.

        Returns:
            List of node IDs forming the path, or None if no path exists.
        """
        if start_id not in self._graph.nodes or end_id not in self._graph.nodes:
            return None

        if start_id == end_id:
            return [start_id]

        # Build adjacency list
        adjacency: dict[str, set[str]] = {}
        for edge in self._graph.edges:
            adjacency.setdefault(edge.source_id, set()).add(edge.target_id)
            adjacency.setdefault(edge.target_id, set()).add(edge.source_id)

        # BFS
        queue: deque[list[str]] = deque([[start_id]])
        visited: set[str] = {start_id}

        while queue:
            path = queue.popleft()
            if len(path) > max_depth:
                continue

            current = path[-1]
            for neighbor in adjacency.get(current, set()):
                if neighbor == end_id:
                    return [*path, neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append([*path, neighbor])

        return None

    async def query_by_type(self, node_type: str) -> list[KnowledgeNode]:
        """Query all nodes of a specific type.

        Args:
            node_type: The type of nodes to retrieve.

        Returns:
            List of nodes matching the type.
        """
        return [node for node in self._graph.nodes.values() if node.node_type == node_type]

    async def query_by_property(self, key: str, value: object) -> list[KnowledgeNode]:
        """Query nodes by a property value.

        Args:
            key: Property key to search.
            value: Expected property value.

        Returns:
            List of nodes with matching property.
        """
        return [node for node in self._graph.nodes.values() if node.properties.get(key) == value]

    async def get_edges_for_node(self, node_id: str) -> list[KnowledgeEdge]:
        """Get all edges connected to a node.

        Args:
            node_id: The node identifier.

        Returns:
            List of edges involving this node.
        """
        return [
            edge
            for edge in self._graph.edges
            if edge.source_id == node_id or edge.target_id == node_id
        ]

    async def merge_nodes(self, keep_id: str, remove_id: str) -> KnowledgeNode | None:
        """Merge two nodes, keeping one and removing the other.

        All edges from the removed node are redirected to the kept node.

        Args:
            keep_id: ID of the node to keep.
            remove_id: ID of the node to remove.

        Returns:
            The kept node, or None if either node doesn't exist.
        """
        keep_node = self._graph.nodes.get(keep_id)
        remove_node = self._graph.nodes.get(remove_id)

        if keep_node is None or remove_node is None:
            return None

        # Redirect edges
        new_edges: list[KnowledgeEdge] = []
        for edge in self._graph.edges:
            source = edge.source_id
            target = edge.target_id

            if source == remove_id:
                source = keep_id
            if target == remove_id:
                target = keep_id

            # Skip self-loops created by merge
            if source == target:
                continue

            new_edge = KnowledgeEdge(
                source_id=source,
                target_id=target,
                relationship=edge.relationship,
                weight=edge.weight,
                metadata=edge.metadata,
            )
            new_edges.append(new_edge)

        self._graph.edges = new_edges

        # Remove the node
        del self._graph.nodes[remove_id]

        logger.info(
            "knowledge_graph.nodes_merged",
            keep_id=keep_id,
            remove_id=remove_id,
        )
        return keep_node

    async def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges.

        Args:
            node_id: The node identifier.

        Returns:
            True if the node was found and removed.
        """
        if node_id not in self._graph.nodes:
            return False

        del self._graph.nodes[node_id]
        self._graph.edges = [
            e for e in self._graph.edges if e.source_id != node_id and e.target_id != node_id
        ]
        return True

    async def export_summary(self) -> dict[str, object]:
        """Export a summary of the knowledge graph.

        Returns:
            Dictionary with node count, edge count, type breakdown,
            and relationship breakdown.
        """
        type_counts: dict[str, int] = {}
        for node in self._graph.nodes.values():
            type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1

        rel_counts: dict[str, int] = {}
        for edge in self._graph.edges:
            rel_counts[edge.relationship] = rel_counts.get(edge.relationship, 0) + 1

        return {
            "total_nodes": len(self._graph.nodes),
            "total_edges": len(self._graph.edges),
            "node_types": type_counts,
            "relationships": rel_counts,
        }

    async def node_count(self) -> int:
        """Get total number of nodes."""
        return len(self._graph.nodes)

    async def edge_count(self) -> int:
        """Get total number of edges."""
        return len(self._graph.edges)
