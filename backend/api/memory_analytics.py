"""Memory Analytics Dashboard API — statistics and insights."""

from __future__ import annotations

from fastapi import APIRouter

from config.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/memory/analytics", tags=["memory-analytics"])

_analytics: dict[str, int] = {}


@router.get("/overview")
async def analytics_overview():
    store = _get_store()
    stats = await store.get_stats()
    total = stats.total_entries if hasattr(stats, "total_entries") else 0
    return {
        "total_entries": total,
        "entries_by_type": stats.by_type if hasattr(stats, "by_type") else {},
        "pinned": stats.pinned_count if hasattr(stats, "pinned_count") else 0,
        "expired": stats.expired_count if hasattr(stats, "expired_count") else 0,
    }


@router.get("/types")
async def analytics_by_type():
    store = _get_store()
    stats = await store.get_stats()
    return {"types": stats.by_type if hasattr(stats, "by_type") else {}}


@router.get("/recent")
async def analytics_recent(days: int = 7):
    import time

    cutoff = time.time() - (days * 86400)
    store = _get_store()
    entries = await store.list(limit=1000)
    recent = [e for e in entries if getattr(e, "created_at", 0) >= cutoff]
    return {"total": len(entries), "recent": len(recent), "days": days}


_MEMORY_STORE = None


def _get_store():
    global _MEMORY_STORE
    if _MEMORY_STORE is None:
        import os

        from memory.persistent_store import PersistentMemoryStore

        _MEMORY_STORE = PersistentMemoryStore(
            db_path=os.environ.get("MEMORY_DB_PATH", "sona_memory.db")
        )
        import asyncio

        asyncio.get_event_loop().run_until_complete(_MEMORY_STORE.initialize())
    return _MEMORY_STORE
