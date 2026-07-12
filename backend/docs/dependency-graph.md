# Dependency Graph

**Project:** Sona AI OS
**Version:** 0.2-alpha
**Date:** 2026-07-12

---

## System-Level Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                           │
│              Web    Desktop    Android    Widgets                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (api/)                          │
│              REST    WebSocket    SSE    GraphQL                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER (services/)                      │
│           Use Cases    Orchestration    Validation               │
└──────┬──────────────────────┬───────────────────┬───────────────┘
       │                      │                   │
       ▼                      ▼                   ▼
┌─────────────┐    ┌──────────────────┐    ┌──────────────┐
│  AI Kernel  │    │   Orchestrator   │    │  Automation  │
│  (core/)    │    │   (services/)    │    │(automation/) │
└──────┬──────┘    └────────┬─────────┘    └──────┬───────┘
       │                    │                      │
       ▼                    ▼                      │
┌─────────────┐    ┌──────────────────┐           │
│  LLM Pool   │    │  Multi-Agent     │           │
│(providers/) │◄───│  (agents/)       │◄──────────┘
└──────┬──────┘    └────────┬─────────┘
       │                    │
       ▼                    ▼
┌─────────────┐    ┌──────────────────┐
│   Memory    │    │      RAG         │
│  (memory/)  │◄───│   (services/)    │
└──────┬──────┘    └──────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE                                  │
│     Database    Redis    Vector DB    External APIs    MCP       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Package Dependency Direction

```
api/  ──────►  services/  ──────►  core/  ◄──────  providers/
                   │                  ▲                   │
                   │                  │                   │
                   └──────────────────┼───────────────────┘
                                      │
                              database/ ────────┘
```

**Rule:** All dependencies point inward toward `core/`. Infrastructure layers implement interfaces defined in `core/`.

---

## Module Dependencies (Planned)

| Module | Depends On | Depended By |
|--------|-----------|-------------|
| `core/` | None (pure domain) | All other modules |
| `services/` | `core/` | `api/` |
| `api/` | `services/`, `core/` | None (entry point) |
| `providers/` | `core/` (interfaces) | `services/` (via DI) |
| `database/` | `core/` (interfaces) | `services/` (via DI) |
| `agents/` | `core/`, `providers/` | `services/` |
| `memory/` | `core/`, `database/` | `services/`, `agents/` |
| `automation/` | `core/`, `services/` | `api/` |
| `tools/` | `core/` | `agents/`, `services/` |
| `models/` | None (data schemas) | All modules |
| `config/` | None (settings) | `app/` |
| `app/` | All modules | None (composition root) |

---

## External Dependencies (from requirements.txt)

```
┌─────────────────────────────────────────────┐
│              APPLICATION                     │
├─────────────────────────────────────────────┤
│  FastAPI ──► Uvicorn (ASGI Server)          │
│  Pydantic (Validation)                       │
│  python-dotenv (Configuration)               │
├─────────────────────────────────────────────┤
│              AI / LLM                        │
│  openai ──► OpenAI API                      │
│  anthropic ──► Anthropic API                │
│  google-generativeai ──► Google AI API      │
├─────────────────────────────────────────────┤
│              DATA                            │
│  SQLAlchemy ──► asyncpg ──► PostgreSQL      │
│  redis ──► Redis Server                     │
│  chromadb ──► Vector Storage                │
├─────────────────────────────────────────────┤
│              SECURITY                        │
│  python-jose (JWT)                           │
│  passlib (Password Hashing)                  │
├─────────────────────────────────────────────┤
│              UTILITIES                       │
│  httpx (HTTP Client)                         │
│  structlog (Logging)                         │
│  tenacity (Retry Logic)                      │
└─────────────────────────────────────────────┘
```

---

## Circular Dependency Risk Assessment

| Risk | Status | Mitigation |
|------|--------|-----------|
| agents/ ↔ services/ | Medium | Use dependency injection; agents accessed via interface |
| memory/ ↔ agents/ | Low | Memory is a service dependency, not a peer |
| providers/ ↔ core/ | None | One-way dependency (providers → core interfaces) |
| api/ ↔ services/ | None | One-way dependency (api → services) |

---

## Recommendations

1. Enforce dependency rules via import linting (e.g., `import-linter` package)
2. Use `__init__.py` with explicit `__all__` to control public API surface
3. Implement dependency injection container in `app/` (composition root)
4. Never import from outer layers into inner layers
5. Use Protocol classes in `core/` for infrastructure contracts
