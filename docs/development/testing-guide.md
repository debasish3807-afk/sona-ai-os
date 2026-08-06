# Testing Guide

This document outlines the testing strategy, tools, and conventions for Sona AI OS.

## Testing Pyramid

```
         ╱ E2E Tests (Playwright, Espresso) ╲
        ╱   Integration Tests (testcontainers) ╲
       ╱     Property-Based Tests (Hypothesis)   ╲
      ╱         Unit Tests (pytest, Vitest, JUnit) ╲
     ╱─────────────────────────────────────────────────╲
```

Most tests should be fast unit tests. Property-based and integration tests provide additional confidence.

---

## Python Backend Testing

### Tools

| Tool | Purpose |
|---|---|
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Coverage reporting |
| `hypothesis` | Property-based testing |
| `factory_boy` | Test fixtures / factories |
| `httpx` | Async HTTP testing |

### Running Tests

```bash
# All tests
pytest --cov -v

# Specific service
pytest services/ai-kernel/tests/ -v

# With coverage report
pytest --cov=services/ai-kernel --cov-report=html

# Shared kernel only
pytest libs/shared-kernel/tests/ -v
```

### Test File Organization

```
services/ai-kernel/
└── tests/
    ├── __init__.py
    ├── conftest.py           # Shared fixtures
    ├── test_domain.py        # Domain model tests
    ├── test_ports.py         # Port contract tests
    └── test_properties.py    # Property-based tests
```

### Writing Unit Tests

```python
import pytest
from sona_shared.domain.result import Result


class TestResult:
    def test_ok_creates_successful_result(self):
        result = Result.ok(42)
        assert result.is_success is True
        assert result.value == 42

    def test_fail_creates_failed_result(self):
        result = Result.fail("error message")
        assert result.is_success is False
        assert result.error == "error message"

    def test_accessing_value_on_failed_result_raises(self):
        result = Result.fail("oops")
        with pytest.raises(ValueError):
            _ = result.value
```

### Writing Property-Based Tests

Property tests verify invariants across many random inputs:

```python
from hypothesis import given, strategies as st
from sona_shared.domain.result import Result


@given(st.text())
def test_result_ok_roundtrip(value):
    """Any value wrapped in Result.ok() is retrievable."""
    result = Result.ok(value)
    assert result.is_success is True
    assert result.value == value


@given(st.integers(min_value=1, max_value=65535))
def test_valid_port_numbers_accepted(port):
    """All ports in [1, 65535] should be accepted."""
    config = ServiceConfig(service_name="test", port=port)
    assert config.port == port
```

### Coverage Goals

| Scope | Target |
|---|---|
| Shared Kernel (`libs/shared-kernel`) | 90% |
| Each service | 80% |
| Gateway | 85% |

---

## TypeScript Frontend Testing

### Tools

| Tool | Purpose |
|---|---|
| `vitest` | Test runner (Vite-native) |
| `@testing-library/react` | Component testing |
| `@testing-library/jest-dom` | DOM matchers |
| `jsdom` | Browser environment |

### Running Tests

```bash
cd apps/web

# Watch mode (development)
npm run test

# Single run (CI)
npm run test:run
```

### Writing Component Tests

```typescript
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { App } from "../src/app/App";

describe("App", () => {
  it("renders the welcome message", () => {
    render(<App />);
    expect(screen.getByText("Sona AI OS")).toBeInTheDocument();
  });
});
```

---

## Kotlin Android Testing

### Tools

| Tool | Purpose |
|---|---|
| JUnit 5 | Test runner |
| MockK | Mocking framework |
| Turbine | Flow testing |
| Compose UI Testing | UI component tests |

### Running Tests

```bash
cd apps/android

# Unit tests
./gradlew test

# UI tests (requires emulator)
./gradlew connectedAndroidTest
```

---

## Integration Testing

Integration tests run against real infrastructure using Docker.

```bash
# Start test infrastructure
docker compose -f infra/compose/docker-compose.test.yml up -d

# Run integration tests
pytest --integration -v

# Teardown
docker compose -f infra/compose/docker-compose.test.yml down -v
```

---

## CI Testing

The monorepo CI pipeline (`ci-monorepo.yml`) runs tests based on what changed:

- **Backend changes** (`services/`, `libs/`, `gateway/`): `backend-lint` → `backend-test`
- **Frontend changes** (`apps/web/`): `frontend-ci` (lint, test, build)
- **Android changes** (`apps/android/`): `android-ci` (lint, test)

Only affected jobs run, keeping CI fast for targeted changes.

---

## Best Practices

1. **Test behavior, not implementation** — Tests should survive refactoring
2. **One assertion per concept** — Each test proves one thing
3. **Descriptive names** — `test_expired_token_returns_401`, not `test_auth`
4. **No network calls in unit tests** — Mock at the port boundary
5. **Use factories** — Don't repeat object construction in every test
6. **Property tests for invariants** — If "for all X, Y holds", write a property test
7. **Fast feedback** — Unit tests should run in under 5 seconds total
