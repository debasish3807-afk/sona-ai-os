#!/usr/bin/env bash
# Sona AI OS - Database Migration Script
# Runs database migrations against the configured PostgreSQL instance.

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

echo "=== Sona AI OS - Database Migration ==="
echo "Target: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
for i in $(seq 1 30); do
    if PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
        echo "PostgreSQL is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: PostgreSQL not ready after 30 seconds."
        exit 1
    fi
    sleep 1
done

# Create database if not exists
echo "Ensuring database exists..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c \
    "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    PGPASSWORD="$DB_PASSWORD" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"

# Run migrations (placeholder for alembic or similar)
echo "Running migrations..."
# TODO: Integrate with alembic when migration files are created
# alembic -c "$PROJECT_ROOT/backend/alembic.ini" upgrade head

echo ""
echo "=== Migration Complete ==="
