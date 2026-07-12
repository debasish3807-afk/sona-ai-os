# Sona AI OS

> A Next-Generation Personal AI Operating System

[![CI Pipeline](https://github.com/debasish3807-afk/sona-ai-os/actions/workflows/ci.yml/badge.svg)](https://github.com/debasish3807-afk/sona-ai-os/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

---

## Vision

Sona AI OS is a personal AI operating system that combines the world's best AI models, multi-agent intelligence, long-term memory, automation, research, coding, voice, vision, and secure integrations into one unified platform.

---

## Current Status

| Item | Status |
|------|--------|
| **Version** | `0.7.0` |
| **Phase** | Phase 8 — Cloud AI Providers & Persistent Memory |
| **Backend** | Implemented (120 Python modules) |
| **AI Brain** | Implemented (full execution pipeline) |
| **Ollama Integration** | Implemented (chat, stream, embeddings, health) |
| **CI/CD** | Implemented (lint, type-check, security, test, deploy) |
| **Tests** | 65 passing |
| **Frontend** | Not started |
| **Android** | Not started |

---

## Completed Phases

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | System Architecture | ✅ Complete |
| Phase 2 | Backend Foundation | ✅ Complete |
| Phase 3 | AI Kernel | ✅ Complete |
| Phase 4 | AI Provider Architecture | ✅ Complete |
| Phase 5 | Multi-Agent Framework | ✅ Complete |
| Phase 6 | Memory Engine | ✅ Complete |
| Phase 7 | AI Brain Execution Pipeline | ✅ Complete |
| **Phase 8** | **Cloud AI Providers & Persistent Memory** | **In Progress** |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interfaces                        │
│          (Web / Desktop / Android / Widgets)             │
├─────────────────────────────────────────────────────────┤
│                    API Gateway                            │
│   POST /chat  │  POST /chat/stream  │  GET /models      │
├─────────────────────────────────────────────────────────┤
│                 AI Brain Orchestrator                     │
│   Request → Memory → Agent → Provider → Response        │
├─────────────────────────────────────────────────────────┤
│  AI Kernel  │  Multi-Agent (6)  │  Agent Router         │
├─────────────────────────────────────────────────────────┤
│  LLM Pool (Ollama)  │  Memory Engine  │  Context Mgr    │
├─────────────────────────────────────────────────────────┤
│             Infrastructure & Security                    │
│   CI/CD  │  GitHub Actions  │  Docker (planned)         │
└─────────────────────────────────────────────────────────┘
```

---

## AI Execution Pipeline

```
User Request
    │
    ▼
POST /api/v1/chat
    │
    ▼
Brain Orchestrator
    │
    ├── 1. Memory Retrieval (conversation history)
    ├── 2. Agent Routing (intent detection)
    ├── 3. Context Assembly (system prompt + history + request)
    ├── 4. Model Selection (provider + model)
    ├── 5. LLM Execution (Ollama → llama3)
    ├── 6. Memory Storage (save response)
    │
    ▼
API Response (content + tokens + latency)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat` | Chat completion |
| `POST` | `/api/v1/chat/stream` | Streaming chat (SSE) |
| `GET` | `/api/v1/models` | List available models |
| `GET` | `/api/v1/providers` | List providers with status |
| `GET` | `/api/v1/health/providers` | Provider health check |
| `GET` | `/api/v1/health` | Application health |
| `GET` | `/api/v1/version` | API version info |

---

## Implemented Systems

### AI Brain (`brain/`)
- Central orchestrator connecting all subsystems
- Full execution pipeline: memory → agent → provider → response
- Streaming support via Server-Sent Events
- Token usage tracking per request

### AI Kernel (`kernel/`)
- Intent classification and reasoning chain management
- Context assembly with token budgeting
- Model selection and routing
- Session and state management
- Event-driven architecture (pub/sub)

### Provider Architecture (`providers/`)
- Abstract provider interface (8 providers defined)
- **Ollama** — fully implemented (chat, stream, embeddings, health, model listing)
- OpenAI, Claude, Gemini, Groq, DeepSeek, Qwen, Mistral — architecture ready
- Provider registry, factory, health monitoring
- Capability-based routing and fallback chains

### Multi-Agent Framework (`agents/`)
- 11 specialized agents (coding, research, planner, android, web, voice, vision, etc.)
- Agent lifecycle management (init, start, stop, health)
- Coordinator for multi-agent delegation
- Intent-based routing with pattern matching
- Communication bus and message protocol

### Memory Engine (`memory/`)
- 5 memory types: working, short-term, long-term, episodic, semantic
- Conversation history with session isolation
- Context injection with token budget management
- Memory store interface with CRUD, search, tagging
- Eviction policies and importance scoring

### Configuration & Infrastructure
- Pydantic-based settings with environment variable loading
- Structured logging (structlog, JSON format)
- CI/CD pipeline (GitHub Actions — lint, type-check, security, test, deploy)
- Development deployment (auto on push to main/develop)
- Production deployment (on tagged releases only)

---

## Repository Structure

```
sona-ai-os/
├── backend/            — Python backend (FastAPI, 120 modules)
│   ├── brain/          — AI Brain orchestrator (6 modules)
│   ├── kernel/         — AI Kernel (14 modules)
│   ├── providers/      — LLM providers (16 modules)
│   ├── agents/         — Multi-agent system (29 modules)
│   ├── memory/         — Memory engine (25 modules)
│   ├── api/            — REST API endpoints (5 modules)
│   ├── app/            — Application factory (3 modules)
│   ├── config/         — Configuration (4 modules)
│   ├── core/           — Domain exceptions & constants (5 modules)
│   └── tests/          — Test suite (11 modules, 65 tests)
├── architecture/       — System architecture docs (13 files)
├── docs/               — Project documentation (10 files)
├── frontend/           — Web & desktop apps (planned)
├── android/            — Android companion (planned)
├── .github/workflows/  — CI/CD pipelines (3 workflows)
└── docker/             — Container configs (planned)
```

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python 3.12, FastAPI, Pydantic, structlog |
| AI/LLM | Ollama (local), OpenAI, Anthropic, Google AI (planned) |
| Testing | Pytest, Ruff, Mypy, Bandit |
| CI/CD | GitHub Actions (lint → type-check → security → test → deploy) |
| Infrastructure | Docker (planned), Kubernetes (planned) |

---

## Getting Started

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.ai) installed and running locally
- A model pulled (e.g., `ollama pull llama3`)

### Setup

```bash
git clone https://github.com/debasish3807-afk/sona-ai-os.git
cd sona-ai-os/backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run the application
uvicorn app.main:app --reload --port 8000
```

### Quick Test

```bash
# Chat with Sona
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello, Sona!"}]}'
```

---

## Development

```bash
# Run linter
ruff check .

# Run formatter
ruff format .

# Run type checker
mypy . --ignore-missing-imports

# Run tests
pytest tests/ -v

# Run full CI locally
ruff check . && ruff format --check . && mypy . --ignore-missing-imports && pytest tests/
```

---

## Deployment

| Environment | Trigger | Pipeline |
|-------------|---------|----------|
| Development | Push to `main`/`develop` | CI gate → Build → Deploy → Health check |
| Production | Tag `v*.*.*` | CI gate → Build → Approval → Deploy → Verify → Release |

---

## Documentation

- [Architecture Overview](architecture/README.md)
- [Backend Documentation](backend/README.md)
- [Project Documentation](docs/README.md)
- [Technology Stack](docs/Technology.md)
- [Roadmap](docs/Roadmap.md)
- [Changelog](docs/Changelog.md)

---

## Design Principles

- **Clean Architecture** — Dependency inversion, layer isolation
- **Async-First** — All I/O operations are non-blocking
- **Type-Safe** — Full type annotations, Mypy strict checking
- **AI-Native** — Designed from the ground up for AI workloads
- **Privacy-First** — Local-first with Ollama, user data sovereignty
- **SOLID** — Every module follows single responsibility

---

## Author

**Sona**

---

## License

Coming Soon
