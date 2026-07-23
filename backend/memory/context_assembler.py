"""Context Builder — assembles memory context for AI prompts."""

from __future__ import annotations

import json
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class ContextAssembler:
    """Assembles structured AI context from multiple memory sources."""

    def __init__(self, max_tokens: int = 4096) -> None:
        self._max_tokens = max_tokens

    def build(
        self,
        recent_conversations: list[dict[str, Any]] | None = None,
        semantic_memories: list[dict[str, Any]] | None = None,
        episodic_memories: list[dict[str, Any]] | None = None,
        knowledge_entries: list[dict[str, Any]] | None = None,
        user_preferences: dict[str, Any] | None = None,
    ) -> str:
        sections: list[str] = []
        sections.append("## Context\n")
        if user_preferences:
            sections.append(f"### User Preferences\n{json.dumps(user_preferences, indent=2)}\n")

        if semantic_memories:
            sections.append("### Semantic Memory (Facts)\n")
            for m in semantic_memories[:10]:
                sections.append(f"- {m.get('content', '')[:300]}")
            sections.append("")

        if episodic_memories:
            sections.append("### Episodic Memory (Events)\n")
            for m in episodic_memories[:10]:
                sections.append(f"- {m.get('content', '')[:300]}")
            sections.append("")

        if knowledge_entries:
            sections.append("### Knowledge Base\n")
            for m in knowledge_entries[:10]:
                sections.append(f"- [{m.get('domain', 'general')}] {m.get('content', '')[:300]}")
            sections.append("")

        if recent_conversations:
            sections.append("### Recent Conversation\n")
            for m in recent_conversations[-10:]:
                role = m.get("role", m.get("session_id", "user"))
                sections.append(f"**{role}**: {m.get('content', '')[:500]}")
            sections.append("")

        return "\n".join(sections)

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
