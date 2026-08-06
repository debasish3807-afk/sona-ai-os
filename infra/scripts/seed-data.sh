#!/usr/bin/env bash
# Sona AI OS - Seed Data Script
# Seeds the database with initial development data.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-sona_db}"
DB_USER="${DATABASE_USER:-sona}"
DB_PASSWORD="${DB_PASSWORD:-sona_dev_pass}"

echo "=== Sona AI OS - Seed Data ==="
echo "Target: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"

# Wait for database
echo "Checking database connectivity..."
if ! PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
    echo "ERROR: PostgreSQL not available. Run migrations first."
    exit 1
fi

# Seed default configuration
echo "Seeding default LLM provider configurations..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'SQL'
-- Create providers table if not exists (temporary until migrations are set up)
CREATE TABLE IF NOT EXISTS llm_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    provider_type VARCHAR(50) NOT NULL,
    base_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default providers
INSERT INTO llm_providers (name, provider_type, base_url, is_active) VALUES
    ('openai', 'openai', 'https://api.openai.com/v1', true),
    ('anthropic', 'anthropic', 'https://api.anthropic.com', true),
    ('ollama-local', 'ollama', 'http://localhost:11434', true),
    ('google-ai', 'google', 'https://generativelanguage.googleapis.com', true)
ON CONFLICT (name) DO NOTHING;

SELECT format('Seeded %s providers', count(*)) FROM llm_providers;
SQL

echo ""
echo "=== Seed Complete ==="
