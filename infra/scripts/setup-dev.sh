#!/usr/bin/env bash
# Sona AI OS - Development Environment Setup
# Sets up the local development environment with all dependencies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Sona AI OS - Dev Environment Setup ==="
echo "Project root: $PROJECT_ROOT"

# Check prerequisites
command -v python3.12 >/dev/null 2>&1 || { echo "ERROR: Python 3.12 required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker required"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "WARNING: docker compose not found, trying docker-compose"; }

# Create .env from example if not exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Creating .env from .env.example..."
    cp "$PROJECT_ROOT/backend/.env.example" "$PROJECT_ROOT/.env" 2>/dev/null || \
    cat > "$PROJECT_ROOT/.env" << 'EOF'
# Sona AI OS - Local Development Environment
ENVIRONMENT=local
DB_PASSWORD=sona_dev_pass
REDIS_PASSWORD=
QDRANT_URL=http://localhost:6333
LOG_LEVEL=debug
EOF
    echo "Created .env file. Review and update as needed."
fi

# Install shared kernel
echo ""
echo "--- Installing shared kernel ---"
cd "$PROJECT_ROOT/libs/shared-kernel"
pip install -e ".[dev]"

# Install gateway
echo ""
echo "--- Installing gateway ---"
cd "$PROJECT_ROOT/gateway"
pip install -e ".[dev]"

# Start infrastructure services
echo ""
echo "--- Starting infrastructure (postgres, redis, qdrant) ---"
cd "$PROJECT_ROOT"
docker compose -f infra/compose/docker-compose.yml up -d postgres redis qdrant

echo ""
echo "=== Setup Complete ==="
echo "Infrastructure services are running."
echo "Run 'docker compose -f infra/compose/docker-compose.yml logs -f' to view logs."
echo "Run gateway with: cd gateway && uvicorn app.main:app --reload"
