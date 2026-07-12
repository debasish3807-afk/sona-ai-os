# Tests

Top-level test suites for Sona AI OS including integration and end-to-end tests.

## Structure

```
tests/
├── integration/   — Cross-service integration tests
├── e2e/           — End-to-end user workflow tests
└── fixtures/      — Shared test data and fixtures
```

## Purpose

This directory holds tests that span multiple components or services. Unit tests for individual modules live within their respective directories (e.g., `backend/tests/`).

## Test Levels

| Level | Location | Scope |
|-------|----------|-------|
| Unit | `<module>/tests/` | Single function/class |
| Integration | `tests/integration/` | Multiple components |
| End-to-End | `tests/e2e/` | Full user workflows |

## Running Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run end-to-end tests
pytest tests/e2e/

# Run with coverage
pytest tests/ --cov --cov-report=html
```

## Guidelines

- Tests should be deterministic and independent
- Use fixtures for shared test data
- Mock external services in integration tests
- E2E tests should mirror real user workflows
