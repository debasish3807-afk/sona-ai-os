"""Abstract port interfaces for the AI Engineering OS service.

Defines the contracts that infrastructure adapters must implement
to provide code generation, code review, and debugging capabilities.
"""

from abc import ABC, abstractmethod

from domain.models import CodeLanguage, CodeRequest, CodeResult, ReviewFinding, ReviewResult


class CodeGenerationPort(ABC):
    """Port for code generation operations.

    Defines the contract for generating code from natural language
    instructions and completing partial code snippets.
    """

    @abstractmethod
    async def generate(self, request: CodeRequest) -> CodeResult:
        """Generate code from a natural language instruction.

        Args:
            request: The code generation request containing instruction,
                language, and optional context.

        Returns:
            A CodeResult with the generated code, explanation, and metrics.
        """
        ...

    @abstractmethod
    async def complete(self, code_prefix: str, language: CodeLanguage) -> str:
        """Complete a partial code snippet.

        Args:
            code_prefix: The existing code to complete from.
            language: The programming language of the code.

        Returns:
            The completed code string (continuation of the prefix).
        """
        ...


class CodeReviewPort(ABC):
    """Port for code review operations.

    Defines the contract for analyzing code quality, detecting issues,
    and suggesting improvements.
    """

    @abstractmethod
    async def review(self, code: str, language: CodeLanguage) -> ReviewResult:
        """Review code for quality issues, bugs, and improvements.

        Args:
            code: The source code to review.
            language: The programming language of the code.

        Returns:
            A ReviewResult containing findings, quality score, and summary.
        """
        ...

    @abstractmethod
    async def suggest_fixes(self, code: str, finding: ReviewFinding) -> str:
        """Suggest a fix for a specific code review finding.

        Args:
            code: The original source code containing the issue.
            finding: The specific review finding to fix.

        Returns:
            The suggested fixed code as a string.
        """
        ...


class DebuggingPort(ABC):
    """Port for debugging operations.

    Defines the contract for analyzing errors and suggesting
    code fixes based on error messages and stack traces.
    """

    @abstractmethod
    async def analyze_error(self, error: str, code: str, language: CodeLanguage) -> str:
        """Analyze an error message in the context of source code.

        Args:
            error: The error message or stack trace to analyze.
            code: The source code that produced the error.
            language: The programming language of the code.

        Returns:
            A natural language explanation of the error and its cause.
        """
        ...

    @abstractmethod
    async def suggest_fix(self, error: str, code: str, language: CodeLanguage) -> CodeResult:
        """Suggest a code fix for an error.

        Args:
            error: The error message or stack trace.
            code: The source code that produced the error.
            language: The programming language of the code.

        Returns:
            A CodeResult with the suggested fix and explanation.
        """
        ...
