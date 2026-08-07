"""Unit tests for AI Engineering OS domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest
from domain.models import (
    CodeLanguage,
    CodeRequest,
    CodeResult,
    ReviewFinding,
    ReviewResult,
    ReviewSeverity,
)


class TestCodeLanguage:
    """Tests for the CodeLanguage enum."""

    def test_all_languages_defined(self) -> None:
        """Verify all expected programming languages are available."""
        assert CodeLanguage.PYTHON == "python"
        assert CodeLanguage.TYPESCRIPT == "typescript"
        assert CodeLanguage.KOTLIN == "kotlin"
        assert CodeLanguage.JAVASCRIPT == "javascript"
        assert CodeLanguage.RUST == "rust"
        assert CodeLanguage.GO == "go"

    def test_language_count(self) -> None:
        """Verify exactly 6 languages exist."""
        assert len(CodeLanguage) == 6

    def test_language_is_str_enum(self) -> None:
        """Verify languages are usable as strings."""
        assert str(CodeLanguage.PYTHON) == "python"
        assert str(CodeLanguage.TYPESCRIPT) == "typescript"


class TestReviewSeverity:
    """Tests for the ReviewSeverity enum."""

    def test_all_severities_defined(self) -> None:
        """Verify all expected severity levels are available."""
        assert ReviewSeverity.CRITICAL == "critical"
        assert ReviewSeverity.WARNING == "warning"
        assert ReviewSeverity.SUGGESTION == "suggestion"
        assert ReviewSeverity.INFO == "info"

    def test_severity_count(self) -> None:
        """Verify exactly 4 severity levels exist."""
        assert len(ReviewSeverity) == 4

    def test_severity_is_str_enum(self) -> None:
        """Verify severities are usable as strings."""
        assert str(ReviewSeverity.CRITICAL) == "critical"
        assert str(ReviewSeverity.INFO) == "info"


class TestCodeRequest:
    """Tests for the CodeRequest frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        req = CodeRequest(
            instruction="Write a hello world function",
            language=CodeLanguage.PYTHON,
        )
        assert req.instruction == "Write a hello world function"
        assert req.language == CodeLanguage.PYTHON

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        req = CodeRequest(
            instruction="Generate a class",
            language=CodeLanguage.TYPESCRIPT,
        )
        assert req.context is None
        assert req.existing_code is None
        assert req.max_tokens == 4096

    def test_custom_values(self) -> None:
        """Create with all optional fields."""
        req = CodeRequest(
            instruction="Refactor this function",
            language=CodeLanguage.RUST,
            context="This is a web server project",
            existing_code="fn main() {}",
            max_tokens=8192,
        )
        assert req.context == "This is a web server project"
        assert req.existing_code == "fn main() {}"
        assert req.max_tokens == 8192

    def test_is_frozen(self) -> None:
        """Verify CodeRequest is immutable."""
        req = CodeRequest(
            instruction="test",
            language=CodeLanguage.PYTHON,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            req.instruction = "changed"  # type: ignore[misc]


class TestCodeResult:
    """Tests for the CodeResult frozen dataclass."""

    def test_creation(self) -> None:
        """Create a code result with all fields."""
        result = CodeResult(
            code="def hello():\n    print('Hello, world!')",
            language=CodeLanguage.PYTHON,
            explanation="A simple hello world function",
            tokens_used=25,
            confidence=0.95,
        )
        assert result.code == "def hello():\n    print('Hello, world!')"
        assert result.language == CodeLanguage.PYTHON
        assert result.explanation == "A simple hello world function"
        assert result.tokens_used == 25
        assert result.confidence == 0.95

    def test_is_frozen(self) -> None:
        """Verify CodeResult is immutable."""
        result = CodeResult(
            code="x = 1",
            language=CodeLanguage.PYTHON,
            explanation="Assignment",
            tokens_used=5,
            confidence=0.99,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            result.code = "y = 2"  # type: ignore[misc]


class TestReviewFinding:
    """Tests for the ReviewFinding frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create finding without suggestion."""
        finding = ReviewFinding(
            line=42,
            severity=ReviewSeverity.WARNING,
            message="Unused variable 'x'",
        )
        assert finding.line == 42
        assert finding.severity == ReviewSeverity.WARNING
        assert finding.message == "Unused variable 'x'"
        assert finding.suggestion is None

    def test_with_suggestion(self) -> None:
        """Create finding with a suggestion."""
        finding = ReviewFinding(
            line=10,
            severity=ReviewSeverity.CRITICAL,
            message="SQL injection vulnerability",
            suggestion="Use parameterized queries instead of string concatenation",
        )
        assert finding.suggestion == "Use parameterized queries instead of string concatenation"

    def test_is_frozen(self) -> None:
        """Verify ReviewFinding is immutable."""
        finding = ReviewFinding(
            line=1,
            severity=ReviewSeverity.INFO,
            message="test",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            finding.message = "changed"  # type: ignore[misc]


class TestReviewResult:
    """Tests for the ReviewResult frozen dataclass."""

    def test_creation_with_findings(self) -> None:
        """Create review result with multiple findings."""
        findings = [
            ReviewFinding(line=5, severity=ReviewSeverity.WARNING, message="Issue 1"),
            ReviewFinding(line=15, severity=ReviewSeverity.SUGGESTION, message="Issue 2"),
        ]
        result = ReviewResult(
            findings=findings,
            overall_quality=0.75,
            summary="Code has minor issues but is generally well-written.",
        )
        assert len(result.findings) == 2
        assert result.overall_quality == 0.75
        assert "minor issues" in result.summary

    def test_creation_with_no_findings(self) -> None:
        """Create review result with no findings (clean code)."""
        result = ReviewResult(
            findings=[],
            overall_quality=1.0,
            summary="No issues found. Code is clean and well-structured.",
        )
        assert len(result.findings) == 0
        assert result.overall_quality == 1.0

    def test_is_frozen(self) -> None:
        """Verify ReviewResult is immutable."""
        result = ReviewResult(
            findings=[],
            overall_quality=0.9,
            summary="Good code",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            result.summary = "changed"  # type: ignore[misc]
