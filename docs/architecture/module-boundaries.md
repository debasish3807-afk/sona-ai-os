# Module Boundaries

This document describes the 14 core service boundaries in Sona AI OS, their responsibilities, and how they communicate with each other.

## Boundary Rules

All inter-service communication follows these strict rules:

1. Services **only** communicate through defined port interfaces (Python ABCs)
2. No service may import implementation code from another service
3. Domain and Application layers **cannot** depend on Infrastructure layers
4. The Shared Kernel (`libs/shared-kernel`) is the only cross-service shared code
5. All external side effects (DB, HTTP, queue) are behind adapters in the Infrastructure layer

---

## 1. AI Kernel (`services/ai-kernel`)

**Responsibility**: Central intelligence engine. Manages reasoning chains, model selection, context assembly, and response generation.

**Exposes**:
- `AIKernelPort` — `process()`, `stream()`, `select_model()`
- `ReasoningEnginePort` — `reason(prompt, context, strategy)`
- `ModelRouterPort` — `route()`, `list_available()`

**Depends on**: `sona-shared-kernel`, `sona-llm-client`, `sona-event-bus`

**Never depends on**: `brain-os`, `thalamus-router`, `workforce-os`

---

## 2. Thalamus Router (`services/thalamus-router`)

**Responsibility**: Named after the brain's thalamus relay center. Classifies intent and routes requests to the appropriate downstream service based on load and health.

**Exposes**:
- `ThalamusRouterPort` — `classify_intent()`, `route()`, `health_check()`
- `LoadBalancerPort` — `get_service_load()`, `select_instance()`

**Depends on**: `sona-shared-kernel`

**Never depends on**: `brain-os`, `ai-kernel`

---

## 3. Brain OS (`services/brain-os`)

**Responsibility**: Central orchestrator. Connects all subsystems through a composable pipeline: memory retrieval → routing → model selection → LLM execution → memory storage.

**Exposes**:
- `BrainOrchestratorPort` — `execute()`, `execute_stream()`, `get_session_context()`
- `PipelineStagePort` — `execute(context)`, `should_skip(context)`

**Depends on**: `sona-shared-kernel`, `ai-kernel` (port), `memory-os` (port), `thalamus-router` (port), `workforce-os` (port)

---

## 4. Memory OS (`services/memory-os`)

**Responsibility**: All forms of memory (working, short-term, long-term, episodic, semantic). Provides vector similarity retrieval, consolidation, and forgetting.

**Exposes**:
- `MemoryStorePort` — `store()`, `retrieve()`, `consolidate()`, `forget()`, `get_conversation_history()`
- `EmbeddingPort` — `embed()`, `embed_batch()`

**Depends on**: `sona-shared-kernel`

**Storage**: Redis (working/short-term), Qdrant (semantic/episodic vector search), PostgreSQL (long-term)

---

## 5. Knowledge OS (`services/knowledge-os`)

**Responsibility**: RAG (Retrieval-Augmented Generation) pipeline. Document ingestion, chunking, embedding, indexing, and context-augmented retrieval.

**Exposes**:
- `KnowledgeBasePort` — `ingest()`, `query()`, `list_knowledge_bases()`, `delete_document()`
- `DocumentProcessorPort` — `process()`, `extract_text()`

**Depends on**: `sona-shared-kernel`

**Storage**: Qdrant (vector embeddings), PostgreSQL (document metadata)

---

## 6. Workforce OS (`services/workforce-os`)

**Responsibility**: Multi-agent system. Specialized agents for coding, research, planning, automation, voice, vision, web, and Android. Manages parallel agent dispatch and lifecycle.

**Exposes**:
- `AgentCoordinatorPort` — `dispatch()`, `dispatch_parallel()`, `register_agent()`, `list_agents()`
- `AgentPort` — `initialize()`, `process()`, `get_capabilities()`, `health_check()`

**Depends on**: `sona-shared-kernel`, `mcp-integration` (port)

