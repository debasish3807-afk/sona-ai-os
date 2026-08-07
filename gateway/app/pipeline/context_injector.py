"""Injects memory context into the request before inference.

Retrieves relevant memories from Memory OS and prepends them as
system context to improve response quality with personalization.
"""

import structlog

from sona_memory.domain.models import MemoryQuery, MemoryType
from sona_memory.infrastructure.memory_manager import MemoryManager

logger = structlog.get_logger()


class ContextInjector:
    """Retrieves and injects relevant context from memory.

    Combines conversation history, working memory, and semantic
    memories to provide rich context for LLM inference.
    """

    def __init__(self, max_context_entries: int = 5) -> None:
        """Initialize the context injector.

        Args:
            max_context_entries: Maximum number of memory entries to inject.
        """
        self._max_context_entries = max_context_entries

    async def inject(
        self,
        messages: list[dict[str, str]],
        user_id: str,
        session_id: str,
        memory: MemoryManager,
    ) -> list[dict[str, str]]:
        """Retrieve working + conversation + user memory and prepend as system context.

        Queries Memory OS for relevant context based on the latest user message
        and prepends it as a system message if found.

        Args:
            messages: The current conversation messages.
            user_id: The user ID for memory retrieval.
            session_id: The session ID for conversation context.
            memory: The Memory Manager instance.

        Returns:
            Messages list with memory context injected as system prefix.
        """
        # Extract the latest user message for query
        user_content = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_content = msg.get("content", "")
                break

        if not user_content:
            return messages

        context_parts: list[str] = []

        # Retrieve conversation history
        try:
            history = await memory.get_conversation_history(session_id, limit=10)
            if history:
                history_text = " | ".join(entry.content for entry in history[:5])
                context_parts.append(f"[Conversation context]: {history_text}")
        except Exception as e:
            logger.warning(
                "context_injection_history_failed",
                session_id=session_id,
                error=str(e),
            )

        # Retrieve relevant memories
        try:
            query = MemoryQuery(
                user_id=user_id,
                query=user_content,
                memory_types=[MemoryType.LONG_TERM, MemoryType.SEMANTIC],
                top_k=self._max_context_entries,
                min_importance=0.3,
            )
            memories = await memory.retrieve(query)
            if memories:
                memory_text = " | ".join(entry.content for entry in memories)
                context_parts.append(f"[User memories]: {memory_text}")
        except Exception as e:
            logger.warning(
                "context_injection_retrieval_failed",
                user_id=user_id,
                error=str(e),
            )

        # If no context found, return original messages
        if not context_parts:
            return messages

        # Build the context system message
        context_message = {
            "role": "system",
            "content": "Relevant context from memory:\n" + "\n".join(context_parts),
        }

        # Inject before existing messages (after any existing system message)
        result: list[dict[str, str]] = []
        system_injected = False

        for msg in messages:
            if msg.get("role") == "system" and not system_injected:
                result.append(msg)
                result.append(context_message)
                system_injected = True
            else:
                result.append(msg)

        # If no system message existed, prepend the context
        if not system_injected:
            result = [context_message, *result]

        logger.info(
            "context_injected",
            user_id=user_id,
            session_id=session_id,
            context_entries=len(context_parts),
        )

        return result
