"""Domain models for the AI Engineering OS service.

Defines the data structures used by the AI Engineering OS for code generation,
code review, and debugging operations.
"""

from dataclasses import dataclass
from enum import StrEnum


class CodeLanguage(StrEnum):
    """Supported programming languages for code operations.

    Determines the language context for code generation, review,
    and debugging operations.
    """

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    KOTLIN = "kotlin"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"


class ReviewSeverity(StrEnum):
    """Severity levels for code review findings.

    Classifies the importance of issues detected during code review.
    """

    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    INFO = "info"


@dataclass(frozen=True)
class CodeRequest:
    """Request for code generation or modification.

    Attributes:
        instruction: Natural language description of what code to generate.
        language: Target programming language for the generated code.
        context: Optional additional context about the project or requirements.
        existing_code: Optional existing code to modify or build upon.
        max_tokens: Maximum number of tokens for the generated code output.
    """

    instruction: str
    language: CodeLanguage
    context: str | None = None
    existing_code: str | None = None
    max_tokens: int = 4096


@dataclass(frozen=True)
class CodeResult:
    """Result of a code generation operation.

    Attributes:
        code: The generated source code.
        language: The programming language of the generated code.
        explanation: Natural language explanation of what was generated.
        tokens_used: Number of tokens consumed during generation.
        confidence: Model confidence score for the generated code (0.0 to 1.0).
    """

    code: str
    language: CodeLanguage
    explanation: str
    tokens_used: int
    confidence: float


@dataclass(frozen=True)
class ReviewFinding:
    """A single finding from a code review operation.

    Attributes:
        line: The line number where the issue was found.
        severity: The severity level of the finding.
        message: Description of the issue found.
        suggestion: Optional suggested fix for the issue.
    """

    line: int
    severity: ReviewSeverity
    message: str
    suggestion: str | None = None


@dataclass(frozen=True)
class ReviewResult:
    """Aggregated result of a code review operation.

    Attributes:
        findings: List of individual review findings.
        overall_quality: Overall code quality score (0.0 to 1.0).
        summary: Natural language summary of the review.
    """

    findings: list[ReviewFinding]
    overall_quality: float
    summary: str
