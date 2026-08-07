"""Unit tests for AI Engineering OS abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest
from sona_ai_engineering.application.ports import CodeGenerationPort, CodeReviewPort, DebuggingPort
from sona_ai_engineering.domain.models import (
    CodeLanguage,
    CodeRequest,
    CodeResult,
    ReviewFinding,
    ReviewResult,
    ReviewSeverity,
)


class TestCodeGenerationPort:
    """Tests for the CodeGenerationPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify CodeGenerationPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CodeGenerationPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = CodeGenerationPort.__abstractmethods__
        assert "generate" in abstract_methods
        assert "complete" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteGenerator(CodeGenerationPort):
            async def generate(self, request: CodeRequest) -> CodeResult:
                return CodeResult(
                    code="print('hello')",
                    language=request.language,
                    explanation="Generated code",
                    tokens_used=10,
                    confidence=0.9,
                )

            async def complete(self, code_prefix: str, language: CodeLanguage) -> str:
                return code_prefix + "\n    pass"

        generator = ConcreteGenerator()
        assert isinstance(generator, CodeGenerationPort)

    @pytest.mark.asyncio
    async def test_generate_returns_code_result(self) -> None:
        """Test that a concrete generate() returns the right type."""

        class MockGenerator(CodeGenerationPort):
            async def generate(self, request: CodeRequest) -> CodeResult:
                return CodeResult(
                    code=f"# {request.instruction}",
                    language=request.language,
                    explanation="Mock generated",
                    tokens_used=5,
                    confidence=0.85,
                )

            async def complete(self, code_prefix: str, language: CodeLanguage) -> str:
                return code_prefix + "\n# completed"

        generator = MockGenerator()
        req = CodeRequest(
            instruction="Write a sort function",
            language=CodeLanguage.PYTHON,
        )
        result = await generator.generate(req)
        assert isinstance(result, CodeResult)
        assert result.language == CodeLanguage.PYTHON
        assert result.confidence == 0.85

    @pytest.mark.asyncio
    async def test_complete_returns_string(self) -> None:
        """Test that a concrete complete() returns a string."""

        class MockGenerator(CodeGenerationPort):
            async def generate(self, request: CodeRequest) -> CodeResult:
                return CodeResult(
                    code="",
                    language=request.language,
                    explanation="",
                    tokens_used=0,
                    confidence=0.0,
                )

            async def complete(self, code_prefix: str, language: CodeLanguage) -> str:
                return code_prefix + "\n    return result"

        generator = MockGenerator()
        result = await generator.complete("def my_func():", CodeLanguage.PYTHON)
        assert isinstance(result, str)
        assert "return result" in result


class TestCodeReviewPort:
    """Tests for the CodeReviewPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify CodeReviewPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CodeReviewPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = CodeReviewPort.__abstractmethods__
        assert "review" in abstract_methods
        assert "suggest_fixes" in abstract_methods

    @pytest.mark.asyncio
    async def test_review_returns_review_result(self) -> None:
        """Test that a concrete review() returns the right type."""

        class MockReviewer(CodeReviewPort):
            async def review(self, code: str, language: CodeLanguage) -> ReviewResult:
                return ReviewResult(
                    findings=[
                        ReviewFinding(
                            line=1,
                            severity=ReviewSeverity.SUGGESTION,
                            message="Consider adding a docstring",
                        )
                    ],
                    overall_quality=0.8,
                    summary="Code is decent with minor improvements possible.",
                )

            async def suggest_fixes(self, code: str, finding: ReviewFinding) -> str:
                return f'"""Docstring."""\n{code}'

        reviewer = MockReviewer()
        result = await reviewer.review("def foo(): pass", CodeLanguage.PYTHON)
        assert isinstance(result, ReviewResult)
        assert len(result.findings) == 1
        assert result.overall_quality == 0.8

    @pytest.mark.asyncio
    async def test_suggest_fixes_returns_string(self) -> None:
        """Test that suggest_fixes() returns a fixed code string."""

        class MockReviewer(CodeReviewPort):
            async def review(self, code: str, language: CodeLanguage) -> ReviewResult:
                return ReviewResult(findings=[], overall_quality=1.0, summary="Clean")

            async def suggest_fixes(self, code: str, finding: ReviewFinding) -> str:
                return code.replace("x = x + 1", "x += 1")

        reviewer = MockReviewer()
        finding = ReviewFinding(
            line=3,
            severity=ReviewSeverity.SUGGESTION,
            message="Use augmented assignment",
        )
        fixed = await reviewer.suggest_fixes("x = x + 1", finding)
        assert "x += 1" in fixed


class TestDebuggingPort:
    """Tests for the DebuggingPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify DebuggingPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DebuggingPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = DebuggingPort.__abstractmethods__
        assert "analyze_error" in abstract_methods
        assert "suggest_fix" in abstract_methods

    @pytest.mark.asyncio
    async def test_analyze_error_returns_explanation(self) -> None:
        """Test that analyze_error() returns an explanation string."""

        class MockDebugger(DebuggingPort):
            async def analyze_error(self, error: str, code: str, language: CodeLanguage) -> str:
                return f"The error '{error}' is caused by a type mismatch."

            async def suggest_fix(
                self, error: str, code: str, language: CodeLanguage
            ) -> CodeResult:
                return CodeResult(
                    code=code,
                    language=language,
                    explanation="Fixed the type mismatch",
                    tokens_used=15,
                    confidence=0.88,
                )

        debugger = MockDebugger()
        explanation = await debugger.analyze_error(
            error="TypeError: unsupported operand type",
            code="result = '5' + 3",
            language=CodeLanguage.PYTHON,
        )
        assert isinstance(explanation, str)
        assert "type mismatch" in explanation

    @pytest.mark.asyncio
    async def test_suggest_fix_returns_code_result(self) -> None:
        """Test that suggest_fix() returns a CodeResult."""

        class MockDebugger(DebuggingPort):
            async def analyze_error(self, error: str, code: str, language: CodeLanguage) -> str:
                return "Analysis"

            async def suggest_fix(
                self, error: str, code: str, language: CodeLanguage
            ) -> CodeResult:
                return CodeResult(
                    code="result = int('5') + 3",
                    language=language,
                    explanation="Convert string to int before addition",
                    tokens_used=12,
                    confidence=0.92,
                )

        debugger = MockDebugger()
        result = await debugger.suggest_fix(
            error="TypeError",
            code="result = '5' + 3",
            language=CodeLanguage.PYTHON,
        )
        assert isinstance(result, CodeResult)
        assert result.language == CodeLanguage.PYTHON
        assert result.confidence == 0.92
