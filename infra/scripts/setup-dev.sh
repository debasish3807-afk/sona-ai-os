#!/usr/bin/env bash
# Sona AI OS - Development Environment Setup
# Sets up the local development environment with all dependencies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Sona AI OS - Dev Environment Setup ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# --- Check prerequisites ---

echo "--- Checking prerequisites ---"

# Check Python 3.12+
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
        echo "ERROR: Python 3.12+ is required (found Python $PYTHON_VERSION)"
        echo "  Install from: https://www.python.org/downloads/"
        exit 1
    fi
    echo "  Python $PYTHON_VERSION ... OK"
else
    echo "ERROR: Python 3 is not installed."
    echo "  Install Python 3.12+ from: https://www.python.org/downloads/"
    exit 1
fi

# Check Node.js 20+
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VERSION" -lt 20 ]; then
        echo "ERROR: Node.js 20+ is required (found Node.js v$(node -v | sed 's/v//'))"
        echo "  Install from: https://nodejs.org/"
        exit 1
    fi
    echo "  Node.js $(node -v) ... OK"
else
    echo "ERROR: Node.js is not installed."
    echo "  Install Node.js 20+ from: https://nodejs.org/"
    exit 1
fi

# Check Docker
if command -v docker >/dev/null 2>&1; then
    echo "  Docker $(docker --version | grep -oP '\d+\.\d+\.\d+') ... OK"
else
    echo "ERROR: Docker is not installed."
    echo "  Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if docker compose version >/dev/null 2>&1; then
    echo "  Docker Compose $(docker compose version --short 2>/dev/null || echo 'available') ... OK"
elif command -v docker-compose >/dev/null 2>&1; then
    echo "  docker-compose (legacy) ... OK"
else
    echo "WARNING: Docker Compose is not available. Container orchestration will not work."
fi

echo ""

# --- Create .env from example if not exists ---
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "--- Creating .env file ---"
    if [ -f "$PROJECT_ROOT/backend/.env.example" ]; then
        cp "$PROJECT_ROOT/backend/.env.example" "$PROJECT_ROOT/.env"
    else
        cat > "$PROJECT_ROOT/.env" << 'EOF'
# Sona AI OS - Local Development Environment
ENVIRONMENT=local
POSTGRES_USER=sona
POSTGRES_PASSWORD=sona_dev_pass
POSTGRES_DB=sona_db
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
LOG_LEVEL=debug
EOF
    fi
    echo "  Created .env file. Review and update as needed."
    echo ""
fi

# --- Install Python dependencies ---

echo "--- Installing shared libraries ---"
cd "$PROJECT_ROOT"

pip install -e "libs/shared-kernel[dev]" --quiet
echo "  sona-shared-kernel ... installed"

pip install -e "libs/llm-client[dev]" --quiet
echo "  sona-llm-client ... installed"

pip install -e "libs/event-bus[dev]" --quiet
echo "  sona-event-bus ... installed"

echo ""
echo "--- Installing gateway ---"
pip install -e "gateway[dev]" --quiet
echo "  gateway ... installed"

echo ""
echo "--- Installing services ---"
for service in services/*/; do
    if [ -f "$service/pyproject.toml" ]; then
        SERVICE_NAME=$(basename "$service")
        pip install -e "$service[dev]" --quiet 2>/dev/null || pip install -e "$service" --quiet
        echo "  $SERVICE_NAME ... installed"
    fi
done

# --- Install Node.js dependencies ---

echo ""
echo "--- Installing web frontend dependencies ---"
if [ -d "$PROJECT_ROOT/apps/web" ]; then
    cd "$PROJECT_ROOT/apps/web"
    npm install --quiet 2>/dev/null || npm install
    echo "  apps/web ... installed"
fi

# --- Start infrastructure services ---

echo ""
echo "--- Starting infrastructure (postgres, redis, qdrant) ---"
cd "$PROJECT_ROOT"
if [ -f "infra/compose/docker-compose.yml" ]; then
    docker compose -f infra/compose/docker-compose.yml up -d postgres redis qdrant 2>/dev/null || \
        echo "  WARNING: Could not start infrastructure. Run manually with 'make up'"
fi

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "  Infrastructure: docker compose -f infra/compose/docker-compose.yml logs -f"
echo "  Gateway:        cd gateway && uvicorn app.main:app --reload"
echo "  Web Frontend:   cd apps/web && npm run dev"
echo "  Run Tests:      make test"
echo ""
