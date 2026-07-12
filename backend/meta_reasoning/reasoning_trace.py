"""Meta Reasoning & Self Reflection Engine — reasoning trace recorder."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceEntry:
    """A single entry in the reasoning trace."""

    stage: str
    category: str
    content: str
    confidence: float = 1.0
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


class ReasoningTrace:
    """Records the trace of a meta-reasoning session."""

    def __init__(self) -> None:
        self._entries: list[TraceEntry] = []

    def add(self, stage: str, category: str, content: str, confidence: float = 1.0) -> None:
        """Add a trace entry.

        Args:
            stage: The reasoning stage producing this entry.
            category: One of observation, assumption, evidence, alternative,
                      simulation, critique, improvement, decision.
            content: Human-readable description of the trace step.
            confidence: Confidence level for this entry (0-1).
        """
        entry = TraceEntry(
            stage=stage,
            category=category,
            content=content,
            confidence=confidence,
        )
        self._entries.append(entry)

    def get_by_stage(self, stage: str) -> list[TraceEntry]:
        """Return all entries for a given stage."""
        return [e for e in self._entries if e.stage == stage]

    def get_by_category(self, category: str) -> list[TraceEntry]:
        """Return all entries for a given category."""
        return [e for e in self._entries if e.category == category]

    def get_all(self) -> list[TraceEntry]:
        """Return all trace entries."""
        return list(self._entries)

    def get_summary(self) -> list[str]:
        """Return formatted summary strings for each entry."""
        return [
            f"[{e.stage}:{e.category}] {e.content} (confidence={e.confidence:.2f})"
            for e in self._entries
        ]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the trace to a dictionary."""
        return {
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "stage": e.stage,
                    "category": e.category,
                    "content": e.content,
                    "confidence": e.confidence,
                    "timestamp": e.timestamp,
                }
                for e in self._entries
            ],
            "total": len(self._entries),
        }

    def clear(self) -> None:
        """Clear all trace entries."""
        self._entries.clear()
