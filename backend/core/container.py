"""Dependency Injection Container — centralizes object creation and lifecycle."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class Container:
    """Central DI container for Sona AI OS.

    Manages singleton instances and provides factory methods
    for all major subsystems. Replaces scattered global singletons.
    """

    def __init__(self) -> None:
        self._instances: dict[str, Any] = {}
        self._factories: dict[str, Any] = {}
        self._initialized: bool = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    def register_factory(self, name: str, factory: Any) -> None:
        """Register a factory function for lazy instantiation."""
        self._factories[name] = factory

    def register_instance(self, name: str, instance: Any) -> None:
        """Register a pre-built instance."""
        self._instances[name] = instance

    def resolve(self, name: str) -> Any:
        """Resolve a dependency by name. Creates via factory if needed."""
        if name in self._instances:
            return self._instances[name]
        if name in self._factories:
            instance = self._factories[name]()
            self._instances[name] = instance
            return instance
        raise KeyError(f"No registration found for '{name}'")

    def has(self, name: str) -> bool:
        """Check if a dependency is registered."""
        return name in self._instances or name in self._factories

    async def initialize(self) -> None:
        """Initialize the container and boot all services."""
        if self._initialized:
            return
        self._build_security()
        self._build_microkernel()
        self._build_cognitive()
        self._build_executive()
        self._build_meta_reasoning()
        self._build_capabilities()
        self._build_runtime()
        self._build_memory()
        self._build_persistence()
        self._initialized = True
        logger.info("container_initialized", services=len(self._instances))

    async def shutdown(self) -> None:
        """Shutdown all managed services."""
        persistence = self._instances.get("persistence")
        if persistence is not None:
            await persistence.shutdown()
        self._initialized = False
        logger.info("container_shutdown")

    def _build_security(self) -> None:
        """Build security services."""
        from security.api_keys import APIKeyManager
        from security.audit import AuditLogger
        from security.rate_limit import RateLimiter
        from security.sessions import SessionManager

        self._instances["api_key_manager"] = APIKeyManager()
        self._instances["audit_logger"] = AuditLogger()
        self._instances["rate_limiter"] = RateLimiter()
        self._instances["session_manager"] = SessionManager()

    def _build_microkernel(self) -> None:
        """Build the microkernel subsystem."""
        from microkernel import (
            HealthMonitor,
            IntentSanitizer,
            InterruptHandler,
            IPCBus,
            Microkernel,
            MicrokernelTelemetry,
            ProcessSupervisor,
            ResourceScheduler,
            SandboxManager,
            ServiceRegistry,
        )

        ipc_bus = IPCBus()
        service_registry = ServiceRegistry()
        sandbox_manager = SandboxManager()
        process_supervisor = ProcessSupervisor()
        resource_scheduler = ResourceScheduler()
        intent_sanitizer = IntentSanitizer()
        interrupt_handler = InterruptHandler()
        health_monitor = HealthMonitor()
        telemetry = MicrokernelTelemetry()

        mk = Microkernel(
            ipc_bus=ipc_bus,
            service_registry=service_registry,
            sandbox_manager=sandbox_manager,
            process_supervisor=process_supervisor,
            resource_scheduler=resource_scheduler,
            intent_sanitizer=intent_sanitizer,
            interrupt_handler=interrupt_handler,
            health_monitor=health_monitor,
            telemetry=telemetry,
        )
        self._instances["microkernel"] = mk
        self._instances["ipc_bus"] = ipc_bus
        self._instances["service_registry"] = service_registry
        self._instances["process_supervisor"] = process_supervisor
        self._instances["resource_scheduler"] = resource_scheduler
        self._instances["intent_sanitizer"] = intent_sanitizer
        self._instances["sandbox_manager"] = sandbox_manager
        self._instances["health_monitor"] = health_monitor
        self._instances["microkernel_telemetry"] = telemetry

    def _build_cognitive(self) -> None:
        """Build the cognitive kernel."""
        from cognitive.kernel import CognitiveKernel

        self._instances["cognitive_kernel"] = CognitiveKernel()

    def _build_executive(self) -> None:
        """Build the executive layer."""
        from executive.approval_engine import ApprovalEngine
        from executive.capability_orchestrator import CapabilityOrchestrator
        from executive.confidence_engine import ConfidenceEngine
        from executive.cost_engine import CostEngine
        from executive.decision_engine import DecisionEngine
        from executive.execution_planner import ExecutionPlanner
        from executive.executive_brain import ExecutiveBrain
        from executive.goal_manager import GoalManager
        from executive.model_selector import ModelSelector
        from executive.parallel_planner import ParallelPlanner
        from executive.provider_selector import ProviderSelector
        from executive.risk_engine import RiskEngine
        from executive.strategic_planner import StrategicPlanner
        from executive.workflow_optimizer import WorkflowOptimizer

        brain = ExecutiveBrain(
            goal_manager=GoalManager(),
            strategic_planner=StrategicPlanner(),
            decision_engine=DecisionEngine(),
            execution_planner=ExecutionPlanner(),
            risk_engine=RiskEngine(),
            cost_engine=CostEngine(),
            confidence_engine=ConfidenceEngine(),
            capability_orchestrator=CapabilityOrchestrator(),
            provider_selector=ProviderSelector(),
            model_selector=ModelSelector(),
            workflow_optimizer=WorkflowOptimizer(),
            parallel_planner=ParallelPlanner(),
            approval_engine=ApprovalEngine(),
        )
        self._instances["executive_brain"] = brain

    def _build_meta_reasoning(self) -> None:
        """Build the meta-reasoning engine."""
        from meta_reasoning.alternative_generator import AlternativeGenerator
        from meta_reasoning.counterfactual_engine import CounterfactualEngine
        from meta_reasoning.critique_engine import CritiqueEngine
        from meta_reasoning.evidence_engine import EvidenceEngine
        from meta_reasoning.hypothesis_engine import HypothesisEngine
        from meta_reasoning.meta_reasoner import MetaReasoner
        from meta_reasoning.plan_refiner import PlanRefiner
        from meta_reasoning.plan_validator import PlanValidator
        from meta_reasoning.quality_estimator import QualityEstimator
        from meta_reasoning.reasoning_memory import ReasoningMemory
        from meta_reasoning.reflection_engine import ReflectionEngine
        from meta_reasoning.simulation_engine import SimulationEngine
        from meta_reasoning.uncertainty_engine import UncertaintyEngine

        reasoner = MetaReasoner(
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
        self._instances["meta_reasoner"] = reasoner

    def _build_capabilities(self) -> None:
        """Build the capabilities fabric."""
        from capabilities.health import HealthMonitor as CapHealthMonitor
        from capabilities.loader import CapabilityLoader
        from capabilities.manager import CapabilityManager
        from capabilities.registry import CapabilityRegistry
        from capabilities.selector import CapabilitySelector

        self._instances["capability_manager"] = CapabilityManager(
            registry=CapabilityRegistry(),
            loader=CapabilityLoader(),
            health_monitor=CapHealthMonitor(),
            selector=CapabilitySelector(),
        )

    def _build_runtime(self) -> None:
        """Build the runtime engine with microkernel integration."""
        from runtime.checkpoint_manager import CheckpointManager
        from runtime.dag_executor import DAGExecutor
        from runtime.recovery_manager import RecoveryManager
        from runtime.retry_manager import RetryManager
        from runtime.rollback_manager import RollbackManager
        from runtime.runtime_engine import RuntimeEngine
        from runtime.task_queue import TaskQueue
        from runtime.worker_pool import WorkerPool
        from runtime.workflow_monitor import WorkflowMonitor
        from runtime.workflow_policies import WorkflowPolicies
        from runtime.workflow_scheduler import WorkflowScheduler

        engine = RuntimeEngine(
            scheduler=WorkflowScheduler(),
            queue=TaskQueue(),
            pool=WorkerPool(),
            dag_executor=DAGExecutor(),
            checkpoint_mgr=CheckpointManager(),
            retry_mgr=RetryManager(),
            rollback_mgr=RollbackManager(),
            recovery_mgr=RecoveryManager(),
            monitor=WorkflowMonitor(),
            policies=WorkflowPolicies(),
        )
        self._instances["runtime_engine"] = engine

    def _build_memory(self) -> None:
        """Build the memory manager."""
        from memory.default_manager import DefaultMemoryManager

        self._instances["memory_manager"] = DefaultMemoryManager()

    def _build_persistence(self) -> None:
        """Build the persistence layer."""
        from adapters.persistence import PersistenceManager

        self._instances["persistence"] = PersistenceManager()

    def get_status(self) -> dict[str, Any]:
        """Return container status."""
        return {
            "initialized": self._initialized,
            "instances": list(self._instances.keys()),
            "factories": list(self._factories.keys()),
            "total_services": len(self._instances),
        }


# Global container singleton
_container: Container | None = None


def get_container() -> Container:
    """Get or create the global DI container."""
    global _container
    if _container is None:
        _container = Container()
    return _container
