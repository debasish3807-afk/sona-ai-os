# Architecture

Complete system architecture documentation for Sona AI OS.

**Implementation Status:** All architecture designs have been implemented in the backend (120 Python modules).

---

## Contents

| Document | Description | Design | Implementation |
|----------|-------------|--------|----------------|
| [System Overview](system-overview.md) | High-level system architecture | ✅ | ✅ |
| [AI Kernel](ai-kernel.md) | Central intelligence engine | ✅ | ✅ 14 modules |
| [Orchestrator](orchestrator.md) | Task coordination layer | ✅ | ✅ Brain orchestrator |
| [Multi-Agent](multi-agent.md) | Multi-agent coordination framework | ✅ | ✅ 29 modules, 11 agents |
| [LLM Pool](llm-pool.md) | LLM provider pooling and routing | ✅ | ✅ 16 modules, Ollama live |
| [Memory](memory.md) | Memory subsystem architecture | ✅ | ✅ 25 modules, 5 types |
| [RAG](rag.md) | Retrieval-Augmented Generation pipeline | ✅ | 🔄 Phase 8 (embeddings) |
| [MCP](mcp.md) | Model Context Protocol integration | ✅ | ⬜ Phase 10 |
| [Automation](automation.md) | Automation engine design | ✅ | ⬜ Future |
| [Security](security.md) | Security architecture and policies | ✅ | 🔄 Partial (CORS, exceptions) |
| [API](api.md) | API layer design and contracts | ✅ | ✅ 7 endpoints live |
| [Deployment](deployment.md) | Deployment architecture and strategies | ✅ | ✅ CI/CD pipelines |

---

## Architecture Principles

| Principle | Status | Evidence |
|-----------|--------|----------|
| **Clean Architecture** | ✅ Enforced | Dependency inversion across all layers |
| **Event-Driven** | ✅ Implemented | EventBus in kernel, agent communication bus |
| **Plugin-Based** | ✅ Implemented | Provider registry, agent registry, factory pattern |
| **AI-Native** | ✅ Implemented | Brain orchestrator, model selection, token budgeting |
| **Privacy-First** | ✅ Implemented | Ollama local-first, session isolation |
| **SOLID** | ✅ Enforced | ABCs, single-responsibility modules, DI |
| **Async-First** | ✅ Enforced | All I/O operations non-blocking |
| **Type-Safe** | ✅ Enforced | Full annotations, Mypy strict (0 errors) |

---

## Implemented Architecture

### Execution Pipeline (Live)

```
User Request
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  API Gateway (api/)                                      │
│  POST /chat  │  POST /chat/stream  │  GET /models       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  AI Brain Orchestrator (brain/orchestrator.py)           │
│                                                          │
│  1. Memory Retrieval ──► Conversation history            │
│  2. Agent Routing ────► Intent detection (6 categories)  │
│  3. Context Assembly ─► System prompt + history + user   │
│  4. Model Selection ──► Provider + model                 │
│  5. LLM Execution ───► Ollama /api/chat                  │
│  6. Memory Storage ──► Save response to session          │
│                                                          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Response (JSON or SSE stream)                           │
│  content + model + agent + token_usage + latency         │
└─────────────────────────────────────────────────────────┘
```

### Dependency Direction (Enforced)

```
api/ ──────► brain/ ──────► providers/
                │                 ▲
                │                 │
                ├──► memory/ ─────┘
                │
                └──► agents/

All depend on: core/ (exceptions, constants)
               config/ (settings, logging)
```

### Component Map

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (5 modules)                  │
│   chat.py • health.py • version.py • router.py          │
├─────────────────────────────────────────────────────────┤
│               AI Brain (6 modules)                        │
│   orchestrator • schemas • memory_bridge • agent_router  │
├─────────────────────────────────────────────────────────┤
│  AI Kernel (14)    │  Agents (29)      │  Memory (25)    │
│  kernel • router   │  11 agents        │  5 memory types │
│  session • context │  coordinator      │  consolidation  │
│  state • events    │  router • bus     │  retrieval      │
│  model_selector    │  lifecycle        │  importance     │
├─────────────────────────────────────────────────────────┤
│             Providers (16 modules)                        │
│  Ollama (live) • OpenAI • Claude • Gemini • Groq        │
│  DeepSeek • Qwen • Mistral • registry • factory         │
├─────────────────────────────────────────────────────────┤
│  Core (5)          │  Config (4)       │  App (3)        │
│  exceptions        │  settings         │  main (factory) │
│  constants         │  logging          │  lifespan       │
└─────────────────────────────────────────────────────────┘
```

---

## Layer Boundaries

| Layer | Package | Modules | Depends On |
|-------|---------|---------|-----------|
| Presentation | `api/` | 5 | brain, core, config |
| Orchestration | `brain/` | 6 | providers, memory, agents, core, config |
| Domain | `kernel/` | 14 | core |
| Domain | `agents/` | 29 | core, providers (interfaces) |
| Domain | `memory/` | 25 | core |
| Infrastructure | `providers/` | 16 | core, config |
| Foundation | `core/` | 5 | (none) |
| Foundation | `config/` | 4 | (pydantic-settings) |
| Entry Point | `app/` | 3 | All (composition root) |

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.12 | Type unions, performance, AI ecosystem |
| Framework | FastAPI | Async, type-safe, OpenAPI auto-generation |
| Validation | Pydantic v2 | Fastest Python validator, settings integration |
| Logging | structlog | Structured JSON, async-safe, zero overhead |
| HTTP Client | httpx | Async, HTTP/2, streaming support |
| Linting | Ruff | 100x faster than flake8, replaces isort |
| Type Checking | Mypy | Strict mode, catches errors before runtime |
| Testing | Pytest | Async support, fixtures, coverage |
| CI/CD | GitHub Actions | Native, 3 workflows, environment gates |
| LLM (Local) | Ollama | Privacy-first, no API key, fast local inference |

---

## Version

Architecture Documentation v0.7 — Phase 8

All architecture designs from Phase 1 have been implemented in code (Phases 2–7).
The architecture documents remain as the canonical design reference.

---

© Sona AI OS
