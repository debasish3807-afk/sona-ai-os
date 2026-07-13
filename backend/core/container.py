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
        self._build_agents()
        self._wire_ipc()
        await self._hydrate_state()
        self._initialized = True
        logger.info("container_initialized", services=len(self._instances))

    async def shutdown(self) -> None:
        """Shutdown all managed services — persist state first."""
        await self._persist_state()
        persistence = self._instances.get("persistence")
        if persistence is not None:
            await persistence.shutdown()
        self._initialized = False
        logger.info("container_shutdown")

    # ─── Persistence Lifecycle ────────────────────────────────────────────

    async def _hydrate_state(self) -> None:
        """Hydrate subsystem state from persistence on startup."""
        persistence = self._instances.get("persistence")
        if persistence is None:
            return
        try:
            await persistence.initialize()
            # Hydrate memory
            memory_records = await persistence.read("state", "memory_entries")
            if memory_records:
                manager = self._instances.get("memory_manager")
                if manager:
                    entries = memory_records.get("entries", [])
                    await manager.hydrate_from_persistence(entries)
                    logger.info("memory_hydrated", entries=len(entries))
        except Exception as exc:
            logger.warning("hydration_failed", error=str(exc))

    async def _persist_state(self) -> None:
        """Persist subsystem state before shutdown."""
        persistence = self._instances.get("persistence")
        if persistence is None:
            return
        try:
            await persistence.initialize()
            # Persist memory
            manager = self._instances.get("memory_manager")
            if manager:
                entries = [e.to_dict() for e in manager._entries.values()]
                await persistence.write("state", "memory_entries", {"entries": entries})

            # Persist runtime workflows
            engine = self._instances.get("runtime_engine")
            if engine:
                workflows = [w.to_dict() for w in engine.list_workflows()]
                await persistence.write("state", "runtime_workflows", {"workflows": workflows})

            # Persist goals
            brain = self._instances.get("executive_brain")
            if brain:
                goals = [g.to_dict() for g in brain.list_goals()]
                await persistence.write("state", "executive_goals", {"goals": goals})

            logger.info("state_persisted")
        except Exception as exc:
            logger.warning("persistence_failed", error=str(exc))

    # ─── IPC Wiring ──────────────────────────────────────────────────────

    def _wire_ipc(self) -> None:
        """Subscribe services to IPC channels for inter-service messaging."""
        ipc_bus = self._instances.get("ipc_bus")
        if ipc_bus is None:
            return

        # Register IPC handlers for each subsystem
        ipc_bus.subscribe("executive", self._ipc_handler_executive)
        ipc_bus.subscribe("runtime", self._ipc_handler_runtime)
        ipc_bus.subscribe("agents", self._ipc_handler_agents)
        ipc_bus.subscribe("memory", self._ipc_handler_memory)
        ipc_bus.subscribe("meta_reasoning", self._ipc_handler_meta)
        logger.info("ipc_channels_wired", channels=5)

    def _ipc_handler_executive(self, message: Any) -> None:
        """Handle IPC messages directed to the executive layer."""
        logger.debug("ipc_received_executive", message_id=getattr(message, "message_id", ""))

    def _ipc_handler_runtime(self, message: Any) -> None:
        """Handle IPC messages directed to the runtime engine."""
        logger.debug("ipc_received_runtime", message_id=getattr(message, "message_id", ""))

    def _ipc_handler_agents(self, message: Any) -> None:
        """Handle IPC messages directed to the agent system."""
        logger.debug("ipc_received_agents", message_id=getattr(message, "message_id", ""))

    def _ipc_handler_memory(self, message: Any) -> None:
        """Handle IPC messages directed to the memory manager."""
        logger.debug("ipc_received_memory", message_id=getattr(message, "message_id", ""))

    def _ipc_handler_meta(self, message: Any) -> None:
        """Handle IPC messages directed to meta-reasoning."""
        logger.debug("ipc_received_meta", message_id=getattr(message, "message_id", ""))

    # ─── Build Methods ────────────────────────────────────────────────────

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
        """Build the runtime engine."""
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

    def _build_agents(self) -> None:
        """Build the multi-agent coordination system."""
        from agents.agent_coordinator import AgentCoordinator
        from agents.agent_executor import AgentExecutor
        from agents.agent_factory import AgentFactory
        from agents.agent_lifecycle import AgentLifecycle
        from agents.agent_manager import AgentManager
        from agents.agent_negotiator import AgentNegotiator
        from agents.agent_registry import AgentRegistry
        from agents.agent_runtime_bridge import AgentRuntimeBridge
        from agents.agent_scheduler import AgentScheduler
        from agents.agent_supervisor import AgentSupervisor

        registry = AgentRegistry()
        factory = AgentFactory()
        negotiator = AgentNegotiator()
        scheduler = AgentScheduler()
        coordinator = AgentCoordinator(
            registry=registry, scheduler=scheduler, negotiator=negotiator
        )
        lifecycle = AgentLifecycle()
        executor = AgentExecutor(lifecycle=lifecycle)
        supervisor = AgentSupervisor()

        # Bridge uses the SHARED runtime engine
        runtime_engine = self._instances["runtime_engine"]
        bridge = AgentRuntimeBridge(engine=runtime_engine)

        manager = AgentManager(
            registry=registry,
            factory=factory,
            coordinator=coordinator,
            executor=executor,
            supervisor=supervisor,
        )

        self._instances["agent_manager"] = manager
        self._instances["agent_registry"] = registry
        self._instances["agent_coordinator"] = coordinator
        self._instances["agent_runtime_bridge"] = bridge
        self._instances["agent_supervisor"] = supervisor

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
