# Sona AI OS — Deployment Runbook

## 1. Server Prerequisites

- Ubuntu 22.04+ (or Docker host)
- 4+ CPU cores, 8GB+ RAM
- Python 3.12+
- Docker & Docker Compose (for Redis, Qdrant, Ollama)
- Ports: 8000 (API), 6379 (Redis), 6333 (Qdrant), 11434 (Ollama)

## 2. Environment Configuration

```bash
# Required secrets (NEVER commit these)
export SONA_JWT_SECRET="<generate-with: openssl rand -hex 32>"
export SONA_DEPENDENCY_MODE=production
export SONA_MCP_DEMO_TOOLS_ENABLED=false

# Infrastructure
export REDIS_URL=redis://localhost:6379/0
export QDRANT_URL=http://localhost:6333
export OLLAMA_URL=http://localhost:11434

# Optional: External LLM providers
# export OPENAI_API_KEY="sk-..."
# export ANTHROPIC_API_KEY="sk-ant-..."
```

## 3. Infrastructure Setup

```bash
# Redis
docker run -d --name sona-redis -p 6379:6379 redis:7-alpine \
  redis-server --appendonly yes --requirepass "${REDIS_PASSWORD}"

# Qdrant
docker run -d --name sona-qdrant -p 6333:6333 -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage qdrant/qdrant:v1.9.0

# Ollama (for local LLM)
docker run -d --name sona-ollama -p 11434:11434 \
  -v ollama:/root/.ollama ollama/ollama:latest
# Pull model: docker exec sona-ollama ollama pull llama3.2
```

## 4. Backend Startup

```bash
cd /opt/sona-ai-os
pip install -e libs/shared-kernel/
for svc in services/*/; do pip install --no-deps -e "$svc"; done
pip install -e gateway/

# Start gateway
uvicorn gateway.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 5. Health Verification

```bash
curl http://localhost:8000/health        # Should return 200
curl http://localhost:8000/ready         # Should return 200 (503 if deps unavailable)
curl http://localhost:8000/health/detailed  # Full dependency status
```

## 6. Authentication Test

```bash
# Should return 401 (no token)
curl -X GET http://localhost:8000/v1/models

# Generate token (via security service or admin endpoint)
TOKEN=$(python -c "
from sona_security.infrastructure.jwt_service import JWTConfig, JWTService
import os
svc = JWTService(JWTConfig(secret=os.environ['SONA_JWT_SECRET']))
print(svc.generate_access_token('admin', ['admin']))
")

# Should return 200
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/models
```

## 7. Backup & Restore

### Redis
```bash
# Backup
docker exec sona-redis redis-cli BGSAVE
docker cp sona-redis:/data/dump.rdb ./backups/redis-$(date +%Y%m%d).rdb

# Restore
docker cp ./backups/redis-latest.rdb sona-redis:/data/dump.rdb
docker restart sona-redis
```

### Qdrant
```bash
# Backup (snapshot)
curl -X POST http://localhost:6333/collections/sona_memories/snapshots

# Restore
curl -X PUT http://localhost:6333/collections/sona_memories/snapshots/recover \
  -H "Content-Type: application/json" \
  -d '{"location": "/path/to/snapshot"}'
```

## 8. Emergency Shutdown

```bash
# Graceful
kill -SIGTERM $(pgrep -f "uvicorn.*gateway")

# Force (data loss possible)
kill -9 $(pgrep -f "uvicorn.*gateway")
docker stop sona-redis sona-qdrant sona-ollama
```

## 9. Update Procedure

```bash
cd /opt/sona-ai-os
git pull origin release/v0.2.0-beta
pip install --no-deps -e libs/shared-kernel/
for svc in services/*/; do pip install --no-deps -e "$svc"; done
pip install --no-deps -e gateway/

# Rolling restart
kill -SIGTERM $(pgrep -f "uvicorn.*gateway")
sleep 5
uvicorn gateway.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 10. Security Checklist

- [ ] SONA_JWT_SECRET is unique, ≥32 chars, not in any file
- [ ] SONA_DEPENDENCY_MODE=production
- [ ] SONA_MCP_DEMO_TOOLS_ENABLED=false (or unset)
- [ ] Redis requires password (REDIS_PASSWORD set)
- [ ] Qdrant behind firewall (not exposed publicly)
- [ ] Ollama behind firewall
- [ ] HTTPS termination via reverse proxy (nginx/caddy)
- [ ] Rate limiting active on gateway
- [ ] No .env files deployed to server
- [ ] Logs do not contain secrets
