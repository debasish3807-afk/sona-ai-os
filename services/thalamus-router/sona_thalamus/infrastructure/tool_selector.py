"""Tool selection logic for THALAMUS routing.

Determines which tools (if any) are needed to fulfill a request
based on intent classification and content analysis.
"""

import re

import structlog

from sona_thalamus.domain.models import IntentCategory

logger = structlog.get_logger(__name__)

# Intent to default tools mapping
_INTENT_TOOLS: dict[IntentCategory, list[str]] = {
    IntentCategory.CODE: ["code_execution", "file_system"],
    IntentCategory.RESEARCH: ["web_search", "knowledge_base"],
    IntentCategory.AUTOMATION: ["workflow_engine", "scheduler"],
    IntentCategory.MEMORY: ["memory_store"],
    IntentCategory.SYSTEM: ["system_admin"],
    IntentCategory.CHAT: [],
}

# Content patterns that indicate specific tool needs
_TOOL_PATTERNS: dict[str, list[str]] = {
    "web_search": [
        r"\bsearch\s+the\s+web\b",
        r"\blook\s+up\s+online\b",
        r"\bfind\s+on\s+the\s+internet\b",
        r"\bgoogle\b",
    ],
    "code_execution": [
        r"\brun\s+(this|the)\s+code\b",
        r"\bexecute\b",
        r"\beval\b",
        r"\bcompile\s+and\s+run\b",
    ],
    "file_system": [
        r"\bread\s+(the\s+)?file\b",
        r"\bwrite\s+to\s+(a\s+)?file\b",
        r"\bcreate\s+(a\s+)?file\b",
        r"\bsave\s+(to|as)\b",
    ],
    "calculator": [
        r"\bcalculate\b",
        r"\bcompute\b",
        r"\bmath\b",
        r"\bsolve\b",
        r"\d+\s*[\+\-\*/]\s*\d+",
    ],
    "image_generation": [
        r"\bgenerate\s+(an?\s+)?image\b",
        r"\bdraw\b",
        r"\billustrate\b",
        r"\bcreate\s+(a\s+)?picture\b",
    ],
}


class ToolSelector:
    """Selects tools needed to fulfill a request.

    Combines intent-based defaults with content pattern matching
    to determine the optimal set of tools for execution.
    """

    def __init__(self) -> None:
        """Initialize the tool selector with pre-compiled patterns."""
        self._compiled_patterns: dict[str, list[re.Pattern[str]]] = {
            tool: [re.compile(p, re.IGNORECASE) for p in patterns]
            for tool, patterns in _TOOL_PATTERNS.items()
        }

    def select(self, content: str, intent: IntentCategory) -> list[str]:
        """Select tools needed for the given request.

        Args:
            content: The user input text.
            intent: The classified intent category.

        Returns:
            List of tool names that should be available for execution.
        """
        tools: set[str] = set()

        # Add intent-based default tools
        intent_tools = _INTENT_TOOLS.get(intent, [])
        tools.update(intent_tools)

        # Add content-pattern-detected tools
        for tool_name, patterns in self._compiled_patterns.items():
            if any(p.search(content) for p in patterns):
                tools.add(tool_name)

        result = sorted(tools)

        logger.debug(
            "tools_selected",
            intent=str(intent),
            tool_count=len(result),
            tools=result,
        )

        return result
