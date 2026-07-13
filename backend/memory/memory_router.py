"""Memory router — routes entries to appropriate memory type."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger

from .memory_types import (
    ConversationMemory,
    EpisodicMemory,
    KnowledgeMemory,
    LongTermMemory,
    SemanticMemory,
    WorkingMemory,
)

logger = get_logger(__name__)


class MemoryRouter:
    """Routes memory entries to the appropriate memory store."""

    def __init__(
        self,
        working: WorkingMemory,
        conversation: ConversationMemory,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        long_term: LongTermMemory,
        knowledge: KnowledgeMemory,
    ) -> None:
        self._working = working
        self._conversation = conversation
        self._episodic = episodic
        self._semantic = semantic
        self._long_term = long_term
        self._knowledge = knowledge

    def route(self, content: str, memory_type_hint: str | None = None) -> str:
        """Route content to the appropriate memory store.

        Args:
            content: The content to store.
            memory_type_hint: Optional hint for which store to use.

        Returns:
            Name of the store that was used.
        """
        store_name = memory_type_hint or self._infer_type(content)

        if store_name == "working":
            self._working.store("latest", content)
        elif store_name == "episodic":
            self._episodic.store_episode(event=content, context="routed", outcome="stored")
        elif store_name == "semantic":
            self._semantic.store_fact(subject=content, predicate="stored_as", obj="fact")
        elif store_name == "long_term":
            self._long_term.store(content=content, category="general")
        elif store_name == "knowledge":
            self._knowledge.ingest(title="routed", content=content)
        else:
            self._long_term.store(content=content, category="general")
            store_name = "long_term"

        logger.debug("memory_routed", store=store_name)
        return store_name

    def search_all(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search across all memory stores.

        Args:
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            Combined search results from all stores.
        """
        results: list[dict[str, Any]] = []

        for item in self._episodic.search(query, limit=limit):
            results.append({"source": "episodic", **item})

        for item in self._semantic.get_related(query, limit=limit):
            results.append({"source": "semantic", **item})

        for item in self._long_term.retrieve(query, limit=limit):
            results.append({"source": "long_term", **item})

        for item in self._knowledge.search(query, limit=limit):
            results.append({"source": "knowledge", **item})

        return results[:limit]

    def _infer_type(self, content: str) -> str:
        """Infer memory type from content heuristics."""
        content_lower = content.lower()
        if any(kw in content_lower for kw in ("event", "happened", "occurred")):
            return "episodic"
        if any(kw in content_lower for kw in ("is a", "has", "means", "defined")):
            return "semantic"
        if any(kw in content_lower for kw in ("document", "article", "reference")):
            return "knowledge"
        return "long_term"
