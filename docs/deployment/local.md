# Local Development Deployment

This guide covers running the full Sona AI OS stack on your local machine using Docker Compose.

## Prerequisites

- Docker 25+
- Docker Compose 2.24+
- At least 4GB free RAM (8GB recommended)
- Ports: 3000, 5432, 6333, 6379, 8000, 80 available

## Quick Start

```bash
# Start everything
make up

# Or manually:
docker compose -f infra/compose/docker-compose.yml up -d
```

## Architecture (Local)

```
┌─────────────────────────────────────────────────┐
│  Nginx (port 80)                                │
│    /        → Web Dashboard (port 3000)         │
│    /api/*   → API Gateway (port 8000)           │
└─────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌──────────────┐    ┌─────────────────┐
│  Web (React) │    │  Gateway (FastAPI)│
│  port 3000   │    │  port 8000       │
└──────────────┘    └─────────────────┘
                              │
         ┌────────────────────┼────────────────┐
         ▼                    ▼                ▼
┌──────────────┐    ┌──────────────┐   ┌──────────────┐
│ PostgreSQL 16│    │   Redis 7    │   │   Qdrant     │
│ port 5432    │    │  port 6379   │   │  port 6333   │
└──────────────┘    └──────────────┘   └──────────────┘
```

## Services

| Service | Port | Health Check | Purpose |
|---|---|---|---|
| nginx | 80, 443 | — | Reverse proxy |
| web | 3000 | — | React dashboard |
| gateway | 8000 | `GET /health` | API Gateway |
| postgres | 5432 | `pg_isready` | Primary database |
| redis | 6379 | `redis-cli ping` | Cache, sessions |
| qdrant | 6333 | HTTP 200 | Vector database |

## Configuration

### Environment Variables

Create a `.env` file at the project root (or run `make setup` to generate one):

```env
# Database
POSTGRES_USER=sona
POSTGRES_PASSWORD=sona_dev_pass
POSTGRES_DB=sona_db

# Services
ENVIRONMENT=local
LOG_LEVEL=debug

# LLM (optional - for Ollama)
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Development Overrides

For live-reload during development:

```bash
docker compose -f infra/compose/docker-compose.yml \
               -f infra/compose/docker-compose.dev.yml \
               up -d
```

The dev override mounts source code as volumes for hot reloading.

## Common Operations

### View logs

```bash
# All services
make logs

# Specific service
docker compose -f infra/compose/docker-compose.yml logs -f gateway
```

### Restart a service

```bash
docker compose -f infra/compose/docker-compose.yml restart gateway
```

### Reset database

```bash
docker compose -f infra/compose/docker-compose.yml down -v
docker compose -f infra/compose/docker-compose.yml up -d postgres
# Wait for health check, then:
bash infra/scripts/migrate-db.sh
bash infra/scripts/seed-data.sh
```

### Connect to database

```bash
docker compose -f infra/compose/docker-compose.yml exec postgres \
  psql -U sona -d sona_db
```

### Connect to Redis

```bash
docker compose -f infra/compose/docker-compose.yml exec redis redis-cli
```

## Troubleshooting

### Container won't start

```bash
# Check container logs
docker compose -f infra/compose/docker-compose.yml logs <service-name>

# Check health status
docker compose -f infra/compose/docker-compose.yml ps
```

### Port conflict

```bash
# Find what's using the port
lsof -i :8000
# Kill the process or change the port in .env
```

### Out of disk space

```bash
# Clean up Docker
docker system prune -a --volumes
```

### Gateway can't connect to database

Ensure PostgreSQL is healthy before the gateway starts:
```bash
docker compose -f infra/compose/docker-compose.yml up -d postgres
# Wait until healthy
docker compose -f infra/compose/docker-compose.yml up -d gateway
```

## Stopping Everything

```bash
# Stop services (keep data)
make down

# Stop and remove data volumes
docker compose -f infra/compose/docker-compose.yml down -v
```
