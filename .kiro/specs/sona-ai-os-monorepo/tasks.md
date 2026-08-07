# Implementation Plan: Sona AI OS Production-Grade Monorepo Restructuring

## Overview

This implementation plan restructures the existing Sona AI OS codebase into a production-grade monorepo following Clean Architecture and Domain-Driven Design principles. The first milestone focuses exclusively on scaffolding: directory structure, interface definitions (abstract ports), configuration schemas, Docker orchestration, CI/CD pipelines, and development tooling. No AI logic is implemented — only the architectural foundation.

The tasks are ordered to build incrementally: shared libraries first (foundation), then services (depend on shared libs), then infrastructure (depends on services), then client apps, and finally documentation and dev tooling.

## Tasks


- [x] 1. Set up root workspace and shared kernel library
  - [x] 1.1 Create root pyproject.toml with Python workspace configuration
    - Define workspace members for all services and libs
    - Set Python >=3.12 requirement
    - Configure ruff, mypy, and pytest settings at workspace level
    - _Requirements: 39.1, 39.2_

  - [x] 1.2 Create shared kernel library structure and domain primitives
    - Create `libs/shared-kernel/` with `sona_shared/domain/`, `sona_shared/ports/`, `sona_shared/config/`, `sona_shared/utils/` directories
    - Implement `EntityId` value object (frozen dataclass wrapping UUID)
    - Implement `Timestamp` value object (frozen dataclass wrapping datetime)
    - Implement base `Entity` class with id, created_at, updated_at fields
    - Implement `DomainEvent` base class with event_id, occurred_at, aggregate_id
    - Implement generic `Result[T, E]` with ok(), fail(), is_success, value, error
    - Ensure ValueError raised when accessing value on failed Result
    - Ensure ValueError raised when accessing error on successful Result
    - Create `libs/shared-kernel/pyproject.toml` declaring "sona-shared-kernel" with Python 3.12 minimum
    - Add `__init__.py` files exporting all public types
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [ ]* 1.3 Write property tests for shared kernel Result type
    - **Property 1: Result Type Round-Trip** — Result.ok(T) yields is_success==True and .value==T; Result.fail(E) yields is_success==False and .error==E
    - **Property 2: Result Access Safety** — accessing .value on failed Result raises ValueError; accessing .error on successful Result raises ValueError
    - **Validates: Requirements 1.3, 1.7, 1.8**


- [x] 2. Create LLM Client and Event Bus shared libraries
  - [x] 2.1 Create LLM Client shared library
    - Create `libs/llm-client/` with `sona_llm/` package and `tests/` directory
    - Define abstract interfaces for chat completion, streaming, and embedding generation
    - Define provider configuration models for Ollama, OpenAI, Anthropic, and Google AI
    - Create `libs/llm-client/pyproject.toml` declaring "sona-llm-client" with Python 3.12 minimum
    - Add dependency on sona-shared-kernel
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

  - [x] 2.2 Create Event Bus shared library
    - Create `libs/event-bus/` with `sona_events/` package and `tests/` directory
    - Define abstract interfaces for event publishing and subscription
    - Define typed event handler protocol accepting specific DomainEvent subtypes
    - Create `libs/event-bus/pyproject.toml` declaring "sona-event-bus" with Python 3.12 minimum
    - Add dependency on sona-shared-kernel
    - _Requirements: 17.1, 17.2, 17.3, 17.4_


- [x] 3. Checkpoint - Verify shared libraries
  - Ensure all shared library packages are importable and pyproject.toml files are valid
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Scaffold AI Kernel and Thalamus Router services
  - [x] 4.1 Scaffold AI Kernel service with interfaces
    - Create `services/ai-kernel/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `ReasoningStrategy` enum (DIRECT, CHAIN_OF_THOUGHT, TREE_OF_THOUGHT, REFLECTION)
    - Define `ModelConfig`, `KernelRequest`, `KernelResponse` frozen dataclasses
    - Define `AIKernelPort` abstract class with process(), stream(), select_model() async methods
    - Define `ReasoningEnginePort` abstract class with reason() async method
    - Define `ModelRouterPort` abstract class with route(), list_available() async methods
    - Create pyproject.toml with dependencies on sona-shared-kernel, sona-llm-client, sona-event-bus
    - Add `__init__.py` files with proper exports
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 4.2 Scaffold Thalamus Router service with interfaces
    - Create `services/thalamus-router/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `IntentCategory` enum (CHAT, RESEARCH, CODE, AUTOMATION, MEMORY, SYSTEM)
    - Define `RequestPriority` enum (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)
    - Define `RoutingDecision` frozen dataclass with target_service, intent, priority, requires_agents, estimated_latency_ms, fallback_service
    - Define `ThalamusRouterPort` abstract class with classify_intent(), route(), health_check() async methods
    - Define `LoadBalancerPort` abstract class with get_service_load(), select_instance() async methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_


