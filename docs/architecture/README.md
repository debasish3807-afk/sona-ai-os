# Architecture Overview

Sona AI OS is structured as a production-grade monorepo following **Clean Architecture** and **Domain-Driven Design** principles. Each service is independently deployable with clearly defined boundaries, ports (interfaces), and adapters.

## Directory Layout

```
sona-ai-os/
├── services/           14 independently-deployable AI services
├── libs/               3 shared libraries (shared-kernel, llm-client, event-bus)
├── gateway/            API Gateway (FastAPI, auth, rate-limiting, routing)
├── apps/               Client applications
│   ├── web/            React + TypeScript dashboard
│   └── android/        Kotlin + Jetpack Compose mobile app
├── infra/              Docker, Nginx, Kubernetes, scripts
└── docs/               This documentation
```

## Architecture Documents

| Document | Description |
|---|---|
| [System Overview](./system-overview.md) | High-level architecture diagram and service context |
| [Module Boundaries](./module-boundaries.md) | The 14 service boundaries, responsibilities, and inter-service contracts |
| [Data Flow](./data-flow.md) | How data flows between services for key user scenarios |

## Core Principles

1. **Clean Architecture** — Domain → Application → Infrastructure layering; no inward dependencies
2. **Ports & Adapters** — All external integrations are behind abstract port interfaces
3. **Domain Events** — Services communicate via typed domain events (not direct calls)
4. **Result Pattern** — Errors are represented as `Result[T, E]` values, not exceptions
5. **Shared Kernel** — Common primitives (EntityId, Timestamp, DomainEvent) live in `libs/shared-kernel`

## Service Categories

### Orchestration Layer
- `services/brain-os` — Central pipeline orchestrator
- `services/thalamus-router` — Intent classification and routing
- `services/workflow-engine` — Multi-step task automation

### Intelligence Layer
- `services/ai-kernel` — Model selection and reasoning
- `services/memory-os` — Working, short-term, long-term, episodic, semantic memory
- `services/knowledge-os` — RAG pipeline and document knowledge bases
- `services/research-os` — Web research and synthesis
- `services/ai-engineering-os` — Code generation and review

### Agent & Integration Layer
- `services/workforce-os` — Multi-agent coordination
- `services/mcp-integration` — Model Context Protocol tool connections
- `services/plugin-system` — Third-party plugin extensibility

### Cross-Cutting Concerns
- `services/security` — Authentication, RBAC, AI safety guardrails
- `services/observability` — Metrics, tracing, structured logging
- `services/evaluation-os` — Quality evaluation and regression testing

## See Also

- [Getting Started Guide](../development/getting-started.md)
- [API Gateway Documentation](../api/gateway.md)
- [Deployment Guide](../deployment/local.md)
