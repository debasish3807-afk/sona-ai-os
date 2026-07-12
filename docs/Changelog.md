# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.7.0] — Phase 7: AI Brain Execution Pipeline

### Added

- **AI Brain Orchestrator** — central execution engine connecting all subsystems
  - Full pipeline: Request → Memory → Agent → Provider → Response
  - Provider lifecycle management (init/shutdown)
  - Global singleton with app lifespan integration
- **Ollama Provider** — complete implementation
  - Chat completion (POST /api/chat)
  - Streaming (SSE via POST /api/chat with stream=true)
  - Embeddings (POST /api/embed)
  - Model listing (GET /api/tags)
  - Health check (GET /)
  - Auto-detect localhost:11434
  - Token usage reporting (prompt_eval_count, eval_count)
- **Chat API Endpoints**
  - POST /api/v1/chat — synchronous chat completion
  - POST /api/v1/chat/stream — Server-Sent Events streaming
  - GET /api/v1/models — list all available models
  - GET /api/v1/providers — list providers with status
  - GET /api/v1/health/providers — provider health with latency
- **Memory Bridge** — conversation history integration
  - Retrieve session history for context injection
  - Save user/assistant messages to session memory
  - Build context window with token budget management
- **Agent Router** — intent-based routing
  - Pattern matching for 6 agent categories (general, coding, research, planner, android, web)
  - Specialized system prompts per agent
  - Confidence threshold (minimum 2 pattern matches)
- **CI/CD Pipeline** — complete automation
  - CI workflow: lint (Ruff) → type-check (Mypy) → security (Bandit) → test (Pytest) → validate
  - Development deployment: auto on push to main/develop
  - Production deployment: on tagged releases (v*.*.*)
- **Test Suite** — 65 tests across 9 modules
  - Brain schemas, agent routing, memory bridge, orchestrator
  - API, app factory, config, core, kernel, memory, providers
- **Tooling Configuration** (pyproject.toml)
  - Ruff: Python 3.12 target, 100-char lines, comprehensive rules
  - Mypy: strict checking with ignore-missing-imports
  - Pytest: auto asyncio, strict markers, 50% coverage minimum

### Changed

- Replaced Ollama provider skeleton with full implementation
- Updated API router to include chat endpoints
- Updated app lifespan to initialize/shutdown AI Brain
- Reformatted all 120 files to consistent style (Ruff)
- Fixed async generator type annotations in base classes

---

## [0.6.0] — Phase 6: Memory Engine

### Added

- Memory Engine with 5 memory types (working, short-term, long-term, episodic, semantic)
- MemoryStore ABC with CRUD, search, tagging, import/export
- MemoryManager for top-level orchestration
- WorkingMemory with session-aware context buffer and eviction
- Conversation, knowledge, and project memory stores
- Consolidation, retrieval, importance scoring modules
- Token-budgeted context injection
- Memory types: MemoryEntry, MemoryQuery, MemorySearchResult, MemoryStats
- 25 memory modules total

---

## [0.5.0] — Phase 5: Multi-Agent Framework

### Added

- Multi-Agent Framework with 11 specialized agents
- BaseAgent ABC with lifecycle (initialize, start, stop, health)
- AgentCoordinator for delegation and parallel execution
- AgentRouter with capability-based routing
- AgentExecutor with priority job queue
- AgentLifecycleManager with dependency ordering
- MessageBus for inter-agent communication
- Agents: Coding, Research, Planner, Android, Web, General, Memory, Security, Automation, Voice, Vision
- 29 agent modules total

---

## [0.4.0] — Phase 4: AI Provider Architecture

### Added

- BaseProvider ABC (chat, stream, embeddings, health, list_models)
- Provider configurations for 8 providers
- ProviderRegistry with capability matching
- ProviderFactory and ProviderManager
- HealthMonitor with circuit breaker
- Capability system with scoring
- Provider skeletons for OpenAI, Claude, Gemini, Ollama, Groq, DeepSeek, Qwen, Mistral
- 16 provider modules total

---

## [0.3.0] — Phase 3: AI Kernel

### Added

- AIKernel ABC with process/process_stream
- TaskRouter with priority rules
- SessionManager for lifecycle and history
- ContextManager with token budgeting
- StateManager for status and metrics
- EventBus pub/sub system
- ModelSelector with routing strategies
- PromptManager for templating
- ResponseManager with filtering
- 14 kernel modules total

---

## [0.2.0] — Phase 2: Backend Foundation

### Added

- FastAPI application factory with middleware
- Pydantic-based settings (environment variable loading)
- Structured logging (structlog, JSON)
- Exception hierarchy (AppException → HTTP errors)
- Health check and version endpoints
- CORS, request ID, response timing middleware
- Clean architecture directory structure

---

## [0.1.0] — Phase 1: Architecture & Documentation

### Added

- System architecture documentation (12 documents)
- Project documentation (vision, mission, goals, features, roadmap)
- Technology stack specification
- Repository structure with clean architecture layout

---

## [0.0.1] — Project Initialization

### Added

- GitHub repository created
- Initial README with project vision
- Documentation structure

---

© Sona AI OS
