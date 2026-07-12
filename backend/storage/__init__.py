"""Persistent storage layer — repository pattern over async databases.

Provides an abstract storage interface with SQLite (dev) and
PostgreSQL/Redis (production) backends.
"""

from storage.repository import DocumentRecord, MemoryRecord, StorageRepository
from storage.sqlite_backend import SQLiteBackend

__all__ = [
    "DocumentRecord",
    "MemoryRecord",
    "SQLiteBackend",
    "StorageRepository",
]
