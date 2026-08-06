# Sona AI OS - Development Makefile
# Usage: make <target>

.DEFAULT_GOAL := help

COMPOSE_FILE := infra/compose/docker-compose.yml
COMPOSE_DEV := infra/compose/docker-compose.dev.yml

.PHONY: help setup lint format test build up down logs clean

## help: Show this help message
help:
	@echo "Sona AI OS - Development Commands"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'

## setup: Set up the development environment (install all dependencies)
setup:
	@bash infra/scripts/setup-dev.sh

## lint: Run linters on all code (Python + frontend)
lint:
	@echo "--- Python lint ---"
	ruff check services/ libs/ gateway/
	ruff format --check services/ libs/ gateway/
	@echo ""
	@echo "--- Frontend lint ---"
	@if [ -d "apps/web/node_modules" ]; then \
		cd apps/web && npm run lint; \
	else \
		echo "  Skipped (run 'make setup' first)"; \
	fi

## format: Auto-format all Python code
format:
	ruff format services/ libs/ gateway/
	ruff check --fix services/ libs/ gateway/

## test: Run all tests (Python backend + frontend)
test:
	@echo "--- Python tests ---"
	pytest --cov -v
	@echo ""
	@echo "--- Frontend tests ---"
	@if [ -d "apps/web/node_modules" ]; then \
		cd apps/web && npm run test:run; \
	else \
		echo "  Skipped (run 'make setup' first)"; \
	fi

## build: Build all Docker images
build:
	docker compose -f $(COMPOSE_FILE) build

## up: Start all services with Docker Compose
up:
	docker compose -f $(COMPOSE_FILE) up -d

## down: Stop all Docker Compose services
down:
	docker compose -f $(COMPOSE_FILE) down

## logs: Follow logs from all Docker services
logs:
	docker compose -f $(COMPOSE_FILE) logs -f

## clean: Remove build artifacts, caches, and virtual environments
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Done."
