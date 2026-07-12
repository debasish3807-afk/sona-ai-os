"""Intent analysis — determines what the user wants to accomplish.

Classifies user messages into actionable intents and extracts
structured parameters for tool selection and planning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskIntent(str, Enum):
    """High-level intent categories for tool-based execution."""

    CHAT = "chat"  # No tools needed — pure conversation
    FILE_OPERATION = "file_operation"  # Read/write/edit files
    CODE_EXECUTION = "code_execution"  # Run code or scripts
    GIT_OPERATION = "git_operation"  # Git commands
    GITHUB_OPERATION = "github_operation"  # GitHub API interactions
    WEB_RESEARCH = "web_research"  # Browse/search the web
    DATABASE_OPERATION = "database_operation"  # Query databases
    PROJECT_ANALYSIS = "project_analysis"  # Analyze codebase
    MULTI_STEP = "multi_step"  # Complex multi-tool task


@dataclass
class IntentResult:
    """Result of intent analysis."""

    intent: TaskIntent
    confidence: float  # 0.0 to 1.0
    requires_tools: bool
    suggested_tools: list[str] = field(default_factory=list)
    extracted_params: dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


# Pattern sets for intent detection
_FILE_PATTERNS = [
    re.compile(
        r"\b(read|write|create|edit|delete|move|copy|rename)\b.*\b(file|directory|folder)\b", re.I
    ),
    re.compile(r"\b(show|display|cat|open|view)\b.*\b(file|content|code)\b", re.I),
    re.compile(r"\b(list|find|search)\b.*\b(files?|directories|folders?|\.py|\.ts|\.js)\b", re.I),
    re.compile(r"\b(save|write|append|update)\b.*\b(to|into)\b", re.I),
]

_CODE_PATTERNS = [
    re.compile(r"\b(run|execute|eval|test)\b.*\b(code|script|python|command)\b", re.I),
    re.compile(r"\b(install|pip|npm|cargo)\b", re.I),
    re.compile(r"\bpytest\b|\bruff\b|\bmypy\b", re.I),
]

_GIT_PATTERNS = [
    re.compile(r"\b(commit|push|pull|merge|rebase|checkout|branch)\b", re.I),
    re.compile(r"\bgit\s+(status|log|diff|add|stash|reset)\b", re.I),
    re.compile(r"\b(stage|unstage|amend)\b.*\b(changes?|files?)\b", re.I),
]

_GITHUB_PATTERNS = [
    re.compile(r"\b(pull\s+request|PR|issue|release)\b", re.I),
    re.compile(r"\bgithub\b", re.I),
    re.compile(r"\b(open|close|merge|review)\b.*\b(PR|issue|pull\s+request)\b", re.I),
]

_WEB_PATTERNS = [
    re.compile(r"\b(search|browse|fetch|download)\b.*\b(web|url|http|page|site)\b", re.I),
    re.compile(r"\bhttps?://", re.I),
    re.compile(r"\b(look\s+up|find\s+online|google|research)\b", re.I),
]

_DB_PATTERNS = [
    re.compile(r"\b(query|select|insert|update|delete)\b.*\b(database|table|db|sql)\b", re.I),
    re.compile(r"\bSELECT\b.*\bFROM\b", re.I),
    re.compile(r"\b(sqlite|postgres|schema)\b", re.I),
]

_PROJECT_PATTERNS = [
    re.compile(
        r"\b(analy[sz]e|inspect|review|audit|summarize)\b.*\b(project|repo|codebase|repository)\b",
        re.I,
    ),
    re.compile(r"\b(find\s+all|count|list\s+all)\b.*\b(TODO|FIXME|errors?|warnings?)\b", re.I),
    re.compile(r"\b(structure|architecture|dependencies)\b.*\b(project|code)\b", re.I),
]

_MULTI_STEP_MARKERS = [
    re.compile(r"\b(and\s+then|after\s+that|next|also|then)\b", re.I),
    re.compile(r"\b(first|second|finally|step)\b", re.I),
    re.compile(r"\bcommit.*push\b|\bfix.*test\b|\bfind.*replace\b", re.I),
]


def _score_patterns(text: str, patterns: list[re.Pattern[str]]) -> float:
    """Score text against pattern set. Returns 0.0-1.0 confidence."""
    matches = sum(1 for p in patterns if p.search(text))
    return min(1.0, matches / max(1, len(patterns) * 0.4))


class IntentAnalyzer:
    """Analyzes user messages to determine intent and required tools.

    Uses pattern matching and heuristics for fast, deterministic
    intent classification without requiring an LLM call.
    """

    def analyze(self, message: str) -> IntentResult:
        """Analyze a user message to determine intent.

        Args:
            message: The user's message text.

        Returns:
            IntentResult with classified intent and metadata.
        """
        scores: dict[TaskIntent, float] = {
            TaskIntent.FILE_OPERATION: _score_patterns(message, _FILE_PATTERNS),
            TaskIntent.CODE_EXECUTION: _score_patterns(message, _CODE_PATTERNS),
            TaskIntent.GIT_OPERATION: _score_patterns(message, _GIT_PATTERNS),
            TaskIntent.GITHUB_OPERATION: _score_patterns(message, _GITHUB_PATTERNS),
            TaskIntent.WEB_RESEARCH: _score_patterns(message, _WEB_PATTERNS),
            TaskIntent.DATABASE_OPERATION: _score_patterns(message, _DB_PATTERNS),
            TaskIntent.PROJECT_ANALYSIS: _score_patterns(message, _PROJECT_PATTERNS),
        }

        # Check for multi-step indicators
        multi_score = _score_patterns(message, _MULTI_STEP_MARKERS)
        active_intents = sum(1 for s in scores.values() if s > 0.3)

        if multi_score > 0.3 or active_intents >= 2:
            scores[TaskIntent.MULTI_STEP] = max(multi_score, 0.5)

        # Find the best intent
        best_intent = max(scores, key=lambda k: scores[k])
        best_score = scores[best_intent]

        # If no strong signal, default to CHAT
        if best_score < 0.25:
            return IntentResult(
                intent=TaskIntent.CHAT,
                confidence=1.0 - best_score,
                requires_tools=False,
                reasoning="No tool-related intent detected",
            )

        # Determine suggested tools based on intent
        tools = self._suggest_tools(best_intent, message)

        return IntentResult(
            intent=best_intent,
            confidence=best_score,
            requires_tools=True,
            suggested_tools=tools,
            extracted_params=self._extract_params(best_intent, message),
            reasoning=f"Detected {best_intent.value} intent with {best_score:.0%} confidence",
        )

    def _suggest_tools(self, intent: TaskIntent, message: str) -> list[str]:
        """Suggest specific tools based on intent."""
        tool_map: dict[TaskIntent, list[str]] = {
            TaskIntent.FILE_OPERATION: [
                "file_read",
                "file_write",
                "file_edit",
                "list_dir",
                "file_search",
            ],
            TaskIntent.CODE_EXECUTION: ["terminal_exec", "python_exec"],
            TaskIntent.GIT_OPERATION: [
                "git_status",
                "git_add",
                "git_commit",
                "git_diff",
                "git_log",
            ],
            TaskIntent.GITHUB_OPERATION: [
                "github_repo_info",
                "github_pull_requests",
                "github_issues",
            ],
            TaskIntent.WEB_RESEARCH: ["browser_fetch", "browser_search"],
            TaskIntent.DATABASE_OPERATION: ["db_query", "db_schema"],
            TaskIntent.PROJECT_ANALYSIS: ["list_dir", "file_read", "file_search", "terminal_exec"],
            TaskIntent.MULTI_STEP: ["file_read", "terminal_exec", "git_status"],
        }
        return tool_map.get(intent, [])

    def _extract_params(self, intent: TaskIntent, message: str) -> dict[str, Any]:
        """Extract structured parameters from the message."""
        params: dict[str, Any] = {}

        # Extract file paths
        path_match = re.search(r'["\']([^"\']+\.[a-zA-Z]+)["\']|(\S+\.[a-zA-Z]{1,5})', message)
        if path_match:
            params["path"] = path_match.group(1) or path_match.group(2)

        # Extract URLs
        url_match = re.search(r"https?://\S+", message)
        if url_match:
            params["url"] = url_match.group(0)

        # Extract branch names for git
        if intent == TaskIntent.GIT_OPERATION:
            branch_match = re.search(r"\b(feature|fix|release|hotfix)/[\w-]+\b", message)
            if branch_match:
                params["branch"] = branch_match.group(0)

        return params