---

## 7. Workflow Engine (`services/workflow-engine`)

**Responsibility**: Task automation with multi-step workflows, conditional branching, retries, scheduled execution, and human-in-the-loop pausing.

**Exposes**:
- `WorkflowEnginePort` — `create_workflow()`, `execute()`, `get_status()`, `cancel()`, `resume()`

**Depends on**: `sona-shared-kernel`

**Storage**: PostgreSQL (workflow definitions and execution state)

---

## 8. MCP Integration (`services/mcp-integration`)

**Responsibility**: Model Context Protocol implementation. Manages external tool servers (stdio, SSE, WebSocket), tool discovery, and permission-gated execution.

**Exposes**:
- `MCPManagerPort` — `register_server()`, `discover_tools()`, `call_tool()`, `list_servers()`, `health_check()`

**Depends on**: `sona-shared-kernel`

---

## 9. Research OS (`services/research-os`)

**Responsibility**: Web research, content extraction, and multi-source synthesis. Powers the research agent in Workforce OS.

**Exposes**:
- `WebSearchPort`, `ContentExtractorPort`, `SummarizerPort`

**Depends on**: `sona-shared-kernel`

---

## 10. AI Engineering OS (`services/ai-engineering-os`)

**Responsibility**: Code generation, code review, debugging assistance, and code quality analysis.

**Exposes**:
- `CodeGeneratorPort`, `CodeReviewerPort`, `DebuggerPort`

**Depends on**: `sona-shared-kernel`

---

## 11. Evaluation OS (`services/evaluation-os`)

**Responsibility**: Quality evaluation, metric collection, regression testing, and model performance benchmarking.

**Exposes**:
- `EvaluationPort`, `MetricCollectorPort`, `RegressionTesterPort`

**Depends on**: `sona-shared-kernel`

---

## 12. Security (`services/security`)

**Responsibility**: JWT authentication, RBAC authorization, API key management, prompt injection detection, output safety filtering, and audit logging.

**Exposes**:
- `AuthenticationPort` — `authenticate()`, `validate_token()`, `refresh_token()`, `revoke_token()`
- `AuthorizationPort` — `check_permission()`, `get_user_roles()`, `assign_role()`
- `AISafetyPort` — `check_input()`, `check_output()`, `audit_log()`

**Depends on**: `sona-shared-kernel`

**Storage**: PostgreSQL (users, roles, revocation lists), Redis (token cache)

---

## 13. Observability (`services/observability`)

**Responsibility**: Structured JSON logging with correlation IDs, distributed tracing with context propagation, and Prometheus-compatible metrics export.

**Exposes**:
- `MetricsPort` — `increment()`, `gauge()`, `histogram()`
- `TracingPort` — `start_span()`, `end_span()`, `inject_context()`
- `LoggingPort` — `log()`, `with_context()`

**Depends on**: `sona-shared-kernel`

---

## 14. Plugin System (`services/plugin-system`)

**Responsibility**: Third-party extension framework. Plugin installation, activation, sandboxed execution, permission management, and version compatibility.

**Exposes**:
- `PluginPort` — `activate()`, `deactivate()`, `get_capabilities()`, `health_check()`
- `PluginRegistryPort` — `install()`, `uninstall()`, `activate()`, `deactivate()`, `list_plugins()`

**Depends on**: `sona-shared-kernel`, `mcp-integration` (port)

---

## Dependency Matrix

| Consumer → | shared-kernel | ai-kernel | memory-os | knowledge-os | workforce-os | mcp | security | observability |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| brain-os | ✓ | port | port | - | port | - | - | port |
| ai-kernel | ✓ | - | - | - | - | - | - | port |
| thalamus-router | ✓ | - | - | - | - | - | - | port |
| workforce-os | ✓ | - | - | - | - | port | - | port |
| gateway | ✓ | - | - | - | - | - | port | port |

All dependencies are on **ports** (abstract interfaces), never on concrete implementations.
