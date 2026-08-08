# Changelog

All notable changes to Sona AI OS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.2.0-beta] - 2026-08-06

### Added

- Personal AI Integration Runtime with research agent and knowledge synthesis (#67)
- Multi-module Android architecture with Hilt DI, Compose, Material 3 (#68)
- Android AI features: Chat, Voice, Camera, Files modules (#69)
- Vision AI Runtime with real-time camera analysis and document scanning (#70)
- Voice Assistant Runtime with wake word detection and streaming TTS (#71)
- Communication AI Runtime with email, messaging, calendar integration (#72)
- Connector Runtime with OAuth 2.0 + PKCE for GitHub and Google (#73)
- AI-powered Dashboard with daily brief, schedule, activity summaries (#74)
- Floating AI overlay, home widgets, quick settings tile (#75)
- Firebase Crashlytics, Performance Monitoring, Analytics integration (#76)
- In-app feedback system and bug report screen (#76)
- Play Store readiness artifacts (release AAB, privacy policy, data safety) (#76)
- Beta operations monitoring dashboard (#76)
- 3,514+ backend tests across 14 services (#67–#76)
- CI Monorepo Pipeline with path-based change detection (#68–#76)

### Changed

- Version identifier updated from `1.0.0-rc1` to `0.2.0-beta` (#67–#76)
- Android app version updated from `0.1.0-beta` to `0.2.0-beta` (#75)
- MyPy strict mode compliance enforced across all Python services (#67)
- Ruff linting enforced from repository root with unified configuration (#67)

### Fixed

- Removed obsolete `type: ignore[override]` comments in domain event classes (#67–#76, internal)
- Fixed variable reuse type conflicts in thalamus routing engine (#73, internal)
- Fixed variable reuse type conflicts in brain-os runtime (#74, internal)
- Added proper type annotations for FastAPI/Pydantic strict-mode compatibility (#67, internal)

### Deprecated

- Single-module Android project at `android/` — use `apps/android/` instead (#68)
- Legacy `ci.yml` workflow — `ci-monorepo.yml` is the authoritative pipeline (#68, internal)

## [v0.1.0-beta] - 2026-08-07

### Added

- Initial AI Kernel with multi-provider LLM integration
- Brain OS execution planning and orchestration
- Memory OS with vector storage and context management
- THALAMUS routing engine
- Knowledge OS with RAG pipeline
- MCP Integration service
- Security service with JWT and RBAC
- Observability service with structured logging
- Workforce OS multi-agent framework
- Plugin System with sandboxed execution
- Gateway API with streaming support
- Basic Android client (single-module)
