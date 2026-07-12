# Backend

The backend service for Sona AI OS, built with Python using clean architecture principles.

## Structure

```
backend/
├── app/           — Application entry point and initialization
├── config/        — Configuration management and environment settings
├── core/          — Core business logic and domain entities
├── api/           — REST API routes and controllers
├── services/      — Application services and use cases
├── agents/        — AI agent implementations
├── memory/        — Memory management subsystem
├── providers/     — External service providers (LLM, APIs)
├── models/        — Data models and schemas
├── database/      — Database connections, migrations, repositories
├── automation/    — Workflow automation engine
├── tools/         — MCP tools and utility functions
├── tests/         — Test suites (unit, integration, e2e)
└── requirements.txt
```

## Architecture

This backend follows **Clean Architecture** principles:

- **Core**: Domain entities and business rules (no external dependencies)
- **Services**: Application use cases coordinating domain logic
- **API**: Interface adapters translating HTTP to service calls
- **Providers**: Infrastructure implementations for external services

## Getting Started

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m app.main
```

## Configuration

Environment-based configuration is managed through the `config/` directory. See `.env.example` for available settings.