- [x] 5. Scaffold Brain OS and Memory OS services
  - [x] 5.1 Scaffold Brain OS service with interfaces
    - Create `services/brain-os/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `BrainRequest` and `BrainResponse` frozen dataclasses with all design-specified fields
    - Define `BrainOrchestratorPort` abstract class with execute(), execute_stream(), get_session_context() async methods
    - Define `PipelineStagePort` abstract class with execute() and should_skip() methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 5.2 Scaffold Memory OS service with interfaces
    - Create `services/memory-os/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `MemoryType` enum (WORKING, SHORT_TERM, LONG_TERM, EPISODIC, SEMANTIC)
    - Define `MemoryEntry` frozen dataclass with id, memory_type, content, embedding, metadata, importance, created_at, expires_at, tags
    - Define `MemoryQuery` frozen dataclass with user_id, query, memory_types, top_k, min_importance, time_range
    - Define `MemoryStorePort` abstract class with store(), retrieve(), consolidate(), forget(), get_conversation_history() async methods
    - Define `EmbeddingPort` abstract class with embed(), embed_batch() async methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_


- [x] 6. Scaffold Knowledge OS and Workforce OS services
  - [x] 6.1 Scaffold Knowledge OS service with interfaces
    - Create `services/knowledge-os/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `DocumentType` enum (PDF, MARKDOWN, TEXT, HTML, CODE, JSON)
    - Define `Document`, `DocumentChunk`, `RAGQuery`, `RAGResult` frozen dataclasses per design
    - Define `KnowledgeBasePort` abstract class with ingest(), query(), list_knowledge_bases(), delete_document() async methods
    - Define `DocumentProcessorPort` abstract class with process(), extract_text() async methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 6.2 Scaffold Workforce OS service with interfaces
    - Create `services/workforce-os/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `AgentType` enum (CODING, RESEARCH, PLANNER, AUTOMATION, COMMUNICATION, SYSTEM, VOICE, VISION, WEB, ANDROID, CUSTOM)
    - Define `AgentStatus` enum (IDLE, BUSY, ERROR, STOPPED)
    - Define `AgentTask` and `AgentResult` frozen dataclasses per design
    - Define `AgentPort` abstract class with initialize(), process(), get_capabilities(), health_check() async methods
    - Define `AgentCoordinatorPort` abstract class with dispatch(), dispatch_parallel(), register_agent(), list_agents() async methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_


- [x] 7. Scaffold Workflow Engine and MCP Integration services
  - [x] 7.1 Scaffold Workflow Engine service with interfaces
    - Create `services/workflow-engine/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `StepStatus` enum (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, WAITING)
    - Define `WorkflowStep` frozen dataclass with step_id, name, action, params, depends_on, retry_count, timeout_seconds, condition
    - Define `WorkflowDefinition` and `WorkflowExecution` dataclasses per design
    - Define `WorkflowEnginePort` abstract class with create_workflow(), execute(), get_status(), cancel(), resume() async methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 7.2 Scaffold MCP Integration service with interfaces
    - Create `services/mcp-integration/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `MCPTransport` enum (STDIO, SSE, WEBSOCKET)
    - Define `ToolPermission` enum (READ, WRITE, EXECUTE, ADMIN)
    - Define `MCPTool`, `MCPServer`, `ToolCallResult` frozen dataclasses per design
    - Define `MCPManagerPort` abstract class with register_server(), discover_tools(), call_tool(), list_servers(), health_check() async methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_


