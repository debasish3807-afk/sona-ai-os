"""Code Reviewer — automated code review with AI-powered analysis."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import Enum


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STYLE = "style"


@dataclass
class Issue:
    """A code review issue."""

    line: int
    column: int
    message: str
    severity: IssueSeverity
    rule: str = ""
    suggestion: str = ""
    end_line: int = 0


@dataclass
class ReviewResult:
    """Results from a code review."""

    file_path: str
    issues: list[Issue] = field(default_factory=list)
    summary: str = ""
    score: float = 0.0  # 0.0 to 10.0
    passed: bool = True


class CodeReviewer:
    """Analyzes code for bugs, style issues, and improvements."""

    DANGEROUS_PATTERNS = {
        "eval": ("Avoid eval() -- can execute arbitrary code", IssueSeverity.ERROR),
        "exec": ("Avoid exec() -- can execute arbitrary code", IssueSeverity.ERROR),
        "pickle.loads": (
            "Unsafe deserialization -- prefer JSON or safe formats",
            IssueSeverity.ERROR,
        ),
        "pickle.load": (
            "Unsafe deserialization -- prefer JSON or safe formats",
            IssueSeverity.ERROR,
        ),
        "shell=True": (
            "Shell injection risk -- avoid shell=True in subprocess",
            IssueSeverity.ERROR,
        ),
        "os.system": ("Use subprocess.run() instead of os.system()", IssueSeverity.WARNING),
    }

    def __init__(self) -> None:
        self._issues: list[Issue] = []

    def review(self, source: str, file_path: str = "unknown") -> ReviewResult:
        """Perform a comprehensive code review."""
        self._issues = []
        lines = source.split("\n")

        self._check_pattern_matches(lines)
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            self._issues.append(
                Issue(
                    line=0,
                    column=0,
                    message="File contains syntax errors",
                    severity=IssueSeverity.ERROR,
                    rule="S100",
                )
            )
            return self._build_result(file_path)

        self._check_ast_issues(tree)
        self._check_complexity(lines)
        self._check_documentation(lines)
        self._check_naming(lines)

        return self._build_result(file_path)

    def _build_result(self, file_path: str) -> ReviewResult:
        """Build the result object."""
        score = self._calculate_score()
        return ReviewResult(
            file_path=file_path,
            issues=self._issues,
            score=score,
            passed=len([i for i in self._issues if i.severity == IssueSeverity.ERROR]) == 0,
        )

    def _check_pattern_matches(self, lines: list[str]) -> None:
        """Check for dangerous patterns via text search."""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"'):
                continue
            for pattern, (message, severity) in self.DANGEROUS_PATTERNS.items():
                if pattern in stripped:
                    self._issues.append(
                        Issue(
                            line=i,
                            column=stripped.index(pattern) + 1,
                            message=message,
                            severity=severity,
                            rule="S001",
                            suggestion=f"Replace '{pattern}' with a safer alternative",
                        )
                    )

    def _check_ast_issues(self, tree: ast.AST) -> None:
        """Check for AST-level issues."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                self._issues.append(
                    Issue(
                        line=node.lineno,
                        column=node.col_offset,
                        message="Bare except clause -- catches all exceptions",
                        severity=IssueSeverity.ERROR,
                        rule="S002",
                        suggestion="Use 'except SpecificException:' instead",
                    )
                )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = (node.end_lineno or node.lineno) - node.lineno
                if func_lines > 60:
                    self._issues.append(
                        Issue(
                            line=node.lineno,
                            column=node.col_offset,
                            message=f"Function '{node.name}' is {func_lines} lines long. Consider splitting.",
                            severity=IssueSeverity.WARNING,
                            rule="S003",
                            suggestion=f"Break '{node.name}' into smaller functions",
                            end_line=node.end_lineno or node.lineno,
                        )
                    )

    def _check_complexity(self, lines: list[str]) -> None:
        """Check for overly complex code patterns."""
        max_depth = 0
        for line in lines:
            stripped = line.rstrip()
            if any(kw in stripped for kw in ["if ", "for ", "while ", "except ", "with ", "try:"]):
                depth = (len(line) - len(line.lstrip())) // 4
                max_depth = max(max_depth, depth)
        if max_depth > 5:
            self._issues.append(
                Issue(
                    line=1,
                    column=0,
                    message=f"Deep nesting detected (depth {max_depth}). Consider refactoring.",
                    severity=IssueSeverity.WARNING,
                    rule="S004",
                    suggestion="Extract nested blocks into separate functions",
                )
            )

    def _check_documentation(self, lines: list[str]) -> None:
        """Check documentation quality."""
        total = len(lines)
        if total < 10:
            return
        comment_lines = sum(1 for _line in lines if _line.strip().startswith("#"))
        docstring_lines = 0
        inside_docstring = False
        for line_text in lines:
            if '"""' in line_text or "'''" in line_text:
                inside_docstring = not inside_docstring
            if inside_docstring:
                docstring_lines += 1
        if total > 50 and comment_lines / total < 0.02:
            self._issues.append(
                Issue(
                    line=1,
                    column=0,
                    message=f"Low comment density ({comment_lines}/{total}). Add more documentation.",
                    severity=IssueSeverity.INFO,
                    rule="S005",
                    suggestion="Add docstrings to functions and classes",
                )
            )

    def _check_naming(self, lines: list[str]) -> None:
        """Check for naming convention violations."""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"'):
                continue
            match = re.match(r"def\s+([a-zA-Z_]\w*)\s*\(", stripped)
            if match:
                name = match.group(1)
                if name[0].isupper():
                    self._issues.append(
                        Issue(
                            line=i,
                            column=stripped.index(name) + 1,
                            message=f"Function '{name}' should use snake_case",
                            severity=IssueSeverity.STYLE,
                            rule="S006",
                            suggestion=f"Rename '{name}' to snake_case",
                        )
                    )
            match = re.match(r"class\s+([a-zA-Z_]\w*)\s*[:\(]", stripped)
            if match:
                name = match.group(1)
                if name[0].islower() and not name.startswith("_"):
                    self._issues.append(
                        Issue(
                            line=i,
                            column=stripped.index(name) + 1,
                            message=f"Class '{name}' should use PascalCase",
                            severity=IssueSeverity.STYLE,
                            rule="S007",
                            suggestion=f"Rename '{name}' to PascalCase",
                        )
                    )

    def _calculate_score(self) -> float:
        """Calculate code quality score from 0 to 10."""
        if not self._issues:
            return 10.0
        penalties = {
            IssueSeverity.ERROR: 2.0,
            IssueSeverity.WARNING: 1.0,
            IssueSeverity.INFO: 0.5,
            IssueSeverity.STYLE: 0.3,
        }
        total_penalty = sum(penalties.get(i.severity, 0) for i in self._issues)
        return max(0.0, min(10.0, 10.0 - total_penalty))
