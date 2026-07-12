"""Executive Intelligence layer — capability pipeline orchestration."""

from __future__ import annotations

from config.logging import get_logger
from executive.schemas import Decision, Goal

logger = get_logger(__name__)


class CapabilityOrchestrator:
    """Assembles and validates capability pipelines for execution."""

    def __init__(self) -> None:
        self._registered_capabilities: set[str] = set()

    def register_capability(self, capability_id: str) -> None:
        """Register an available capability."""
        self._registered_capabilities.add(capability_id)

    def assemble_pipeline(self, goal: Goal, decision: Decision) -> list[str]:
        """Assemble an ordered list of capability IDs for the pipeline."""
        if decision.selected is None:
            return []
        steps = decision.selected.steps
        pipeline: list[str] = []
        for step in steps:
            # Extract capability_id from step format "mode:capability_id"
            cap_id = step.split(":")[-1] if ":" in step else step
            if cap_id not in pipeline:
                pipeline.append(cap_id)
        logger.info(
            "pipeline_assembled",
            goal_id=goal.goal_id,
            pipeline_length=len(pipeline),
        )
        return pipeline

    def compose_single(self, capability_id: str) -> dict:
        """Compose execution descriptor for a single capability."""
        return {
            "type": "single",
            "capability_id": capability_id,
            "mode": "direct",
            "timeout_seconds": 30.0,
        }

    def compose_multi(self, capability_ids: list[str]) -> dict:
        """Compose execution descriptor for sequential multi-capability pipeline."""
        return {
            "type": "sequential",
            "capabilities": capability_ids,
            "mode": "chain",
            "timeout_seconds": 30.0 * len(capability_ids),
        }

    def compose_parallel(self, capability_ids: list[str]) -> dict:
        """Compose execution descriptor for parallel multi-capability pipeline."""
        return {
            "type": "parallel",
            "capabilities": capability_ids,
            "mode": "fan_out",
            "timeout_seconds": 30.0,
            "max_concurrency": min(len(capability_ids), 8),
        }

    def compose_conditional(self, conditions: list[tuple[str, str]]) -> dict:
        """Compose execution descriptor for conditional branching."""
        branches = [{"condition": cond, "action": action} for cond, action in conditions]
        return {
            "type": "conditional",
            "branches": branches,
            "mode": "branch",
            "timeout_seconds": 60.0,
        }

    def validate_pipeline(self, pipeline: list[str]) -> tuple[bool, list[str]]:
        """Validate that all capabilities in a pipeline are available."""
        errors: list[str] = []
        if not pipeline:
            errors.append("Pipeline is empty")
            return False, errors

        for cap_id in pipeline:
            if not cap_id:
                errors.append("Empty capability ID in pipeline")
            # If we have registered capabilities, validate against them
            if self._registered_capabilities and cap_id not in self._registered_capabilities:
                errors.append(f"Capability not registered: {cap_id}")

        valid = len(errors) == 0
        return valid, errors
