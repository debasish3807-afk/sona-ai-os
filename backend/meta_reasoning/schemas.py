"""Meta Reasoning & Self Reflection Engine — data models and schemas."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReasoningStage(str, Enum):
    """Stages of the meta-reasoning pipeline."""

    REFLECTION = "reflection"
    CRITIQUE = "critique"
    EVIDENCE = "evidence"
    COUNTERFACTUAL = "counterfactual"
    SIMULATION = "simulation"
    QUALITY = "quality"
    CONFIDENCE = "confidence"
    REFINEMENT = "refinement"
    DECISION = "decision"


class ReasoningVerdict(str, Enum):
    """Final verdicts from the meta-reasoning process."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REFINEMENT = "needs_refinement"
    BLOCKED = "blocked"
    HUMAN_REQUIRED = "human_required"


class EvidenceLabel(str, Enum):
    """Labels assigned to evidence claims."""

    VERIFIED = "verified"
    INFERRED = "inferred"
    ESTIMATED = "estimated"
    HYPOTHESIS = "hypothesis"


@dataclass
class ReasoningResult:
    """Complete result of a meta-reasoning pass."""

    verdict: ReasoningVerdict
    confidence: float
    risk: float
    quality_score: float
    critique: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    evidence_labels: dict[str, EvidenceLabel] = field(default_factory=dict)
    reasoning_trace: list[str] = field(default_factory=list)
    alternatives_considered: int = 0
    simulation_passed: bool = False
    iterations: int = 1
    max_iterations: int = 3
    explanation: str = ""
    metadata: dict = field(default_factory=dict)
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "result_id": self.result_id,
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "risk": self.risk,
            "quality_score": self.quality_score,
            "critique": self.critique,
            "improvements": self.improvements,
            "evidence_labels": {k: v.value for k, v in self.evidence_labels.items()},
            "reasoning_trace": self.reasoning_trace,
            "alternatives_considered": self.alternatives_considered,
            "simulation_passed": self.simulation_passed,
            "iterations": self.iterations,
            "max_iterations": self.max_iterations,
            "explanation": self.explanation,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class SimulationResult:
    """Result of a plan simulation."""

    success: bool
    estimated_latency_ms: float
    estimated_cost: float
    estimated_tokens: int
    failure_probability: float
    resource_usage: dict = field(default_factory=dict)
    expected_outcome: str = ""
    warnings: list[str] = field(default_factory=list)
    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Serialize simulation result to dictionary."""
        return {
            "simulation_id": self.simulation_id,
            "success": self.success,
            "estimated_latency_ms": self.estimated_latency_ms,
            "estimated_cost": self.estimated_cost,
            "estimated_tokens": self.estimated_tokens,
            "failure_probability": self.failure_probability,
            "resource_usage": self.resource_usage,
            "expected_outcome": self.expected_outcome,
            "warnings": self.warnings,
        }


@dataclass
class QualityReport:
    """Quality assessment of a plan."""

    correctness: float
    completeness: float
    safety: float
    performance: float
    efficiency: float
    cost_efficiency: float
    confidence: float
    explainability: float
    overall: float
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize quality report to dictionary."""
        return {
            "correctness": self.correctness,
            "completeness": self.completeness,
            "safety": self.safety,
            "performance": self.performance,
            "efficiency": self.efficiency,
            "cost_efficiency": self.cost_efficiency,
            "confidence": self.confidence,
            "explainability": self.explainability,
            "overall": self.overall,
            "details": self.details,
        }
