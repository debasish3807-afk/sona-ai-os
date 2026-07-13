"""Knowledge memory store types: Semantic, LongTerm, Knowledge."""

from __future__ import annotations

import time
import uuid
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class SemanticMemory:
    """Fact-based semantic memory for knowledge representation."""

    def __init__(self) -> None:
        self._facts: list[dict[str, Any]] = []

    def store_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 0.8,
    ) -> None:
        """Store a semantic fact (subject-predicate-object triple)."""
        self._facts.append(
            {
                "fact_id": str(uuid.uuid4()),
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "confidence": confidence,
                "created_at": time.time(),
            }
        )

    def query(
        self,
        subject: str | None = None,
        predicate: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query facts by subject and/or predicate."""
        results = []
        for fact in self._facts:
            if subject and fact["subject"].lower() != subject.lower():
                continue
            if predicate and fact["predicate"].lower() != predicate.lower():
                continue
            results.append(fact)
        return results

    def get_related(self, concept: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get facts related to a concept."""
        concept_lower = concept.lower()
        results = [
            f
            for f in self._facts
            if concept_lower in f["subject"].lower() or concept_lower in f["object"].lower()
        ]
        results.sort(key=lambda f: f["confidence"], reverse=True)
        return results[:limit]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {"facts": self._facts, "count": len(self._facts)}


class LongTermMemory:
    """Persistent long-term memory with categorization and consolidation."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def store(
        self,
        content: str,
        category: str,
        importance: float = 0.5,
        tags: list[str] | None = None,
    ) -> None:
        """Store a long-term memory entry."""
        self._entries.append(
            {
                "entry_id": str(uuid.uuid4()),
                "content": content,
                "category": category,
                "importance": importance,
                "tags": tags or [],
                "created_at": time.time(),
                "access_count": 0,
            }
        )

    def retrieve(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve entries matching query."""
        query_lower = query.lower()
        results = [
            e
            for e in self._entries
            if query_lower in e["content"].lower()
            or query_lower in e["category"].lower()
            or any(query_lower in t.lower() for t in e["tags"])
        ]
        results.sort(key=lambda e: e["importance"], reverse=True)
        return results[:limit]

    def consolidate(self) -> int:
        """Consolidate low-importance old entries. Returns count removed."""
        now = time.time()
        before = len(self._entries)
        self._entries = [
            e
            for e in self._entries
            if not (
                (now - e["created_at"]) > 86400 and e["importance"] < 0.3 and e["access_count"] == 0
            )
        ]
        removed = before - len(self._entries)
        logger.info("long_term_consolidated", removed=removed)
        return removed

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {"entries": self._entries, "count": len(self._entries)}


class KnowledgeMemory:
    """Document-based knowledge memory for RAG and reference."""

    def __init__(self) -> None:
        self._documents: dict[str, dict[str, Any]] = {}

    def ingest(
        self,
        title: str,
        content: str,
        source: str = "",
        tags: list[str] | None = None,
    ) -> str:
        """Ingest a document. Returns doc_id."""
        doc_id = str(uuid.uuid4())
        self._documents[doc_id] = {
            "doc_id": doc_id,
            "title": title,
            "content": content,
            "source": source,
            "tags": tags or [],
            "ingested_at": time.time(),
        }
        logger.debug("knowledge_ingested", doc_id=doc_id, title=title)
        return doc_id

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search documents by text matching."""
        query_lower = query.lower()
        results = [
            doc
            for doc in self._documents.values()
            if query_lower in doc["title"].lower()
            or query_lower in doc["content"].lower()
            or any(query_lower in t.lower() for t in doc["tags"])
        ]
        return results[:limit]

    def get(self, doc_id: str) -> dict[str, Any] | None:
        """Get a document by ID."""
        return self._documents.get(doc_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {"documents": self._documents, "count": len(self._documents)}
