# Backend

The backend service for Sona AI OS — a fully implemented AI execution engine built with Python 3.12 and FastAPI, following clean architecture principles.

**Status:** Implemented (120 Python modules, 65 tests passing)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  API Layer (api/)                                        │
│  POST /chat  │  POST /chat/stream  │  GET /models       │
├─────────────────────────────────────────────────────────┤
│  AI Brain (brain/)                                       │
│  Orchestrator → Memory → Agent → Provider → Response    │
├─────────────────────────────────────────────────────────┤
│  AI Kernel (kernel/)        │  Agent Framework (agents/) │
│  Intent • Routing • State   │  11 agents • Coordinator  │
├─────────────────────────────────────────────────────────┤
│  Providers (providers/)     │  Memory Engine (memory/)   │
│  Ollama • 7 more planned    │  5 types • Session store   │
├─────────────────────────────────────────────────────────┤
│  Core (core/)               │  Config (config/)          │
│  Exceptions • Constants     │  Settings • Logging        │
└─────────────────────────────────────────────────────────┘
```

---

## Implemented Modules

### AI Brain (`brain/`) — 6 modules
The central execution engine connecting all subsystems.

| Module | Purpose |
|--------|---------|
| `orchestrator.py` | Full AI pipeline: request → memory → agent → provider → response |
| `schemas.py` | Pydantic request/response models for the Chat API |
| `memory_bridge.py` | Conversation history retrieval, context injection, storage |
| `agent_router.py` | Intent detection with pattern matching (6 agent categories) |
| `__init__.py` | Package exports |

### AI Kernel (`kernel/`) — 14 modules
Central intelligence engine for reasoning and decision-making.

| Module | Purpose |
|--------|---------|
| `kernel.py` | AIKernel ABC — process, process_stream, initialize, shutdown |
| `router.py` | TaskRouter — routes tasks to handlers with priority rules |
| `session.py` | SessionManager — session lifecycle and message history |
| `context.py` | ContextManager — token-budgeted context window assembly |
| `state.py` | StateManager — kernel status, resource metrics tracking |
| `task_manager.py` | TaskManager — task lifecycle (create, execute, retry, cancel) |
| `events.py` | EventBus — pub/sub event system for kernel events |
| `model_selector.py` | ModelSelector — intelligent model routing with strategies |
| `prompt_manager.py` | PromptManager — prompt templating, rendering, optimization |
| `response_manager.py` | ResponseManager — response filtering and streaming |
| `lifecycle.py` | Lifecycle management hooks |
| `manager.py` | High-level kernel manager |
| `registry.py` | Component registry |
| `__init__.py` | Package exports |

### Provider Architecture (`providers/`) — 16 modules
Multi-provider LLM integration with routing and fallback.

| Module | Purpose |
|--------|---------|
| `base.py` | BaseProvider ABC — chat, stream, embeddings, health, list_models |
| `ollama_provider.py` | **Ollama — fully implemented** (chat, stream, embed, health) |
| `openai_provider.py` | OpenAI architecture (implementation Phase 8) |
| `claude_provider.py` | Anthropic Claude architecture |
| `gemini_provider.py` | Google Gemini architecture |
| `groq_provider.py` | Groq architecture |
| `deepseek_provider.py` | DeepSeek architecture |
| `qwen_provider.py` | Alibaba Qwen architecture |
| `mistral_provider.py` | Mistral AI architecture |
| `manager.py` | ProviderManager — orchestrates selection, fallback, health |
| `registry.py` | ProviderRegistry — register/lookup with capability matching |
| `factory.py` | ProviderFactory — creates instances from config |
| `health.py` | HealthMonitor — circuit breaker, health state tracking |
| `capabilities.py` | Capability enum, matching, and scoring |
| `config.py` | Per-provider configuration classes |
| `types.py` | ChatRequest, ChatResponse, StreamChunk, TokenUsage, ModelInfo |

### Multi-Agent Framework (`agents/`) — 29 modules
Specialized AI agents with lifecycle management and coordination.

| Module | Purpose |
|--------|---------|
| `base.py` | BaseAgent ABC — execute, health, capabilities |
| `coordinator.py` | AgentCoordinator — delegation, parallel/pipeline execution |
| `manager.py` | AgentManager — lifecycle orchestration |
| `router.py` | AgentRouter — capability-based task routing |
| `registry.py` | AgentRegistry — registration and lookup |
| `factory.py` | AgentFactory — agent instantiation |
| `executor.py` | AgentExecutor — job queue with priority |
| `lifecycle.py` | AgentLifecycleManager — dependency-ordered startup/shutdown |
| `communication.py` | MessageBus — inter-agent messaging |
| `capabilities.py` | AgentCapability enum and matching |
| `context.py` | ExecutionContext and ExecutionResult types |
| `state.py` | AgentState, AgentStatus, AgentHealth tracking |
| `events.py` | Agent event definitions |
| `exceptions.py` | Agent-specific exception hierarchy |
| `planner.py` | TaskPlanner — execution plan building |
| `workflow.py` | Workflow orchestration |
| `verifier.py` | Result verification |
| `coding_agent.py` | Code generation, review, debugging |
| `research_agent.py` | Web research, summarization, analysis |
| `planner_agent.py` | Project planning, task breakdown |
| `android_agent.py` | Android/Kotlin development |
| `web_agent.py` | Frontend/web development |
| `general_agent.py` | General-purpose assistant |
| `memory_agent.py` | Memory operations |
| `security_agent.py` | Security analysis |
| `automation_agent.py` | Workflow automation |
| `voice_agent.py` | Voice interaction |
| `vision_agent.py` | Image analysis |
| `__init__.py` | Package exports (60+ symbols) |

### Memory Engine (`memory/`) — 25 modules
Persistent and ephemeral memory with session isolation.

| Module | Purpose |
|--------|---------|
| `base.py` | MemoryStore ABC — CRUD, search, tagging, import/export |
| `manager.py` | MemoryManager — top-level orchestration |
| `working.py` | WorkingMemory — session-aware context buffer |
| `short_term.py` | Short-term memory (hours/days) |
| `long_term.py` | Long-term memory (permanent) |
| `episodic.py` | Episodic memory (events) |
| `semantic.py` | Semantic memory (knowledge graph) |
| `conversation.py` | Conversation history store |
| `knowledge.py` | Knowledge base management |
| `project.py` | Project-scoped memory |
| `types.py` | MemoryEntry, MemoryQuery, MemorySearchResult, enums |
| `consolidation.py` | Memory merging and summarization |
| `retrieval.py` | Retrieval strategies |
| `importance.py` | Importance scoring |
| `index.py` | Search indexing |
| `metrics.py` | Memory system metrics |
| `policies.py` | Eviction and retention policies |
| `summarizer.py` | Content summarization |
| `factory.py` | Memory store factory |
| `registry.py` | Store registry |
| `context.py` | Context assembly |
| `session.py` | Session memory management |
| `state.py` | Memory state tracking |
| `events.py` | Memory event definitions |
| `exceptions.py` | Memory-specific exceptions |

### API Layer (`api/`) — 5 modules

| Module | Purpose |
|--------|---------|
| `chat.py` | Chat endpoints — POST /chat, POST /chat/stream, GET /models, GET /providers, GET /health/providers |
| `health.py` | GET /health — application health check |
| `version.py` | GET /version — API version information |
| `router.py` | Router factory — assembles all sub-routers |
| `__init__.py` | Package init |

### Application (`app/`) — 3 modules

| Module | Purpose |
|--------|---------|
| `main.py` | FastAPI application factory with middleware |
| `lifespan.py` | Startup/shutdown lifecycle (Brain init/shutdown) |
| `__init__.py` | Package init |

### Configuration (`config/`) — 4 modules

| Module | Purpose |
|--------|---------|
| `settings.py` | Pydantic-settings with env loading |
| `config.py` | Configuration helpers |
| `logging.py` | Structured logging setup (structlog) |
| `__init__.py` | Package init |

### Core (`core/`) — 5 modules

| Module | Purpose |
|--------|---------|
| `exceptions.py` | AppException hierarchy + FastAPI exception handlers |
| `constants.py` | Header names, version constants |
| `responses.py` | Standard response wrappers |
| `dependencies.py` | FastAPI dependency injection |
| `__init__.py` | Package init |

---

## API Documentation

### Chat Completion

```http
POST /api/v1/chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "Write a Python function to sort a list"}
  ],
  "model": "llama3",
  "temperature": 0.7,
  "max_tokens": 4096,
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "success": true,
  "response_id": "uuid",
  "content": "Here's a Python function...",
  "model": "llama3",
  "provider": "ollama",
  "agent": "coding",
  "finish_reason": "stop",
  "token_usage": {
    "prompt_tokens": 42,
    "completion_tokens": 156,
    "total_tokens": 198
  },
  "latency_ms": 1234.5
}
```

### Streaming Chat (SSE)

```http
POST /api/v1/chat/stream
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "Hello"}]
}
```

**Response:** `text/event-stream`
```
data: {"event": "start", "model": "llama3"}

