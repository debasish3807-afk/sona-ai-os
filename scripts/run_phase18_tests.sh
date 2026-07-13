#!/usr/bin/env bash
# Phase 18 Test Suite Runner
# Runs all quality gates: Ruff, Mypy, Bandit, Pytest
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
cd "$BACKEND_DIR"

echo "=========================================="
echo "  Sona AI OS — Phase 18 Test Validation"
echo "=========================================="
echo ""

# --- Ruff Lint ---
echo "[1/5] Running Ruff linter..."
python -m ruff check tests/test_phase18.py
echo "  ✓ Ruff lint: PASSED"
echo ""

# --- Ruff Format ---
echo "[2/5] Running Ruff format check..."
python -m ruff format --check tests/test_phase18.py
echo "  ✓ Ruff format: PASSED"
echo ""

# --- Mypy ---
echo "[3/5] Running Mypy type checker..."
python -m mypy tests/test_phase18.py --ignore-missing-imports --no-strict-optional
echo "  ✓ Mypy: PASSED"
echo ""

# --- Bandit ---
echo "[4/5] Running Bandit security scanner (skipping B101 for test asserts)..."
python -m bandit tests/test_phase18.py --skip B101 -ll --quiet
echo "  ✓ Bandit: PASSED (no medium/high issues)"
echo ""

# --- Pytest ---
echo "[5/5] Running Pytest (401 tests)..."
python -m pytest tests/test_phase18.py -v --tb=short
echo ""

echo "=========================================="
echo "  ALL QUALITY GATES PASSED"
echo "=========================================="
