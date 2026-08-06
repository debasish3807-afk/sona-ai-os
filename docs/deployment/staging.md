# Staging Deployment

This guide covers deploying Sona AI OS to the staging environment. Staging mirrors production as closely as possible while allowing rapid iteration.

## Overview

- **Trigger**: Push to `develop` branch
- **Workflow**: `.github/workflows/deploy-staging.yml`
- **Infrastructure**: Container-based deployment
- **Database**: Separate PostgreSQL instance with staging data
- **URL**: `https://api-staging.sona.ai`

## Deployment Pipeline

```
Push to develop
    │
    ▼
CI Pipeline (ci-monorepo.yml)
    │  - Lint check
    │  - Run tests
    │  - Build validation
    │
    ▼
Deploy Staging (deploy-staging.yml)
    │  1. Build container images
    │  2. Tag with :staging and :<sha>
    │  3. Push to container registry (ghcr.io)
    │  4. Run vulnerability scan (Trivy)
    │  5. Deploy to staging environment
    │
    ▼
Staging Environment Live
```

## Container Images

All services are built and pushed to GitHub Container Registry:

```
ghcr.io/<org>/sona-ai-os/gateway:staging
ghcr.io/<org>/sona-ai-os/web:staging
ghcr.io/<org>/sona-ai-os/ai-kernel:staging
ghcr.io/<org>/sona-ai-os/brain-os:staging
... (all 14 services)
```

Each image is tagged with both `:staging` (latest) and `:<commit-sha>` (for rollback).

## Environment Configuration

Staging uses environment-specific configuration:

| Variable | Staging Value |
|---|---|
| `ENVIRONMENT` | `staging` |
| `LOG_LEVEL` | `info` |
| `DEBUG` | `false` |
| `DATABASE_URL` | (staging DB instance) |
| `REDIS_URL` | (staging Redis instance) |
| `CORS_ORIGINS` | `https://staging.sona.ai` |

Secrets (DB passwords, API keys) are stored in GitHub Actions Secrets and injected at deploy time.

## Manual Deployment

If you need to deploy staging manually:

```bash
# Build and push images
docker compose -f infra/compose/docker-compose.yml build
docker compose -f infra/compose/docker-compose.prod.yml push

# Or deploy specific services
docker compose -f infra/compose/docker-compose.yml build gateway web
```

## Monitoring Staging

- **Logs**: Available through container runtime logs
- **Health**: `GET https://api-staging.sona.ai/health`
- **Metrics**: Prometheus endpoint at `/metrics` (internal only)

## Rollback

To rollback to a previous staging deployment:

```bash
# Find the previous commit SHA
git log --oneline -5

# Re-tag images with the desired SHA
# Then trigger redeployment
```

## Differences from Production

| Aspect | Staging | Production |
|---|---|---|
| Database | Shared, may be reset | Dedicated, persistent |
| Scale | Single instance per service | Multiple replicas (HPA) |
| LLM providers | Ollama (local) + OpenAI | Full provider pool |
| Rate limits | Relaxed | Enforced |
| Data | Synthetic/test data | Real user data |
| Monitoring | Basic logging | Full observability stack |

## Testing Against Staging

```bash
# Quick health check
curl https://api-staging.sona.ai/health

# Test chat endpoint
curl -X POST https://api-staging.sona.ai/api/v1/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```