- [x] 8. Scaffold Research OS, AI Engineering OS, and Evaluation OS services
  - [x] 8.1 Scaffold Research OS service with interfaces
    - Create `services/research-os/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define abstract port interfaces for web search, content extraction, and summarization
    - Define data models for research queries, search results, and synthesized reports
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 8.2 Scaffold AI Engineering OS service with interfaces
    - Create `services/ai-engineering-os/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define abstract port interfaces for code generation, code review, and debugging
    - Define data models for code requests, generation results, and review feedback
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 8.3 Scaffold Evaluation OS service with interfaces
    - Create `services/evaluation-os/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define abstract port interfaces for quality evaluation, metric collection, and regression testing
    - Define data models for evaluation requests, metric results, and quality reports
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 12.1, 12.2, 12.3, 12.4_


- [ ] 9. Scaffold Security, Observability, and Plugin System services
  - [~] 9.1 Scaffold Security Layer service with interfaces
    - Create `services/security/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `Role` enum (ADMIN, USER, SERVICE, READONLY)
    - Define `AuthToken` and `Permission` frozen dataclasses per design
    - Define `AuthenticationPort` abstract class with authenticate(), validate_token(), refresh_token(), revoke_token() async methods
    - Define `AuthorizationPort` abstract class with check_permission(), get_user_roles(), assign_role() async methods
    - Define `AISafetyPort` abstract class with check_input(), check_output(), audit_log() async methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [~] 9.2 Scaffold Observability service with interfaces
    - Create `services/observability/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `MetricType` enum (COUNTER, GAUGE, HISTOGRAM, SUMMARY)
    - Define `LogLevel` enum (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Define `SpanContext` frozen dataclass with trace_id, span_id, parent_span_id, service_name, operation
    - Define `MetricsPort` abstract class with increment(), gauge(), histogram() methods
    - Define `TracingPort` abstract class with start_span(), end_span(), inject_context() methods
    - Define `LoggingPort` abstract class with log(), with_context() methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [~] 9.3 Scaffold Plugin System service with interfaces
    - Create `services/plugin-system/` with `domain/`, `application/`, `infrastructure/`, `tests/` directories
    - Define `PluginStatus` enum (ACTIVE, INACTIVE, ERROR, LOADING)
    - Define `PluginManifest` and `PluginInstance` dataclasses per design
    - Define `PluginPort` abstract class with activate(), deactivate(), get_capabilities(), health_check() async methods
    - Define `PluginRegistryPort` abstract class with install(), uninstall(), activate(), deactivate(), list_plugins() async methods
    - Create pyproject.toml with dependency on sona-shared-kernel
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_


- [~] 10. Checkpoint - Verify all service scaffolds
  - Ensure all 14 service directories exist with correct structure
  - Ensure all pyproject.toml files are syntactically valid
  - Ensure all abstract port interfaces are defined correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement configuration schemas and API models
  - [~] 11.1 Create service configuration schema with Pydantic models
    - Create configuration module in `libs/shared-kernel/sona_shared/config/`
    - Define `Environment` enum (LOCAL, DEVELOPMENT, STAGING, PRODUCTION)
    - Define `DatabaseConfig` Pydantic model with host, port, name, user, password (excluded), pool_size, pool_overflow, ssl_mode
    - Define `RedisConfig` Pydantic model with url, max_connections, decode_responses, socket_timeout
    - Define `VectorDBConfig` Pydantic model with url, collection_prefix, embedding_dimension, distance_metric
    - Define `LLMProviderConfig` Pydantic model with provider, api_key (excluded), base_url, model_id, max_tokens, timeout_seconds, retry_count
    - Define `ServiceConfig` root model with all fields per design
    - Add validation: port range 1-65535, pool_size must be positive
    - Add environment variable loading with SERVICE_NAME prefix convention
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7_

  - [ ]* 11.2 Write property tests for configuration validation
    - **Property 3: Configuration Password Exclusion** — serializing any config with password field SHALL never include password in output
    - **Property 4: Configuration Validation Rejects Invalid Numerics** — port outside [1,65535] and pool_size <=0 produce validation errors
    - **Validates: Requirements 19.4, 19.5, 19.6**

  - [~] 11.3 Create API Gateway request/response Pydantic models
    - Create `gateway/app/models/` directory
    - Define `ChatMessage` model with role (user/assistant/system), content (1-100K chars), name, timestamp
    - Define `ChatRequest` model with messages (min 1), model, stream, temperature (0.0-2.0), max_tokens (1-128000), session_id, metadata
    - Define `TokenUsage` model with prompt_tokens, completion_tokens, total_tokens
    - Define `ChatResponse` model with content, model_used, usage, session_id, latency_ms, created_at
    - Ensure proper validation error (422) for invalid role, empty content, out-of-range temperature, empty messages list
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7_

  - [ ]* 11.4 Write property tests for API model validation
    - **Property 5: API Model Validation Rejects Out-of-Bound Values** — invalid role, temperature outside [0.0, 2.0], max_tokens outside [1, 128000] all produce validation errors
    - **Validates: Requirements 20.4, 20.6**


- [ ] 12. Scaffold API Gateway with routes and middleware
  - [~] 12.1 Create API Gateway application structure
    - Create `gateway/app/main.py` with FastAPI application entry point
    - Create `gateway/app/routes/` directory with `chat.py`, `models.py`, `providers.py`, `health.py` route modules
    - Create `gateway/app/middleware/` directory with `authentication.py`, `rate_limiting.py`, `cors.py` modules
    - Create `gateway/app/deps.py` for dependency injection
    - Define health endpoint returning HTTP 200 when service is ready
    - Create `gateway/tests/` directory with `__init__.py`
    - _Requirements: 18.1, 18.2, 18.3, 18.6_

  - [~] 12.2 Create Gateway pyproject.toml and Dockerfile
    - Create `gateway/pyproject.toml` declaring dependencies on FastAPI 0.115+, Pydantic 2.0+, uvicorn, structlog, and shared libs
    - Create `gateway/Dockerfile` for containerized deployment (multi-stage, non-root user UID 1000, slim base)
    - _Requirements: 18.4, 18.5, 38.1, 38.4_

- [ ] 13. Create Docker Compose orchestration
  - [~] 13.1 Create main Docker Compose and infrastructure configuration
    - Create `infra/compose/docker-compose.yml` with services: gateway, postgres, redis, qdrant, nginx, web
    - Configure PostgreSQL 16 with healthcheck (pg_isready), named volume for data
    - Configure Redis 7 with healthcheck (redis-cli ping), maxmemory 512MB with LRU eviction, named volume
    - Configure Qdrant with persistent volume storage
    - Configure gateway with depends_on conditions (postgres, redis, qdrant healthy)
    - Define named volumes: pgdata, redisdata, qdrantdata
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.7_

  - [~] 13.2 Create environment-specific Docker Compose overrides
    - Create `infra/compose/docker-compose.dev.yml` with development overrides (volume mounts, debug mode)
    - Create `infra/compose/docker-compose.test.yml` with test configuration (ephemeral volumes, test env)
    - Create `infra/compose/docker-compose.prod.yml` with production configuration (resource limits, no debug)
    - _Requirements: 21.6_

  - [~] 13.3 Create multi-stage service Dockerfile and Nginx configuration
    - Create `infra/docker/Dockerfile.service` accepting SERVICE_NAME build argument
    - Use multi-stage build: builder stage installs deps, runtime stage copies only needed artifacts
    - Run as non-root user (UID 1000), use slim base image
    - Create `infra/docker/Dockerfile.gateway` for the gateway service
    - Create `infra/docker/Dockerfile.web` for web frontend
    - Create `infra/docker/Dockerfile.nginx` and `infra/nginx/nginx.conf` with reverse proxy configuration
    - _Requirements: 21.8, 38.1, 38.2, 38.3, 38.4_


- [~] 14. Checkpoint - Verify gateway and Docker setup
  - Ensure gateway app is importable and health endpoint is defined
  - Ensure Docker Compose files are syntactically valid YAML
  - Ensure all Dockerfiles build without errors
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Create CI/CD pipeline configuration
  - [~] 15.1 Create unified CI pipeline with monorepo-aware change detection
    - Create `.github/workflows/ci.yml` with trigger on push to main/develop and PRs targeting those branches
    - Implement path-filter job detecting backend, frontend, android, and infra changes
    - Create `backend-lint` job: ruff check and ruff format --check on services/, libs/, gateway/
    - Create `backend-test` job: install shared libs first, then run pytest with coverage
    - Create `frontend-ci` job: npm ci, lint, test --run, build in apps/web/
    - Create `android-ci` job: gradlew lint test in apps/android/
    - Ensure jobs only run when their respective paths change
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7_

  - [~] 15.2 Create deployment workflow files
    - Create `.github/workflows/deploy-dev.yml` for dev environment deployment
    - Create `.github/workflows/deploy-staging.yml` for staging deployment
    - Create `.github/workflows/deploy-prod.yml` for production deployment
    - Include container vulnerability scanning step in build jobs
    - _Requirements: 22.8, 38.5_

- [ ] 16. Scaffold React web frontend application
  - [~] 16.1 Create web app directory structure and configuration
    - Create `apps/web/src/app/`, `apps/web/src/features/`, `apps/web/src/shared/`, `apps/web/src/infrastructure/` directories
    - Create `apps/web/public/` and `apps/web/tests/` directories
    - Create `apps/web/package.json` with React 19, TypeScript 6, Vite 8, TanStack Query 5, Vitest dependencies
    - Include lint, test (using Vitest --run for CI), and build scripts
    - _Requirements: 23.1, 23.2, 23.5, 23.6_

  - [~] 16.2 Create web app build configuration and Dockerfile
    - Create `apps/web/vite.config.ts` with React plugin and path aliases
    - Create `apps/web/tsconfig.json` with strict TypeScript configuration
    - Create `apps/web/Dockerfile` for containerized deployment (multi-stage, nginx serve)
    - _Requirements: 23.3, 23.4_


- [ ] 17. Scaffold Kotlin Android application
  - [~] 17.1 Create Android app directory structure and build configuration
    - Create `apps/android/app/src/main/` directory structure
    - Create `apps/android/core/domain/`, `apps/android/core/data/`, `apps/android/core/di/` directories
    - Create `apps/android/features/chat/`, `apps/android/features/settings/`, `apps/android/features/voice/` directories
    - Create `apps/android/build.gradle.kts` with Kotlin 2.0+, Jetpack Compose BOM 2024, Hilt 2.51+, Retrofit 2.11+, Room 2.6+
    - Create `apps/android/settings.gradle.kts` including all feature modules
    - Create `apps/android/gradle.properties` with required Gradle settings
    - Include lint and test Gradle task configuration
    - Configure Hilt for dependency injection across all feature modules
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5_

- [ ] 18. Create development environment setup and tooling
  - [~] 18.1 Create development setup script
    - Create `infra/scripts/setup-dev.sh` (executable)
    - Verify Python 3.12+, Node.js 20+, and Docker are installed
    - Print clear error messages for missing prerequisites
    - Create Python virtual environments and install all service dependencies
    - Install Node.js dependencies for apps/web/
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5_

  - [~] 18.2 Create root Makefile with standard commands
    - Create `Makefile` at repository root
    - Provide commands: setup (run setup-dev.sh), lint (ruff check + format), test (pytest), build (Docker), up (docker compose up), down (docker compose down)
    - _Requirements: 25.6_


- [ ] 19. Create documentation structure
  - [~] 19.1 Create documentation directory tree and architecture docs
    - Create `docs/architecture/` with README.md, system-overview.md, module-boundaries.md, data-flow.md
    - Create `docs/development/` with getting-started.md, contributing.md, coding-standards.md, testing-guide.md
    - Create `docs/api/` with gateway.md, internal-services.md
    - Create `docs/deployment/` with local.md, staging.md, production.md
    - Update root README.md describing monorepo structure, getting started, and links to detailed docs
    - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5_

- [~] 20. Final checkpoint - Verify complete monorepo structure
  - Verify all 14 services are scaffolded with proper directory structure
  - Verify all 3 shared libraries exist with correct package names
  - Verify gateway app, Docker Compose, CI/CD pipelines are in place
  - Verify web frontend and Android app scaffolds exist
  - Verify existing `backend/` directory is preserved untouched
  - Verify development scripts and Makefile work
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The existing `backend/` directory is explicitly preserved — no files are modified or deleted from it
- All new code goes into the new `services/`, `libs/`, `gateway/`, `apps/`, `infra/`, and `docs/` directories
- Python 3.12+ is required for all backend code; use StrEnum, type hints, and dataclasses throughout
- All services follow Clean Architecture: domain (models, events) → application (use cases, ports) → infrastructure (adapters)


## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "2.1", "2.2"] },
    { "id": 3, "tasks": ["4.1", "4.2", "5.1", "5.2", "6.1", "6.2", "7.1", "7.2", "8.1", "8.2", "8.3", "9.1", "9.2", "9.3"] },
    { "id": 4, "tasks": ["11.1"] },
    { "id": 5, "tasks": ["11.2", "11.3"] },
    { "id": 6, "tasks": ["11.4", "12.1"] },
    { "id": 7, "tasks": ["12.2", "13.1"] },
    { "id": 8, "tasks": ["13.2", "13.3"] },
    { "id": 9, "tasks": ["15.1", "15.2", "16.1", "17.1"] },
    { "id": 10, "tasks": ["16.2", "18.1"] },
    { "id": 11, "tasks": ["18.2", "19.1"] }
  ]
}
```
