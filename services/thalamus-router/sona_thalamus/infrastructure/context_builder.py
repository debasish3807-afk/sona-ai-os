"""Execution context builder.

Builds rich execution context from the incoming request, extracting
session references, determining memory needs, estimating token budgets,
and identifying user preferences.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

from sona_thalamus.domain.models import IntentCategory

logger = structlog.get_logger(__name__)

# Default token budget for different intent categories
_TOKEN_BUDGETS: dict[IntentCategory, int] = {
    IntentCategory.CHAT: 2048,
    IntentCategory.CODE: 4096,
    IntentCategory.RESEARCH: 4096,
    IntentCategory.AUTOMATION: 2048,
    IntentCategory.MEMORY: 1024,
    IntentCategory.SYSTEM: 512,
}


@dataclass(frozen=True)
class ExecutionContext:
    """Context assembled for execution planning.

    Attributes:
        session_id: Reference to the current session.
        user_id: Reference to the requesting user.
        needs_memory_retrieval: Whether memory retrieval is needed.
        needs_knowledge_query: Whether knowledge base query is needed.
        token_budget: Estimated token budget for the response.
        user_preferences: Extracted user preferences.
        history_depth: Number of historical messages to include.
        metadata: Additional context metadata.
    """

    session_id: str = ""
    user_id: str = ""
    needs_memory_retrieval: bool = False
    needs_knowledge_query: bool = False
    token_budget: int = 2048
    user_preferences: dict[str, Any] = field(default_factory=dict)
    history_depth: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ContextBuilder:
    """Builds execution context from request data and intent.

    Analyzes the request payload to extract session information,
    determine what additional data retrieval is needed, and set
    appropriate resource limits.
    """

    def __init__(self, default_history_depth: int = 5) -> None:
        """Initialize the context builder.

        Args:
            default_history_depth: Default number of history messages to include.
        """
        self._default_history_depth = default_history_depth

    def build(self, request: dict[str, Any], intent: IntentCategory) -> ExecutionContext:
        """Build execution context from request and classified intent.

        Args:
            request: The incoming request payload.
            intent: The classified intent category.

        Returns:
            Assembled ExecutionContext.
        """
        session_id = str(request.get("session_id", ""))
        user_id = str(request.get("user_id", ""))
        content = str(request.get("content", ""))
        context_data = request.get("context", {})

        # Determine memory retrieval needs
        needs_memory = self._needs_memory_retrieval(content, intent, context_data)

        # Determine knowledge query needs
        needs_knowledge = self._needs_knowledge_query(content, intent)

        # Estimate token budget
        token_budget = self._estimate_token_budget(content, intent)

        # Extract user preferences
        preferences = self._extract_preferences(context_data)

        # Determine history depth
        history_depth = self._determine_history_depth(intent, context_data)

        # Build metadata
        metadata: dict[str, Any] = {}
        if context_data.get("system_prompt"):
            metadata["has_system_prompt"] = True
        if context_data.get("tools"):
            metadata["available_tools"] = context_data["tools"]

        ctx = ExecutionContext(
            session_id=session_id,
            user_id=user_id,
            needs_memory_retrieval=needs_memory,
            needs_knowledge_query=needs_knowledge,
            token_budget=token_budget,
            user_preferences=preferences,
            history_depth=history_depth,
            metadata=metadata,
        )

        logger.debug(
            "context_built",
            session_id=session_id,
            needs_memory=needs_memory,
            needs_knowledge=needs_knowledge,
            token_budget=token_budget,
        )

        return ctx

    def _needs_memory_retrieval(
        self,
        content: str,
        intent: IntentCategory,
        context_data: dict[str, Any],
    ) -> bool:
        """Determine if memory retrieval is needed."""
        if intent == IntentCategory.MEMORY:
            return True

        # Check for references to past interactions
        memory_signals = ["remember", "recall", "last time", "previously", "earlier", "before"]
        content_lower = content.lower()
        if any(signal in content_lower for signal in memory_signals):
            return True

        # Check if context explicitly requests memory
        if context_data.get("include_memory", False):
            return True

        return False

    def _needs_knowledge_query(self, content: str, intent: IntentCategory) -> bool:
        """Determine if knowledge base query is needed."""
        if intent == IntentCategory.RESEARCH:
            return True

        # Check for explicit knowledge-seeking patterns
        knowledge_signals = ["what is", "how does", "explain", "tell me about", "definition"]
        content_lower = content.lower()
        return any(signal in content_lower for signal in knowledge_signals)

    def _estimate_token_budget(self, content: str, intent: IntentCategory) -> int:
        """Estimate appropriate token budget for the response."""
        base_budget = _TOKEN_BUDGETS.get(intent, 2048)

        # Longer inputs may need longer outputs
        word_count = len(content.split())
        if word_count > 100:
            base_budget = int(base_budget * 1.5)
        elif word_count > 50:
            base_budget = int(base_budget * 1.25)

        return base_budget

    def _extract_preferences(self, context_data: dict[str, Any]) -> dict[str, Any]:
        """Extract user preferences from context data."""
        preferences: dict[str, Any] = {}

        if "language" in context_data:
            preferences["language"] = context_data["language"]
        if "response_format" in context_data:
            preferences["response_format"] = context_data["response_format"]
        if "temperature" in context_data:
            preferences["temperature"] = context_data["temperature"]
        if "max_tokens" in context_data:
            preferences["max_tokens"] = context_data["max_tokens"]

        return preferences

    def _determine_history_depth(
        self,
        intent: IntentCategory,
        context_data: dict[str, Any],
    ) -> int:
        """Determine how many historical messages to include."""
        # Explicit override
        if "history_depth" in context_data:
            return int(context_data["history_depth"])

        # Memory intent needs more history
        if intent == IntentCategory.MEMORY:
            return self._default_history_depth * 2

        # System intent needs minimal history
        if intent == IntentCategory.SYSTEM:
            return 0

        return self._default_history_depth
