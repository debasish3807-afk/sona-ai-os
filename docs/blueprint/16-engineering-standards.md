# 16 — Engineering Standards

> Engineering Standards define the conventions, practices, and processes that ensure consistent, high-quality development across the Sona AI OS project. These standards apply to all contributors and are enforced through automation where possible.

---

## Folder Standards

### Package Structure

```text
sona-ai-os/
├── backend/
│   ├── src/
│   │   └── sona/
│   │       ├── kernel/           # Cognitive Kernel
│   │       ├── engines/          # Engine implementations
│   │       ├── memory/           # Memory Fabric
│   │       ├── knowledge/        # Knowledge Fabric
│   │       ├── execution/        # Execution Fabric
│   │       ├── verification/     # Verification Fabric
│   │       ├── capabilities/     # Capability Fabric
│   │       ├── security/         # Security layer
│   │       ├── observability/    # Metrics, tracing, logging
│   │       ├── api/              # FastAPI routes and schemas
│   │       ├── models/           # Domain models (dataclasses)
│   │       ├── providers/        # External service integrations
│   │       └── shared/           # Cross-cutting utilities
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── migrations/
│   └── scripts/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── stores/
│   │   ├── api/
│   │   └── utils/
│   └── tests/
├── android/
├── desktop/
├── cli/
├── docs/
│   ├── architecture/
│   ├── blueprint/
│   ├── api/
│   └── guides/
└── infrastructure/
    ├── docker/
    ├── k8s/
    └── terraform/
```

### Naming Conventions (Files & Directories)

| Item | Convention | Example |
|------|-----------|---------|
| Python packages | `snake_case` | `memory_fabric/` |
| Python modules | `snake_case.py` | `working_memory.py` |
| TypeScript files | `kebab-case.ts` | `goal-manager.ts` |
| React components | `PascalCase.tsx` | `GoalList.tsx` |
| Test files | `test_*.py` / `*.test.ts` | `test_kernel.py` |
| Configuration | `kebab-case` | `docker-compose.yml` |
| Documentation | `kebab-case.md` or `NN-title.md` | `04-cognitive-kernel.md` |

---

## Naming Conventions

### Python

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | `PascalCase` | `CognitiveKernel` |
| Functions | `snake_case` | `process_request` |
| Variables | `snake_case` | `goal_state` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Private members | `_leading_underscore` | `_internal_state` |
| Type variables | `PascalCase` with suffix | `EngineT`, `ResultT` |
| Protocols | `PascalCase` | `ExecutionEngine` |
| Enums | `PascalCase` (class), `UPPER` (members) | `GoalState.EXECUTING` |

### TypeScript

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | `PascalCase` | `GoalManager` |
| Interfaces | `PascalCase` | `KernelConfig` |
| Functions | `camelCase` | `processRequest` |
| Variables | `camelCase` | `goalState` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| React components | `PascalCase` | `GoalList` |
| Hooks | `useCamelCase` | `useGoalState` |
| CSS classes | `kebab-case` | `goal-card` |

### General Rules

- No abbreviations unless universally understood (`id`, `url`, `api`)
- Boolean variables prefixed with `is_`, `has_`, `can_`, `should_`
- Collection variables use plural nouns (`goals`, `tasks`, `events`)
- Functions use verb phrases (`create_goal`, `validate_plan`)

---

## Coding Standards

### Python

| Standard | Requirement |
|----------|-------------|
| Version | Python 3.12+ |
| Paradigm | Async-first (all I/O operations async) |
| Type hints | Full typing on all functions and variables |
| Type checking | mypy strict mode, zero errors |
| Linting | ruff (replaces flake8, isort, pyupgrade) |
| Formatting | ruff format (Black-compatible) |
| No `Any` | Explicit types always; `Any` requires justification comment |
| SOLID | Single responsibility, open/closed, dependency inversion |
| Error handling | Custom exception hierarchy, no bare `except` |
| Imports | Absolute imports only, grouped by stdlib/third-party/local |

### Async Guidelines

| Rule | Description |
|------|-------------|
| All I/O is async | Database, HTTP, file system operations |
| No blocking calls | Never block the event loop |
| Structured concurrency | Use `asyncio.TaskGroup` for parallel tasks |
| Timeouts everywhere | All async operations have explicit timeouts |
| Cancellation support | All async functions honor cancellation |

### Forbidden Patterns

| Pattern | Reason | Alternative |
|---------|--------|-------------|
| `from module import *` | Pollutes namespace | Explicit imports |
| `except Exception:` | Swallows all errors | Specific exceptions |
| Global mutable state | Threading issues | Dependency injection |
| `type: ignore` without reason | Hides type errors | Fix the type error |
| Nested functions > 2 levels | Readability | Extract to methods |
| Magic numbers | Unmaintainable | Named constants |

---

## Testing Standards

### Framework and Tools

| Tool | Purpose |
|------|---------|
| pytest | Test runner and framework |
| pytest-asyncio | Async test support |
| pytest-cov | Coverage measurement |
| factory_boy | Test data factories |
| hypothesis | Property-based testing |
| httpx | Async HTTP test client |
| testcontainers | Integration test infrastructure |

### Coverage Requirements

| Level | Minimum | Target | Enforcement |
|-------|---------|--------|-------------|
| Line coverage | 80% | 90% | CI gate at minimum |
| Branch coverage | 70% | 80% | CI warning |
| New code coverage | 90% | 95% | PR check |

### Test Organization

| Type | Location | Naming | Dependencies |
|------|----------|--------|-------------|
| Unit | `tests/unit/` | `test_<module>.py` | None (all mocked) |
| Integration | `tests/integration/` | `test_<feature>_integration.py` | Real services (containers) |
| E2E | `tests/e2e/` | `test_<flow>_e2e.py` | Full system |
| Performance | `tests/performance/` | `bench_<component>.py` | Isolated environment |

