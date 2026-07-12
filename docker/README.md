# Docker

Container configurations for Sona AI OS services.

## Purpose

This directory contains Docker-related files for building, running, and orchestrating the application containers.

## Contents

- **Dockerfiles**: Multi-stage build definitions for each service
- **docker-compose**: Orchestration files for local development and production
- **Configuration**: Container-specific config files and entrypoints

## Quick Start

```bash
# Start all services locally
docker-compose up -d

# Build specific service
docker build -f docker/Dockerfile.backend -t sona-backend .

# View logs
docker-compose logs -f
```

## Environments

| File | Purpose |
|------|---------|
| docker-compose.yml | Local development |
| docker-compose.prod.yml | Production deployment |
| docker-compose.test.yml | Testing environment |

## Best Practices

- Use multi-stage builds to minimize image size
- Pin base image versions for reproducibility
- Never include secrets in images
- Use .dockerignore to exclude unnecessary files
