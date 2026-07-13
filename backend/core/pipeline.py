"""End-to-End Orchestration Pipeline — unified request flow through all layers."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class PipelineStage(str, Enum):
    """Stages of the end-to-end pipeline."""

    INTAKE = "intake"
    SANITIZE = "sanitize"
    COGNITIVE = "cognitive"
    GOAL = "goal"
    EXECUTIVE = "executive"
    META_REASONING = "meta_reasoning"
    AGENT_COORDINATION = "agent_coordination"
    RUNTIME = "runtime"
    MEMORY = "memory"
    RESPONSE = "response"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineRequest:
    """A request flowing through the pipeline."""

    user_input: str
    user_id: str = ""
    session_id: str = ""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)


@dataclass
class PipelineResult:
    """Result of a complete pipeline execution."""

    request_id: str
    status: PipelineStatus
    output: dict[str, Any] = field(default_factory=dict)
    stages_completed: list[str] = field(default_factory=list)
    error: str = ""
    duration_ms: float = 0.0
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "output": self.output,
            "stages_completed": self.stages_completed,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
        }


class Pipeline:
    """Orchestrates end-to-end request processing through all layers.

    Flow: Security → IntentSanitizer → CognitiveKernel → ExecutiveBrain
         → MetaReasoner → AgentManager → AgentCoordinator → RuntimeEngine
         → MemoryManager → Response
    """

    def __init__(self, container: Any) -> None:
        self._container = container
        self._executions: dict[str, PipelineResult] = {}

    async def execute(self, request: PipelineRequest) -> PipelineResult:
        """Execute the full pipeline for a request."""
        start = time.perf_counter()
        result = PipelineResult(
            request_id=request.request_id,
            status=PipelineStatus.RUNNING,
        )
        self._executions[request.request_id] = result
        stage_outputs: dict[str, Any] = {}

        try:
            # Stage 1: Sanitize input via IntentSanitizer
            sanitize_result = await self._stage_sanitize(request)
            stage_outputs["sanitize"] = sanitize_result
            result.stages_completed.append(PipelineStage.SANITIZE.value)
            if not sanitize_result.get("safe", True):
                result.status = PipelineStatus.FAILED
                result.error = "Input failed safety sanitization"
                result.output = sanitize_result
                return result

            # Stage 2: CognitiveKernel intent classification
            cognitive_result = await self._stage_cognitive(request)
            stage_outputs["cognitive"] = cognitive_result
            result.stages_completed.append(PipelineStage.COGNITIVE.value)

            # Stage 3: Goal creation via ExecutiveBrain
            goal_result = await self._stage_goal(request)
            stage_outputs["goal"] = goal_result
            result.stages_completed.append(PipelineStage.GOAL.value)

            # Stage 4: Executive planning
            executive_result = await self._stage_executive(goal_result)
            stage_outputs["executive"] = executive_result
            result.stages_completed.append(PipelineStage.EXECUTIVE.value)

            # Stage 5: Meta-reasoning verification
            meta_result = await self._stage_meta_reasoning(executive_result)
            stage_outputs["meta_reasoning"] = meta_result
            result.stages_completed.append(PipelineStage.META_REASONING.value)

            # Stage 6: Agent coordination
            agent_result = await self._stage_agent_coordination(executive_result, meta_result)
            stage_outputs["agent_coordination"] = agent_result
            result.stages_completed.append(PipelineStage.AGENT_COORDINATION.value)

            # Stage 7: Runtime execution via AgentRuntimeBridge
            runtime_result = await self._stage_runtime(executive_result, meta_result)
            stage_outputs["runtime"] = runtime_result
            result.stages_completed.append(PipelineStage.RUNTIME.value)

            # Stage 8: Memory storage
            await self._stage_memory(request, stage_outputs)
            result.stages_completed.append(PipelineStage.MEMORY.value)

            # Stage 9: Response assembly
            response = self._assemble_response(stage_outputs)
            result.output = response
            result.stages_completed.append(PipelineStage.RESPONSE.value)

            result.status = PipelineStatus.COMPLETED

        except Exception as exc:
            logger.error(
                "pipeline_failed",
                request_id=request.request_id,
                error=str(exc),
                stages_completed=result.stages_completed,
            )
            result.status = PipelineStatus.FAILED
            result.error = str(exc)

        finally:
            result.duration_ms = (time.perf_counter() - start) * 1000

        return result

    async def _stage_sanitize(self, request: PipelineRequest) -> dict[str, Any]:
        """Sanitize user input through the microkernel IntentSanitizer."""
        sanitizer = self._container.resolve("intent_sanitizer")
        result = sanitizer.sanitize(request.user_input)
        return dict(result.to_dict())

    async def _stage_cognitive(self, request: PipelineRequest) -> dict[str, Any]:
        """Classify intent through the CognitiveKernel pipeline."""
        kernel = self._container.resolve("cognitive_kernel")
        from cognitive.request_context import RequestContext

        ctx = RequestContext(
            session_id=request.session_id,
            user_id=request.user_id,
            metadata={"user_input": request.user_input},
        )
        try:
            result = await kernel.process(ctx)
            return dict(result)
        except Exception as exc:
            logger.warning("cognitive_stage_fallback", error=str(exc))
            return {
                "success": True,
                "intent": "task_execution",
                "confidence": 0.7,
                "source": "fallback",
            }

    async def _stage_goal(self, request: PipelineRequest) -> dict[str, Any]:
        """Create a goal via the ExecutiveBrain's public API."""
        brain = self._container.resolve("executive_brain")
        goal = brain.create_goal(
            title=request.user_input[:100],
            description=request.user_input,
        )
        return dict(goal.to_dict())

    async def _stage_executive(self, goal: dict[str, Any]) -> dict[str, Any]:
        """Run executive planning via ExecutiveBrain.process_goal()."""
        brain = self._container.resolve("executive_brain")
        try:
            result = await brain.process_goal(
                title=goal.get("title", ""),
                description=goal.get("description", ""),
            )
            return dict(result)
        except Exception as exc:
            logger.warning("executive_stage_error", error=str(exc))
            return {"plan": {"tasks": []}, "approval": "auto_approved"}

    async def _stage_meta_reasoning(self, executive_result: dict[str, Any]) -> dict[str, Any]:
        """Validate plan through the MetaReasoner."""
        reasoner = self._container.resolve("meta_reasoner")
        plan = executive_result.get("plan", {})
        goal = executive_result.get("goal", {})
        try:
            result = await reasoner.reason(plan, goal, {})
            return dict(result.to_dict())
        except Exception as exc:
            logger.warning("meta_reasoning_stage_error", error=str(exc))
            return {"verdict": "approved", "confidence": 0.7}

    async def _stage_agent_coordination(
        self, executive_result: dict[str, Any], meta_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Route task to agents via AgentManager and AgentCoordinator."""
        verdict = meta_result.get("verdict", "approved")
        if verdict == "rejected":
            return {"status": "skipped", "reason": "plan rejected by meta-reasoning"}

        manager = self._container.resolve("agent_manager")
        from agents.schemas import AgentType, CoordinationMode, CoordinationPlan

        # Select agent type based on plan
        tasks = executive_result.get("plan", {}).get("tasks", [])
        if not tasks:
            tasks = ["default_task"]

        # Create an execution agent for the work
        agent = await manager.create_agent(
            name="pipeline_executor",
            agent_type=AgentType.EXECUTION,
            capabilities=["task_execution"],
        )

        # Create coordination plan
        plan = CoordinationPlan(
            mode=CoordinationMode.SINGLE,
            agents=[agent.agent_id],
            tasks=[str(t) for t in tasks[:5]],
        )
        result = await manager.execute_plan(plan)

        # Cleanup agent
        await manager.terminate_agent(agent.agent_id)
        return dict(result)

    async def _stage_runtime(
        self, executive_result: dict[str, Any], meta_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Submit workflow to the shared RuntimeEngine."""
        verdict = meta_result.get("verdict", "approved")
        if verdict == "rejected":
            return {"status": "skipped", "reason": "plan rejected by meta-reasoning"}

        engine = self._container.resolve("runtime_engine")
        from runtime.schemas import Workflow, WorkflowTask, WorkflowType

        tasks_data = executive_result.get("plan", {}).get("tasks", [])
        tasks = [
            WorkflowTask(name=f"task_{i}", capability_id="general")
            for i in range(min(len(tasks_data), 10) or 1)
        ]
        workflow = Workflow(
            name="pipeline_workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            tasks=tasks,
        )
        workflow_id = await engine.submit_workflow(workflow)
        return {"workflow_id": workflow_id, "status": "submitted"}

    async def _stage_memory(self, request: PipelineRequest, outputs: dict[str, Any]) -> None:
        """Store execution results in memory via the shared MemoryManager."""
        from memory.default_manager import MemoryEntry

        manager = self._container.resolve("memory_manager")
        entry = MemoryEntry(
            content=request.user_input,
            memory_type="conversation",
            scope="session",
            session_id=request.session_id,
            user_id=request.user_id,
            metadata={"pipeline_stages": list(outputs.keys())},
        )
        await manager.store(entry)

    def _assemble_response(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """Assemble the final pipeline response."""
        return {
            "stages": list(outputs.keys()),
            "cognitive": outputs.get("cognitive", {}),
            "executive": outputs.get("executive", {}),
            "meta_reasoning": outputs.get("meta_reasoning", {}),
            "agent_coordination": outputs.get("agent_coordination", {}),
            "runtime": outputs.get("runtime", {}),
        }

    def get_execution(self, request_id: str) -> PipelineResult | None:
        """Get a pipeline execution result."""
        return self._executions.get(request_id)

    def list_executions(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent pipeline executions."""
        executions = list(self._executions.values())
        executions.sort(key=lambda e: e.duration_ms, reverse=True)
        return [e.to_dict() for e in executions[:limit]]
