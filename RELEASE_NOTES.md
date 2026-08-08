# Release Notes — v0.2.0-beta

## Summary

Sona AI OS v0.2.0-beta is the first public beta release, consolidating 10 major sprints of development into a unified, stable release. This version delivers a complete AI Operating System with a production-ready Python backend (14 services), a multi-module Android client (Kotlin/Compose), and comprehensive CI/CD infrastructure.

## New Capabilities

- **Personal AI Runtime** (#67) — Research OS with personal AI agent, knowledge synthesis, and adaptive learning pipelines
- **Android Runtime Phase 1** (#68) — Multi-module Android architecture with Hilt DI, Compose UI, and NavHost navigation
- **Android AI Features** (#69) — Chat, voice input, camera integration, and file management modules
- **Vision AI Runtime** (#70) — Real-time camera analysis, document scanning, and visual intelligence features
- **Voice Assistant Runtime** (#71) — Hands-free voice interaction with wake word detection, streaming TTS, and conversation management
- **Communication AI Runtime** (#72) — Unified communication hub with email, messaging, and calendar AI integration
- **Connector Runtime** (#73) — OAuth 2.0 + PKCE connector framework for GitHub and Google services with background sync
- **Daily Driver Dashboard** (#74) — AI-powered home dashboard with daily brief, schedule, and activity summaries
- **Daily Driver Optimization** (#75) — Floating AI overlay, home widgets, quick settings tile, Material Motion, and accessibility
- **Public Beta Operations** (#76) — Firebase Crashlytics/Performance/Analytics, in-app feedback, Play Store readiness, beta monitoring

## Improvements

- 3,514+ backend tests with 100% pass rate across 14 services and 4 libraries
- MyPy strict compliance across entire Python codebase (343 source files)
- Ruff lint and format clean (587 Python files)
- Multi-module Android architecture with 17 Gradle modules and 185 Kotlin source files
- CI Monorepo Pipeline with path-based detection for backend, android, and frontend changes
- Namespaced Python packages (sona_*) eliminating installation conflicts

## Known Limitations

- Android instrumentation tests require physical device or emulator (not available in CI sandbox)
- `deploy-prod.yml` tag pattern does not match beta versioning (`v0.2.0-beta`)
- Offline mode requires initial online sync before local caching activates
- Voice wake word detection requires microphone permission grant at runtime
- Google/GitHub OAuth requires API credentials configured in environment

## System Requirements

### Backend
- Python 3.12+
- Redis (for caching, optional — graceful fallback to in-memory)
- Qdrant (for vector storage, optional — graceful fallback to in-memory)

### Android
- Android 10+ (API 29)
- Kotlin 2.0.21
- compileSdk 35
- Java 17

## Upgrade from v0.1.0-beta

See [MIGRATION.md](MIGRATION.md) for detailed upgrade instructions.