### Test Quality Rules

| Rule | Enforcement |
|------|-------------|
| Each test tests one thing | Code review |
| Test names describe behavior | Linting |
| No shared mutable state between tests | pytest isolation |
| Tests must be deterministic | No random, no time-dependent |
| Arrange-Act-Assert structure | Code review |
| Fixtures over setup/teardown | pytest best practices |
| Mock at boundaries only | Code review |

---

## Documentation Standards

### Required Documentation

| Scope | Requirement | Format |
|-------|-------------|--------|
| Public APIs | Docstring on every public function/class | Google-style docstring |
| Modules | Module-level docstring explaining purpose | First line of file |
| Architecture | Per-module architecture doc | Markdown in `docs/` |
| ADRs | For significant technical decisions | `docs/adr/` |
| Changelog | For every release | `CHANGELOG.md` |
| API reference | Auto-generated from docstrings | OpenAPI spec |

### Docstring Format

```text
"""Short one-line summary.

Longer description if needed. Explain the purpose,
behavior, and any important considerations.

Args:
    param_name: Description of the parameter.
    another_param: Description with type info if complex.

Returns:
    Description of the return value.

Raises:
    SpecificError: When this error condition occurs.

Example:
    >>> result = function_name(arg1, arg2)
    >>> assert result == expected
"""
```

### Architecture Documentation

Each module maintains:
- `README.md` — Purpose, responsibilities, public API
- `ARCHITECTURE.md` — Internal design, diagrams, trade-offs
- `CHANGELOG.md` — Version history and migration notes

---

## Release Standards

### SemVer Policy

| Change | Version Bump | Examples |
|--------|--------------|---------|
| Breaking API change | MAJOR | Remove endpoint, change schema |
| New feature (backward-compatible) | MINOR | Add endpoint, new capability |
| Bug fix | PATCH | Fix error, performance improvement |
| Pre-release | Suffix | `1.2.0-beta.1`, `2.0.0-rc.1` |

### Changelog Format

```text
## [1.2.0] - 2024-03-15

### Added
- New capability: code review pipeline (#123)
- Support for streaming responses in CLI

### Changed
- Improved goal scheduling priority algorithm
- Updated minimum Python version to 3.12

### Fixed
- Race condition in concurrent goal execution (#456)
- Memory leak in long-running sessions

### Deprecated
- `old_api_endpoint` — use `new_api_endpoint` instead (removal in 2.0)
```

### Migration Guides

Required for any MAJOR version bump:
- List all breaking changes
- Provide before/after code examples
- Automated migration script where possible
- Deprecation warnings added one MINOR version before removal

### Deprecation Policy

```text
1. Add deprecation warning in MINOR release (N.x)
2. Document in CHANGELOG and migration guide
3. Maintain deprecated functionality for one MINOR cycle
4. Remove in next MAJOR release (N+1.0)
5. Provide automated migration tool if possible
```

---

## ADR Workflow

### Architecture Decision Records

ADRs document significant technical decisions with their context and consequences.

### ADR Lifecycle

```text
PROPOSED → REVIEW → ACCEPTED | REJECTED → RECORDED
                                         ↓
                                    SUPERSEDED (by newer ADR)
```

### ADR Template

```text
# ADR-NNN: Title

## Status
Proposed | Accepted | Rejected | Superseded by ADR-XXX

## Context
What is the problem or decision we need to make?

## Decision Drivers
- Driver 1
- Driver 2

## Considered Options
1. Option A — description
2. Option B — description
3. Option C — description

## Decision
We chose Option B because...

## Consequences
### Positive
- Benefit 1
- Benefit 2

### Negative
- Trade-off 1
- Trade-off 2

## Related
- ADR-NNN (related decision)
- Issue #NNN
```

### ADR Rules

| Rule | Description |
|------|-------------|
| Immutable once accepted | Never modify accepted ADRs; supersede instead |
| Numbered sequentially | ADR-001, ADR-002, etc. |
| Review required | Minimum 2 approvers |
| Time-boxed review | 5 business days maximum |
| Stored in repo | `docs/adr/` directory |

---

## RFC Workflow

### Request for Comments

RFCs are used for significant feature proposals or architectural changes.

### RFC Lifecycle

```text
DRAFT → DISCUSSION → REVISION → FINAL → IMPLEMENT
                         ↓
                     WITHDRAWN
```

### RFC Process

| Phase | Duration | Activities |
|-------|----------|------------|
| Draft | 1 week | Author writes proposal |
| Discussion | 2 weeks | Team provides feedback |
| Revision | 1 week | Author incorporates feedback |
| Final | — | Approved by maintainers |
| Implement | — | Work begins |

### RFC Template

```text
# RFC-NNN: Title

## Summary
One paragraph overview.

## Motivation
Why is this needed? What problem does it solve?

## Detailed Design
Technical specification of the proposal.

## Drawbacks
Why should we NOT do this?

## Alternatives
What other approaches were considered?

## Unresolved Questions
What needs further investigation?

## Implementation Plan
High-level steps to implement this RFC.
```

### RFC Rules

| Rule | Description |
|------|-------------|
| Required for cross-module changes | Changes affecting 3+ modules need RFC |
| Required for new external dependencies | Any new third-party dependency |
| Required for API changes | Public API modifications |
| Champion required | One person drives the RFC to completion |
| Consensus-based approval | Majority of maintainers must approve |

---

*Next: [17 — Implementation Roadmap](./17-implementation-roadmap.md)*
