"""Meta Reasoning & Self Reflection API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from meta_reasoning.alternative_generator import AlternativeGenerator
from meta_reasoning.counterfactual_engine import CounterfactualEngine
from meta_reasoning.critique_engine import CritiqueEngine
from meta_reasoning.evidence_engine import EvidenceEngine
from meta_reasoning.exceptions import DeadlockError, MetaReasoningError
from meta_reasoning.hypothesis_engine import HypothesisEngine
from meta_reasoning.meta_reasoner import MetaReasoner
from meta_reasoning.plan_refiner import PlanRefiner
from meta_reasoning.plan_validator import PlanValidator
from meta_reasoning.quality_estimator import QualityEstimator
from meta_reasoning.reasoning_memory import ReasoningMemory
from meta_reasoning.reflection_engine import ReflectionEngine
from meta_reasoning.simulation_engine import SimulationEngine
from meta_reasoning.uncertainty_engine import UncertaintyEngine

router = APIRouter(prefix="/meta-reasoning", tags=["meta-reasoning"])

_reasoner: MetaReasoner | None = None


def get_reasoner() -> MetaReasoner:
    """Get or create the global MetaReasoner instance."""
    global _reasoner
    if _reasoner is None:
        _reasoner = MetaReasoner(
            reflection_engine=ReflectionEngine(),
            critique_engine=CritiqueEngine(),
            alternative_generator=AlternativeGenerator(),
            hypothesis_engine=HypothesisEngine(),
            counterfactual_engine=CounterfactualEngine(),
            simulation_engine=SimulationEngine(),
            plan_validator=PlanValidator(),
            plan_refiner=PlanRefiner(),
            evidence_engine=EvidenceEngine(),
            uncertainty_engine=UncertaintyEngine(),
            quality_estimator=QualityEstimator(),
            reasoning_memory=ReasoningMemory(),
        )
    return _reasoner


@router.post("/reason")
async def reason(body: dict[str, Any]) -> dict[str, Any]:
    """Run full meta-reasoning on a plan.

    Expects JSON body with keys: plan, goal, context.
    """
    reasoner = get_reasoner()
    plan = body.get("plan", {})
    goal = body.get("goal", {})
    context = body.get("context", {})

    if not plan:
        raise HTTPException(status_code=400, detail="Plan is required")

    try:
        result = await reasoner.reason(plan, goal, context)
        return {"success": True, "result": result.to_dict()}
    except DeadlockError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except MetaReasoningError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/status")
async def meta_reasoning_status() -> dict[str, Any]:
    """Get meta-reasoner status."""
    reasoner = get_reasoner()
    return {"success": True, "status": reasoner.get_status()}


@router.get("/trace/{plan_id}")
async def get_trace(plan_id: str) -> dict[str, Any]:
    """Get reasoning trace for a plan.

    Note: Returns the current trace state. In production this would
    be keyed by plan_id in persistent storage.
    """
    reasoner = get_reasoner()
    trace_data = reasoner._trace.to_dict()
    return {"success": True, "plan_id": plan_id, "trace": trace_data}


@router.get("/events")
async def recent_events(limit: int = 50) -> dict[str, Any]:
    """Get recent meta-reasoning events."""
    reasoner = get_reasoner()
    events = [e.to_dict() for e in reasoner._events[-limit:]]
    return {"success": True, "events": events, "total": len(events)}


@router.get("/memory/stats")
async def memory_stats() -> dict[str, Any]:
    """Get reasoning memory statistics."""
    reasoner = get_reasoner()
    stats = reasoner._reasoning_memory.stats()
    return {"success": True, "stats": stats}
