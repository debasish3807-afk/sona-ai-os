# Contributing Guide

Thank you for contributing to Sona AI OS! This guide covers everything you need to know to contribute effectively.

## Development Workflow

1. **Fork & Clone** — Fork the repository and clone locally
2. **Branch** — Create a feature branch from `develop`
3. **Implement** — Make your changes following our coding standards
4. **Test** — Ensure all existing and new tests pass
5. **Lint** — Run `make lint` and fix any issues
6. **Commit** — Use conventional commit messages
7. **Push & PR** — Push your branch and open a Pull Request against `develop`

## Branch Naming

Use these prefixes:
- `feat/` — New features (e.g., `feat/memory-consolidation`)
- `fix/` — Bug fixes (e.g., `fix/token-refresh-race`)
- `refactor/` — Code restructuring without behavior change
- `docs/` — Documentation updates
- `test/` — Adding or fixing tests
- `chore/` — Tooling, CI, dependencies

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

<body>

<footer>
```

**Examples:**
```
feat(ai-kernel): add chain-of-thought reasoning strategy
fix(memory-os): prevent duplicate embeddings on re-index
docs(architecture): update data flow diagram
test(security): add JWT expiry property tests
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `perf`

**Scope** should be the service or module name (e.g., `ai-kernel`, `gateway`, `shared-kernel`).

## Pull Request Guidelines

### Before Submitting

- [ ] All tests pass (`make test`)
- [ ] Lint passes (`make lint`)
- [ ] New functionality has tests (unit + property-based where applicable)
- [ ] Documentation updated if changing public interfaces
- [ ] No unrelated changes in the PR

### PR Description Template

```markdown
## Summary
Brief description of what this PR does.

## Changes
- Added X to service Y
- Fixed Z in library W

## Testing
Describe how this was tested.

## Related Issues
Closes #123
```

### Review Process

1. CI must pass (lint, tests, build)
2. At least one approving review required
3. All review comments must be resolved
4. Squash-merge into `develop`

## Code Organization Rules

### Service Structure

Every service follows Clean Architecture:

```
services/<name>/
├── domain/          Models, entities, value objects, domain events
├── application/     Use cases, port interfaces (ABCs)
├── infrastructure/  Adapters (implementations of ports)
├── tests/           Unit tests, property tests
└── pyproject.toml   Package definition and dependencies
```

### Key Rules

1. **domain/** has NO external dependencies (only standard library + shared-kernel)
2. **application/** depends only on domain/ and port interfaces
3. **infrastructure/** implements ports and may depend on external libraries
4. **tests/** may import from any layer within the same service

### Adding a New Service

1. Create the directory structure under `services/`
2. Create `pyproject.toml` with `sona-shared-kernel` dependency
3. Define domain models in `domain/`
4. Define port interfaces in `application/`
5. Add the service to `settings.gradle.kts` (for workspace resolution)
6. Add to CI matrix in `.github/workflows/ci-monorepo.yml`

## Questions?

- Check existing issues for similar questions
- Open a Discussion for design/architecture questions
- Open an Issue for bugs or specific feature requests
