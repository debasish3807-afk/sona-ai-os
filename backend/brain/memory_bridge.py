"""Memory bridge — connects the Brain to the Memory Engine.

Handles:
    - Retrieving conversation history for context injection
    - Saving assistant responses to memory
    - Building context windows with token budgets
"""

from __future__ import annotations

from datetime import UTC, datetime

from brain.schemas import ChatMessageSchema
from config.logging import get_logger
from memory.types import MemoryEntry, MemoryScope, MemoryType

logger = get_logger(__name__)

# In-memory conversation store (production would use a persistent backend)
_conversation_store: dict[str, list[MemoryEntry]] = {}


def retrieve_conversation_history(
    session_id: str | None,
    max_messages: int = 20,
) -> list[ChatMessageSchema]:
    """Retrieve recent conversation history for context injection.

    Args:
        session_id: The session to retrieve history for.
        max_messages: Maximum number of messages to return.

    Returns:
        List of messages from conversation history.
    """
    if not session_id:
        return []

    entries = _conversation_store.get(session_id, [])
    if not entries:
        return []

    # Return most recent messages up to limit
    recent = entries[-max_messages:]
    messages: list[ChatMessageSchema] = []
    for entry in recent:
        role = entry.metadata.get("role", "user")
        messages.append(ChatMessageSchema(role=role, content=entry.content))

    logger.debug(
        "Retrieved conversation history",
        session_id=session_id,
        message_count=len(messages),
    )
    return messages


def save_message_to_memory(
    session_id: str,
    role: str,
    content: str,
    model: str | None = None,
    token_count: int | None = None,
) -> None:
    """Save a message to conversation memory.

    Args:
        session_id: Session identifier.
        role: Message role (user/assistant/system).
        content: Message content.
        model: Model that generated the response (for assistant messages).
        token_count: Estimated token count.
    """
    if not session_id:
        return

    if session_id not in _conversation_store:
        _conversation_store[session_id] = []

    entry = MemoryEntry(
        memory_type=MemoryType.CONVERSATION,
        scope=MemoryScope.SESSION,
        content=content,
        session_id=session_id,
        token_count=token_count,
        metadata={
            "role": role,
            "model": model or "",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
    _conversation_store[session_id].append(entry)

    logger.debug(
        "Saved message to memory",
        session_id=session_id,
        role=role,
        content_length=len(content),
    )


def build_context_messages(
    request_messages: list[ChatMessageSchema],
    history: list[ChatMessageSchema],
    system_prompt: str | None = None,
    max_context_tokens: int = 8192,
) -> list[ChatMessageSchema]:
    """Build the full context window for the LLM request.

    Combines system prompt, conversation history, and new messages
    while respecting token budget.

    Args:
        request_messages: The new messages from the current request.
        history: Previous conversation history.
        system_prompt: Optional system prompt override.
        max_context_tokens: Token budget for context window.

    Returns:
        Combined message list ready for the provider.
    """
    result: list[ChatMessageSchema] = []

    # System prompt first
    if system_prompt:
        result.append(ChatMessageSchema(role="system", content=system_prompt))
    elif not any(m.role == "system" for m in request_messages):
        result.append(
            ChatMessageSchema(
                role="system",
                content=(
                    "You are Sona, an intelligent AI assistant. "
                    "You are helpful, precise, and knowledgeable. "
                    "Respond clearly and concisely."
                ),
            )
        )

    # Inject conversation history (respecting token budget)
    estimated_tokens = sum(len(m.content) // 4 for m in result)
    budget = max_context_tokens - 1024  # Reserve tokens for response

    for msg in history:
        msg_tokens = len(msg.content) // 4
        if estimated_tokens + msg_tokens > budget:
            break
        result.append(msg)
        estimated_tokens += msg_tokens

    # Add current request messages (skip system if already added)
    for msg in request_messages:
        if msg.role == "system" and system_prompt:
            continue
        result.append(msg)

    return result


def get_session_stats(session_id: str) -> dict[str, int]:
    """Get memory statistics for a session."""
    entries = _conversation_store.get(session_id, [])
    return {
        "total_messages": len(entries),
        "user_messages": sum(1 for e in entries if e.metadata.get("role") == "user"),
        "assistant_messages": sum(1 for e in entries if e.metadata.get("role") == "assistant"),
    }
