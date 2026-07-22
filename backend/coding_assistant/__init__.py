"""AI Coding Assistant — code analysis, generation, review, and indexing."""

from coding_assistant.analyzer import CodeAnalyzer
from coding_assistant.generator import CodeGenerator
from coding_assistant.reviewer import CodeReviewer, Issue, IssueSeverity, ReviewResult
from coding_assistant.service import CodingAssistantService

__all__ = [
    "CodeAnalyzer",
    "CodeGenerator",
    "CodeReviewer",
    "CodingAssistantService",
    "Issue",
    "IssueSeverity",
    "ReviewResult",
]
