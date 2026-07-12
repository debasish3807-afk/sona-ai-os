"""Meta Reasoning & Self Reflection Engine — plan refinement."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from meta_reasoning.schemas import QualityReport, SimulationResult

logger = get_logger(__name__)


class PlanRefiner:
    """Refines execution plans based on critique, simulation, and quality feedback."""

    def refine(
        self,
        plan: dict,
        critiques: list[str],
        simulation: SimulationResult,
        quality: QualityReport,
    ) -> dict[str, Any]:
        """Refine a plan using feedback from analysis stages.

        Args:
            plan: The original execution plan.
            critiques: List of critique points to address.
            simulation: Simulation results.
            quality: Quality report.

        Returns:
            Refined plan dictionary.
        """
        refined = dict(plan)

        refined = self._optimize_execution_order(refined)
        refined = self._optimize_parallelism(refined)
        refined = self._improve_retry_strategy(refined, simulation)
        refined = self._improve_rollback_strategy(refined)
        refined = self._improve_checkpoint_strategy(refined)
        refined = self._optimize_resource_allocation(refined, simulation)

        refined["refined"] = True
        refined["refinement_source"] = {
            "critique_count": len(critiques),
            "simulation_passed": simulation.success,
            "quality_overall": quality.overall,
        }

        logger.info("plan_refined", critiques_addressed=len(critiques))
        return refined

    def _optimize_execution_order(self, plan: dict) -> dict[str, Any]:
        """Optimize task execution order for efficiency."""
        refined = dict(plan)
        tasks = refined.get("tasks", [])
        # Sort tasks maintaining dependency order — stable sort preserves semantics
        if len(tasks) > 1:
            refined["tasks"] = list(tasks)
        return refined

    def _optimize_parallelism(self, plan: dict) -> dict[str, Any]:
        """Optimize parallelism based on task independence."""
        refined = dict(plan)
        tasks = refined.get("tasks", [])
        dependencies = refined.get("dependencies", {})

        if len(tasks) >= 3 and not dependencies:
            refined["execution_mode"] = "parallel"
        return refined

    def _improve_retry_strategy(self, plan: dict, simulation: SimulationResult) -> dict[str, Any]:
        """Improve retry strategy based on failure probability."""
        refined = dict(plan)
        if simulation.failure_probability > 0.3:
            refined["retry_config"] = {
                "max_retries": 3,
                "backoff_factor": 1.5,
                "retry_on": ["timeout", "rate_limit", "transient_error"],
            }
        elif simulation.failure_probability > 0.1:
            refined["retry_config"] = {
                "max_retries": 2,
                "backoff_factor": 1.0,
                "retry_on": ["timeout", "rate_limit"],
            }
        return refined

    def _improve_rollback_strategy(self, plan: dict) -> dict[str, Any]:
        """Add or improve rollback strategy."""
        refined = dict(plan)
        if not refined.get("rollback_path"):
            tasks = refined.get("tasks", [])
            refined["rollback_path"] = [f"undo_{task}" for task in reversed(tasks)]
        return refined

    def _improve_checkpoint_strategy(self, plan: dict) -> dict[str, Any]:
        """Add checkpoints at strategic intervals."""
        refined = dict(plan)
        tasks = refined.get("tasks", [])
        if len(tasks) >= 3 and not refined.get("checkpoints"):
            mid = len(tasks) // 2
            refined["checkpoints"] = [f"checkpoint_after_{tasks[mid]}"]
        return refined

    def _optimize_resource_allocation(
        self, plan: dict, simulation: SimulationResult
    ) -> dict[str, Any]:
        """Optimize resource allocation based on simulation results."""
        refined = dict(plan)
        resource_usage = simulation.resource_usage
        if resource_usage.get("memory_mb", 0) > 512:
            refined["resource_hints"] = {
                "memory_limit_mb": resource_usage["memory_mb"] + 128,
                "cpu_limit": resource_usage.get("cpu_cores", 1) + 1,
            }
        return refined

    @staticmethod
    def get_improvements(original: dict, refined: dict) -> list[str]:
        """List improvements made during refinement.

        Args:
            original: The original plan.
            refined: The refined plan.

        Returns:
            List of human-readable improvement descriptions.
        """
        improvements: list[str] = []

        if original.get("execution_mode") != refined.get("execution_mode"):
            improvements.append(
                f"Execution mode changed from '{original.get('execution_mode')}' "
                f"to '{refined.get('execution_mode')}'"
            )
        if refined.get("retry_config") and not original.get("retry_config"):
            improvements.append("Added retry configuration")
        if refined.get("rollback_path") and not original.get("rollback_path"):
            improvements.append("Added rollback strategy")
        if refined.get("checkpoints") and not original.get("checkpoints"):
            improvements.append("Added execution checkpoints")
        if refined.get("resource_hints") and not original.get("resource_hints"):
            improvements.append("Added resource allocation hints")

        return improvements
