# Getting Started

This guide walks you through setting up the Sona AI OS development environment from scratch.

## Prerequisites

Before you begin, ensure you have the following installed:

| Tool | Minimum Version | Install Guide |
|---|---|---|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 20 LTS+ | [nodejs.org](https://nodejs.org/) |
| Docker | 25+ | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Docker Compose | 2.24+ | Included with Docker Desktop |
| Git | 2.40+ | [git-scm.com](https://git-scm.com/) |

**Optional** (for Android development):
- Android Studio Hedgehog (2023.1.1) or newer
- JDK 17 (Temurin recommended)

## Quick Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/sona-ai-os.git
cd sona-ai-os
```

### 2. Run automated setup

```bash
make setup
```

This script will:
- Verify Python 3.12+, Node.js 20+, and Docker are installed
- Create a `.env` file from the example template
- Install all shared libraries (`shared-kernel`, `llm-client`, `event-bus`)
- Install the API Gateway
- Install all 14 backend services
- Install web frontend Node.js dependencies
- Start the infrastructure containers (PostgreSQL, Redis, Qdrant)

### 3. Start the API Gateway

```bash
cd gateway
uvicorn app.main:app --reload --port 8000
```

### 4. Start the Web Frontend

```bash
cd apps/web
npm run dev
```

The web app is available at `http://localhost:3000`.

---

## Manual Setup (Step by Step)

If you prefer to set up components individually:

### Step 1: Install shared libraries

```bash
pip install -e libs/shared-kernel[dev]
pip install -e libs/llm-client[dev]
pip install -e libs/event-bus[dev]
```

### Step 2: Install services

```bash
for service in services/*/; do
  pip install -e "$service[dev]"
done
```

### Step 3: Install the gateway

```bash
pip install -e gateway[dev]
```

### Step 4: Configure environment

```bash
cp backend/.env.example .env
# Edit .env with your local settings
```

### Step 5: Start infrastructure

```bash
docker compose -f infra/compose/docker-compose.yml up -d postgres redis qdrant
```

### Step 6: Start the gateway

```bash
cd gateway && uvicorn app.main:app --reload
```

---

## Project Structure at a Glance

```
sona-ai-os/
├── services/           14 AI services (ai-kernel, brain-os, memory-os, ...)
├── libs/               Shared libraries (shared-kernel, llm-client, event-bus)
├── gateway/            API Gateway (FastAPI)
├── apps/
│   ├── web/            React + TypeScript dashboard
│   └── android/        Kotlin + Compose app
├── infra/              Docker, Nginx, scripts
├── docs/               This documentation
└── Makefile            Common development commands
```

## Running Tests

```bash
# Run all tests
make test

# Run Python tests only
pytest --cov -v

# Run a specific service's tests
pytest services/ai-kernel/tests/ -v

# Run frontend tests
cd apps/web && npm run test:run
```

## Common Make Commands

```bash
make help       # List all available commands
make setup      # Set up the full dev environment
make lint       # Lint all code
make format     # Auto-format Python code
make test       # Run all tests
make build      # Build all Docker images
make up         # Start all services
make down       # Stop all services
make logs       # Tail Docker logs
make clean      # Remove build artifacts and caches
```

## Troubleshooting

### Port already in use

```bash
# Check what's using port 8000
lsof -i :8000

# Or start the gateway on a different port
uvicorn app.main:app --port 8001 --reload
```

### Database connection issues

```bash
# Verify PostgreSQL is running
docker compose -f infra/compose/docker-compose.yml ps

# Restart infrastructure services
docker compose -f infra/compose/docker-compose.yml restart postgres
```

### Python import errors

```bash
# Re-install shared libraries with dev extras
pip install -e libs/shared-kernel[dev] --force-reinstall
```

## Next Steps

- Read the [Contributing Guide](./contributing.md) before opening a PR
- Review the [Architecture Overview](../architecture/README.md) to understand the system design
- Check the [API Gateway Documentation](../api/gateway.md) for endpoint references
