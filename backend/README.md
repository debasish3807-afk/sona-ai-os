# Backend

The backend service for Sona AI OS, built with Python using clean architecture principles.

## Structure

```
backend/
├── app/             — Application entry point and initialization
├── config/          — Configuration management and environment settings
├── core/            — Core business logic and domain entities
├── api/             — REST API routes and controllers
├── services/        — Application services and use cases
├── agents/          — AI agent implementations
├── memory/          — Memory management subsystem
├── providers/       — External service providers (LLM, APIs)
├── models/          — Data models and schemas
├── database/        — Database connections, migrations, repositories
├── automation/      — Workflow automation engine
├── tools/           — MCP tools and utility functions
├── tests/           — Test suites (unit, integration, e2e)
├── .env.example     — Environment variable template
└── requirements.txt — Python dependencies
```

## Architecture

This backend follows **Clean Architecture** principles:

```
┌─────────────────────────────────────────────┐
│  API Layer (api/)                            │
│  - HTTP routes, request/response handling    │
├─────────────────────────────────────────────┤
│  Service Layer (services/)                   │
│  - Application use cases, orchestration      │
├─────────────────────────────────────────────┤
│  Domain Layer (core/)                        │
│  - Entities, value objects, domain rules     │
│  - NO external dependencies                  │
├─────────────────────────────────────────────┤
│  Infrastructure (providers/, database/)      │
│  - External service implementations         │
│  - Database repositories                     │
└─────────────────────────────────────────────┘
```

### Layer Rules

| Layer | Depends On | Purpose |
|-------|-----------|---------|
| `api/` | `services/`, `core/` | Interface adapters |
| `services/` | `core/` | Application logic |
| `core/` | Nothing | Domain entities and rules |
| `providers/` | `core/` (interfaces) | External integrations |
| `database/` | `core/` (interfaces) | Data persistence |

## Getting Started

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the application
python -m app.main
```

## Configuration

Environment-based configuration is managed through the `config/` directory. See [`.env.example`](.env.example) for all available settings.

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Status

**Pre-implementation** — Directory structure and architecture are defined. Code implementation begins in the next phase.
