# GitHub Configuration

GitHub-specific configuration including CI/CD workflows, issue templates, and community files.

## Structure

```
.github/
├── workflows/          — GitHub Actions CI/CD pipelines
│   └── ci.yml          — Main CI pipeline
├── ISSUE_TEMPLATE/     — Issue and bug report templates (planned)
└── PULL_REQUEST_TEMPLATE.md — PR template (planned)
```

## Workflows

CI/CD pipelines for:

- Linting and code quality checks (Ruff, Mypy)
- Automated testing (Pytest)
- Security scanning
- Docker image building (when Dockerfiles are added)
- Deployment to staging/production (future)

## Status

- CI workflow: Template ready
- Issue templates: Planned
- PR template: Planned
