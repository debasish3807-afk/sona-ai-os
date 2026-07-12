"""Result verification system.

Validates and verifies the outputs produced by agents to ensure
quality, correctness, and safety before returning to the user.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from agents.context import ExecutionResult


class VerificationStatus(str, Enum):
    """Outcome of a verification check."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class VerificationType(str, Enum):
    """Types of verification checks."""

    SAFETY = "safety"
    QUALITY = "quality"
    CORRECTNESS = "correctness"
    FORMAT = "format"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"


@dataclass
class VerificationCheck:
    """A single verification check result.

    Attributes:
        check_id: Unique check identifier.
        check_type: The type of verification.
        status: Check outcome.
        message: Human-readable result message.
        score: Confidence score (0-1).
        details: Additional check details.
    """

    check_type: VerificationType
    status: VerificationStatus
    check_id: str = field(default_factory=lambda: str(uuid4()))
    message: str = ""
    score: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationReport:
    """Complete verification report for a result.

    Attributes:
        report_id: Unique report identifier.
        result_id: The result that was verified.
        checks: Individual check results.
        overall_status: Aggregate status.
        overall_score: Aggregate quality score.
        recommendations: Suggested improvements.
        metadata: Additional report metadata.
    """

    result_id: str
    checks: List[VerificationCheck]
    report_id: str = field(default_factory=lambda: str(uuid4()))
    overall_status: VerificationStatus = VerificationStatus.PASSED
    overall_score: float = 1.0
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Check if all verifications passed."""
        return self.overall_status == VerificationStatus.PASSED

    @property
    def failed_checks(self) -> List[VerificationCheck]:
        """Get only the failed checks."""
        return [
            c for c in self.checks
            if c.status == VerificationStatus.FAILED
        ]


class ResultVerifier(ABC):
    """Abstract interface for result verification.

    Applies a series of checks to agent outputs to ensure
    they meet quality, safety, and correctness standards.
    """

    @abstractmethod
    async def verify(
        self,
        result: ExecutionResult,
        checks: Optional[List[VerificationType]] = None,
    ) -> VerificationReport:
        """Verify an execution result.

        Applies configured checks and produces a report.

        Args:
            result: The result to verify.
            checks: Optional specific checks to run.

        Returns:
            VerificationReport with outcomes.
        """
        ...

    @abstractmethod
    async def verify_safety(
        self, result: ExecutionResult
    ) -> VerificationCheck:
        """Verify the safety of a result.

        Args:
            result: The result to check.

        Returns:
            Safety check result.
        """
        ...

    @abstractmethod
    async def verify_quality(
        self, result: ExecutionResult
    ) -> VerificationCheck:
        """Verify the quality of a result.

        Args:
            result: The result to check.

        Returns:
            Quality check result.
        """
        ...

    @abstractmethod
    async def register_check(
        self,
        check_type: VerificationType,
        checker: "ResultVerifier",
    ) -> None:
        """Register a custom verification checker.

        Args:
            check_type: The verification type.
            checker: The verification implementation.
        """
        ...

    @abstractmethod
    async def should_reject(
        self, report: VerificationReport
    ) -> bool:
        """Determine if a result should be rejected.

        Args:
            report: The verification report.

        Returns:
            True if the result should be rejected.
        """
        ...