data: {"event": "delta", "content": "Hello", "model": "llama3"}

data: {"event": "delta", "content": "!", "model": "llama3"}

data: {"event": "done", "model": "llama3", "finish_reason": "stop", "token_usage": {...}}

data: [DONE]
```

### List Models

```http
GET /api/v1/models
```

```json
{
  "success": true,
  "models": [
    {
      "model_id": "llama3:latest",
      "name": "llama3:latest",
      "provider": "ollama",
      "model_type": "chat",
      "supports_streaming": true
    }
  ],
  "total": 1
}
```

### Provider Health

```http
GET /api/v1/health/providers
```

```json
{
  "success": true,
  "providers": [
    {
      "provider_id": "ollama",
      "name": "Ollama (Local)",
      "healthy": true,
      "latency_ms": 5.2
    }
  ]
}
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.ai) running locally (`ollama serve`)
- A model pulled: `ollama pull llama3`

### Installation

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt

# Install dev dependencies (testing, linting)
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
```

### Running

```bash
# Development server (auto-reload)
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Run linter
ruff check .

# Run type checker
mypy . --ignore-missing-imports

# Run security scan
bandit -r . -x ./tests -ll -ii
```

---

## Configuration

Environment variables (see [`.env.example`](.env.example)):

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Sona AI OS | Application name |
| `APP_ENV` | development | Environment (development/staging/production) |
| `APP_PORT` | 8000 | Server port |
| `LOG_LEVEL` | INFO | Log level |
| `OLLAMA_API_KEY` | (none) | Ollama API key (not required for local) |
| `OPENAI_API_KEY` | — | OpenAI API key (Phase 8) |
| `ANTHROPIC_API_KEY` | — | Anthropic API key (Phase 8) |

---

## Project Metrics

| Metric | Value |
|--------|-------|
| Python source files | 109 |
| Test files | 11 |
| Total modules | 120 |
| Test cases | 65 |
| Lines of Python | ~14,000 |
| Ruff lint errors | 0 |
| Mypy type errors | 0 |
| Bandit security issues | 0 |

---

## CI/CD Pipeline

```
Push/PR → Lint (Ruff) → Type Check (Mypy) → Security (Bandit)
    → Test (Pytest) → Architecture Validation → Deploy
```

| Workflow | Trigger | Action |
|----------|---------|--------|
| `ci.yml` | PR / push to main | Full validation gate |
| `deploy-dev.yml` | Push to main/develop | Auto-deploy development |
| `deploy-prod.yml` | Tag v*.*.* | Production release |
