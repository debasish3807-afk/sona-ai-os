"""Conversation Recall — cross-session conversation retrieval."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from memory.persistent_store import PersistentMemoryStore
from memory.ranker import MemoryRanker

logger = get_logger(__name__)


class ConversationRecall:
    """Retrieves conversation history across sessions using memory store."""

    def __init__(self, store: PersistentMemoryStore | None = None) -> None:
        self._store = store
        self._ranker = MemoryRanker()

    async def recall_recent(self, session_id: str, limit: int = 20) -> list[Any]:
        if not self._store:
            return []
        return await self._store.list_memories(
            memory_type="conversation", user_id=session_id, limit=limit
        )

    async def recall_context(
        self, session_id: str, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        if not self._store:
            return []
        entries = await self._store.list_memories(
            memory_type="conversation", user_id=session_id, limit=100
        )
        ranked = self._ranker.rank(entries, query=query, top_k=limit)
        return [
            {
                "content": getattr(e, "content", ""),
                "score": s,
                "entry_id": getattr(e, "entry_id", ""),
                "created_at": getattr(e, "created_at", 0.0),
            }
            for e, s in ranked
        ]

    async def recall_keywords(self, keywords: list[str], limit: int = 10) -> list[Any]:
        if not self._store or not keywords:
            return []
        results: list[Any] = []
        for kw in keywords:
            res = await self._store.search(kw, top_k=limit)
            for r in res:
                if hasattr(r, "entry"):
                    results.append(r.entry)
                else:
                    results.append(r)
        seen = set()
        unique = []
        for r in results:
            eid = getattr(r, "entry_id", str(id(r)))
            if eid not in seen:
                seen.add(eid)
                unique.append(r)
        return unique[:limit]
