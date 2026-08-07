"""Evaluation OS domain layer.

Contains domain models, enums, and value objects for the Evaluation OS service.
"""

from domain.models import (
    EvaluationRequest,
    EvaluationType,
    MetricResult,
    MetricStatus,
    QualityReport,
)

__all__ = [
    "EvaluationRequest",
    "EvaluationType",
    "MetricResult",
    "MetricStatus",
    "QualityReport",
]
