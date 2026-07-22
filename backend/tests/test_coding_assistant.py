"""Tests for the AI Coding Assistant — analyzer, reviewer, generator."""

from pathlib import Path

from coding_assistant.analyzer import CodeAnalyzer
from coding_assistant.generator import CodeGenerator
from coding_assistant.reviewer import CodeReviewer

SIMPLE_MODULE = '''
import os
from pathlib import Path

def greet(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

class Calculator:
    """A simple calculator."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
'''

SEARCHABLE_CODE = '''
def calculate_total(items: list) -> float:
    """Calculate the total."""
    return sum(items)

def calculate_average(items: list) -> float:
    """Calculate the average."""
    return sum(items) / len(items) if items else 0.0
'''

CLEAN_CODE = '''
"""A simple module."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''

BAD_CODE = """
try:
    do_something()
except:
    pass
"""

DANGEROUS_CODE = """
result = eval(user_input)
"""

SOURCE_FOR_TESTS = '''
def add(a, b):
    """Add two numbers."""
    return a + b

class Calculator:
    """A calculator."""
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b
'''

SOURCE_FOR_DOCS = '''
class User:
    """Represents a user in the system."""
    pass

def login(username, password):
    """Authenticate a user."""
    pass
'''


class TestCodeAnalyzer:
    """Test the code analysis and indexing capabilities."""

    def test_index_basic(self, tmp_path: Path) -> None:
        """Test indexing a basic Python file."""
        src = tmp_path / "test_module.py"
        src.write_text(SIMPLE_MODULE)
        analyzer = CodeAnalyzer()
        result = analyzer.index_file(str(src))
        assert result.files >= 0
        assert len(result.symbols) > 0, "Should find symbols"
        names = {s.name for s in result.symbols}
        assert any(
            "os" in names or "Path" in names or s.name == "greet" or s.name == "Calculator"
            for s in result.symbols
        )

    def test_index_syntax_error(self, tmp_path: Path) -> None:
        """Test indexing a file with syntax errors."""
        src = tmp_path / "broken.py"
        src.write_text("def broken(\n")
        analyzer = CodeAnalyzer()
        result = analyzer.index_file(str(src))
        assert len(result.errors) > 0, "Should report syntax errors"

    def test_search_symbols(self, tmp_path: Path) -> None:
        """Test searching indexed symbols."""
        src = tmp_path / "searchable.py"
        src.write_text(SEARCHABLE_CODE)
        analyzer = CodeAnalyzer()
        analyzer.index_file(str(src))
        results = analyzer.search_symbol("calculate")
        assert len(results) >= 2, "Should find both calculate functions"

    def test_get_stats(self, tmp_path: Path) -> None:
        """Test stats reporting."""
        src = tmp_path / "stats_test.py"
        src.write_text("x = 1\n")
        analyzer = CodeAnalyzer()
        analyzer.index_file(str(src))
        stats = analyzer.get_stats()
        assert isinstance(stats, dict)


class TestCodeReviewer:
    """Test the automated code reviewer."""

    def test_clean_code(self) -> None:
        """Test that clean code gets a high score."""
        result = CodeReviewer().review(CLEAN_CODE, "clean.py")
        assert result.passed
        assert result.score >= 8.0

    def test_bare_except(self) -> None:
        """Test detection of bare except."""
        result = CodeReviewer().review(BAD_CODE, "bare_except.py")
        assert any("bare except" in i.message.lower() for i in result.issues)

    def test_dangerous_patterns(self) -> None:
        """Test detection of dangerous patterns."""
        result = CodeReviewer().review(DANGEROUS_CODE, "dangerous.py")
        assert any("eval" in i.message.lower() for i in result.issues)

    def test_empty_code(self) -> None:
        """Test reviewing empty code."""
        result = CodeReviewer().review("", "empty.py")
        assert result.score == 10.0
        assert result.passed


class TestCodeGenerator:
    """Test code generation capabilities."""

    def test_generate_tests(self) -> None:
        """Test generating tests from source."""
        result = CodeGenerator().generate_tests(SOURCE_FOR_TESTS)
        assert result.success
        assert result.test_count >= 2
        assert "test_" in result.content

    def test_generate_tests_syntax_error(self) -> None:
        """Test generating tests from broken code."""
        result = CodeGenerator().generate_tests("def broken(", "python")
        assert not result.success

    def test_generate_documentation(self) -> None:
        """Test generating documentation."""
        result = CodeGenerator().generate_documentation(SOURCE_FOR_DOCS)
        assert result.success
        assert "##" in result.content

    def test_refactor_code(self) -> None:
        """Test code refactoring."""
        source = 'name = "%s, %s" % (last, first)\n'
        result = CodeGenerator().refactor_code(source)
        assert result.success
