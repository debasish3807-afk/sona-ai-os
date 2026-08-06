# Production Deployment

This guide covers deploying Sona AI OS to production. Production deployments prioritize stability, security, and observability.

## Overview

- **Trigger**: Push to `main` branch (after PR merge from `develop`)
- **Workflow**: `.github/workflows/deploy-prod.yml`
- **Infrastructure**: Container orchestration (Docker Compose initially, Kubernetes planned)
- **URL**: `https://api.sona.ai`

## Deployment Pipeline

```
PR merged to main
    │
    ▼
CI Pipeline (all checks pass)
    │  - Backend lint + test
    │  - Frontend lint + test + build
    │  - Security scan
    │
    ▼
Deploy Production (deploy-prod.yml)
    │  1. Build container images (multi-stage, optimized)
    │  2. Tag with :production and :<version>
    │  3. Push to container registry
    │  4. Vulnerability scan (must pass: no CRITICAL)
    │  5. Rolling deployment (zero downtime)
    │  6. Post-deploy health verification
    │
    ▼
Production Live (with health monitoring)
```

## Production Architecture

```
                     ┌───────────────────┐
                     │   Load Balancer    │
                     │   (HTTPS / TLS)    │
                     └────────┬──────────┘
                              │
                     ┌────────▼──────────┐
                     │      Nginx        │
                     │  (Reverse Proxy)  │
                     └────────┬──────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Gateway (x3) │  │   Web (x2)   │  │  Services    │
    │  (FastAPI)   │  │  (Nginx+SPA) │  │  (x1-3 each) │
    └──────┬───────┘  └──────────────┘  └──────┬───────┘
           │                                     │
    ┌──────┴────────────────────────────────────┴──────┐
    │                Infrastructure                      │
    │  PostgreSQL 16 (primary + read replica)           │
    │  Redis 7 (cluster mode, 3 nodes)                 │
    │  Qdrant (persistent, replicated)                 │
    └──────────────────────────────────────────────────┘
```

## Container Security

All production containers adhere to:

- **Non-root execution** (UID 1000)
- **Read-only filesystem** where possible
- **No privileged mode**
- **Minimal base images** (slim/alpine variants)
- **Vulnerability-free** (no CRITICAL CVEs allowed to deploy)

## Resource Limits

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---|---|---|---|---|
| Gateway | 250m | 2000m | 256Mi | 2Gi |
| AI Service | 500m | 2000m | 512Mi | 2Gi |
| PostgreSQL | 500m | 4000m | 1Gi | 4Gi |
| Redis | 100m | 1000m | 256Mi | 512Mi |
| Qdrant | 250m | 2000m | 512Mi | 2Gi |
| Web | 100m | 500m | 128Mi | 256Mi |

## Environment Configuration

Production environment variables are managed through secrets:

| Variable | Source |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | GitHub Secrets / Vault |
| `REDIS_URL` | GitHub Secrets / Vault |
| `JWT_SECRET` | GitHub Secrets / Vault |
| `OPENAI_API_KEY` | GitHub Secrets / Vault |
| `ANTHROPIC_API_KEY` | GitHub Secrets / Vault |
| `LOG_LEVEL` | `info` |
| `DEBUG` | `false` |

## Health Checks

Production health checks run continuously:

| Service | Endpoint | Interval | Timeout | Failure Threshold |
|---|---|---|---|---|
| Gateway | `GET /health` | 10s | 5s | 3 |
| PostgreSQL | `pg_isready` | 5s | 3s | 5 |
| Redis | `redis-cli ping` | 5s | 3s | 5 |
| Qdrant | `GET /` | 10s | 5s | 3 |

## Rollback Procedure

If a production deployment causes issues:

1. **Automatic**: If health checks fail within 5 minutes, automatic rollback to previous version
2. **Manual**: Re-deploy the previous container image tag

```bash
# Find previous version
git log --oneline --tags -5

# Trigger manual deploy with specific tag
# (via workflow_dispatch with version input)
```

## Monitoring & Alerting

| Signal | Tool | Alert Threshold |
|---|---|---|
| Error rate | Prometheus + Alertmanager | > 1% of requests |
| Latency P95 | Prometheus | > 3000ms |
| CPU usage | Container metrics | > 80% for 5min |
| Memory usage | Container metrics | > 90% |
| Disk usage | Host metrics | > 85% |
| Health check | HTTP probe | 3 consecutive failures |

## Backup & Recovery

| Data | Backup Frequency | Retention | Recovery Time |
|---|---|---|---|
| PostgreSQL | Hourly snapshots | 30 days | < 30 min |
| Redis (AOF) | Continuous | 7 days | < 5 min |
| Qdrant | Daily snapshot | 14 days | < 60 min |
| Configuration | Git (versioned) | Unlimited | Instant |

## Future: Kubernetes Migration

The current Docker Compose production setup will migrate to Kubernetes:

- Helm charts for each service
- Horizontal Pod Autoscaler (HPA)
- Ingress controller (NGINX or Istio)
- Service mesh for mTLS between services
- ConfigMaps and Secrets for configuration

The `infra/k8s/` directory contains placeholder manifests for this future migration.
