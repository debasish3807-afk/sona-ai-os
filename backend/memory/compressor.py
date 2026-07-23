"""Memory Compression — deduplication, merging, and consolidation."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class MemoryCompressor:
    """Compresses memory by deduplicating, merging, and archiving."""

    def __init__(self, similarity_threshold: float = 0.8) -> None:
        self._threshold = similarity_threshold

    def deduplicate(self, entries: list[Any]) -> list[Any]:
        seen_hashes: set[str] = set()
        unique: list[Any] = []
        for e in entries:
            content = getattr(e, "content", str(e))
            h = hashlib.sha256(content.encode()).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique.append(e)
        removed = len(entries) - len(unique)
        if removed:
            logger.info("dedup_removed", count=removed)
        return unique

    def merge_similar(self, entries: list[Any]) -> list[Any]:
        if len(entries) < 2:
            return entries
        merged: list[Any] = []
        used: set[int] = set()
        for i, a in enumerate(entries):
            if i in used:
                continue
            best = i
            best_sim = 1.0
            for j, b in enumerate(entries):
                if j <= i or j in used:
                    continue
                sim = self._content_similarity(getattr(a, "content", ""), getattr(b, "content", ""))
                if sim > best_sim:
                    best_sim = sim
                    best = j
            if best != i and best_sim >= self._threshold:
                content_a = getattr(entries[i], "content", "")
                content_b = getattr(entries[best], "content", "")
                merged_content = content_a + "\n" + content_b
                merged_entry = entries[i]
                if hasattr(merged_entry.__class__, "content"):
                    merged_entry.content = merged_content[:10000]
                merged.append(merged_entry)
                used.add(i)
                used.add(best)
            else:
                merged.append(entries[i])
                used.add(i)
        return merged

    @staticmethod
    def _content_similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())
        if not a_words or not b_words:
            return 0.0
        intersection = a_words & b_words
        union = a_words | b_words
        return len(intersection) / len(union)

    def archive(self, entries: list[Any], max_age_days: int = 90) -> list[Any]:
        now = time.time()
        cutoff = now - (max_age_days * 86400)
        active: list[Any] = []
        archived: list[Any] = []
        for e in entries:
            created = getattr(e, "created_at", getattr(e, "accessed_at", now))
            if isinstance(created, (int, float)) and created < cutoff:
                archived.append(e)
            else:
                active.append(e)
        if archived:
            logger.info("archive_moved", count=len(archived), days=max_age_days)
        return active
