# Migration Guide — v0.1.0-beta → v0.2.0-beta

## Overview

This document describes the changes required to upgrade from Sona AI OS v0.1.0-beta (1.0.0-rc1) to v0.2.0-beta.

## Breaking Changes

### 1. Android Project Structure (#68)

**Change**: The primary Android client has moved from `android/` (single-module) to `apps/android/` (multi-module).

**Action Required**:
- Update all build scripts and CI references to point to `apps/android/`
- The `android/` directory remains for backward compatibility but is deprecated
- Gradle wrapper is now at `apps/android/gradlew`

### 2. Version Identifier Format (#67–#76)

**Change**: Version format changed from `1.0.0-rc1` to `0.2.0-beta` to reflect beta status.

**Action Required**:
- Update any hardcoded version references in deployment scripts
- API version is now `0.2.0-beta` (check health endpoints)

### 3. Python Package Namespace (#67)

**Change**: All services use `sona_*` namespaced packages (e.g., `sona_ai_kernel`, `sona_memory`).

**Action Required**:
- Update any import statements referencing old package paths
- Install packages with `pip install --no-deps -e services/<service-name>/`

## New Environment Variables

| Variable | Service | Default | Description |
|----------|---------|---------|-------------|
| `FIREBASE_PROJECT_ID` | Android | — | Firebase project for Crashlytics/Analytics (#76) |
| `GITHUB_OAUTH_CLIENT_ID` | MCP Integration | — | GitHub OAuth app client ID (#73) |
| `GITHUB_OAUTH_CLIENT_SECRET` | MCP Integration | — | GitHub OAuth app client secret (#73) |
| `GOOGLE_OAUTH_CLIENT_ID` | MCP Integration | — | Google OAuth client ID (#73) |
| `GOOGLE_OAUTH_CLIENT_SECRET` | MCP Integration | — | Google OAuth client secret (#73) |
| `REDIS_URL` | All services | `redis://localhost:6379` | Redis connection URL (optional) |
| `QDRANT_URL` | Memory/Knowledge | `http://localhost:6333` | Qdrant vector DB URL (optional) |

## Configuration Changes

### CI/CD (#68)

- **New**: `ci-monorepo.yml` is the authoritative CI pipeline
- **Deprecated**: `ci.yml` (legacy, scoped to `backend/**` only)
- **New**: Android CI job triggers on `apps/android/**` changes

### Android (#68, #75)

- **compileSdk**: 35
- **minSdk**: 29 (Android 10)
- **targetSdk**: 35
- **Kotlin**: 2.0.21
- **AGP**: 8.5.0
- **Gradle**: 8.7
- **Compose BOM**: latest
- **DI**: Hilt with KSP (not kapt)

### Backend (#67)

- **Python**: 3.12+ required
- **MyPy**: Strict mode enforced
- **Ruff**: Runs from repo root with `known-first-party` for 17 packages
- **Tests**: Per-service execution (`cd services/<name> && pytest tests/`)

## Non-Breaking Additions

These features are new in v0.2.0-beta and require no migration:

- Firebase Crashlytics/Performance/Analytics (#76)
- In-app feedback and bug reporting (#76)
- Floating AI overlay and home widgets (#75)
- Voice Assistant with wake word (#71)
- Vision AI camera features (#70)
- Communication hub (#72)
- GitHub/Google connectors (#73)
- AI Dashboard (#74)

## Rollback Procedure

If migration fails:
1. Revert to the `v0.1.0-beta` tag: `git checkout v0.1.0-beta`
2. Restore the `android/` project as primary build target
3. Use `ci.yml` workflow for backend-only validation
4. Remove new environment variables (optional features degrade gracefully)
