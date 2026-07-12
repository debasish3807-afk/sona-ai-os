# Android

The Android application for Sona AI OS, built with Kotlin and Jetpack Compose following clean architecture principles.

## Structure

```
android/
├── app/        — Application module (entry point, DI, navigation)
├── compose/    — Jetpack Compose UI components and screens
├── data/       — Data layer (repositories, data sources, DTOs)
├── domain/     — Domain layer (entities, use cases, interfaces)
├── ai/         — AI integration (on-device models, LLM clients)
├── mcp/        — Model Context Protocol client implementation
├── voice/      — Voice input/output and speech processing
├── settings/   — Settings and preferences management
└── widgets/    — Home screen widgets and quick actions
```

## Architecture

Follows **Clean Architecture** with three main layers:

- **Domain**: Pure Kotlin, no Android dependencies. Contains entities, use cases, and repository interfaces.
- **Data**: Implements domain interfaces. Handles network, database, and external service communication.
- **Presentation**: Jetpack Compose UI with MVVM pattern and unidirectional data flow.

## Key Technologies

- Kotlin + Coroutines + Flow
- Jetpack Compose for UI
- Hilt for dependency injection
- Room for local database
- Retrofit/Ktor for networking
- ML Kit / TensorFlow Lite for on-device AI

## Getting Started

```bash
# Open in Android Studio
# Sync Gradle
# Run on device/emulator
```
