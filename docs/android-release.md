# Sona AI OS — Android Release Guide

## Quick Start

### Build locally
```bash
cd apps/android
chmod +x gradlew
./gradlew assembleRelease --no-daemon
```

### Build via CI
1. Go to GitHub Actions
2. Select "Android Release Build"
3. Click "Run workflow"
4. Select branch: `release/v0.2.0-beta`
5. Download APK from artifacts

## Project Structure

```
apps/android/
├── app/                    # Main application module
├── core/
│   ├── domain/            # Domain models
│   ├── data/              # Data layer (Room, API)
│   └── di/                # Dependency injection
├── features/
│   ├── chat/              # Chat UI
│   ├── voice/             # Voice assistant
│   ├── vision/            # Camera/vision
│   ├── camera/            # Camera capture
│   ├── files/             # File management
│   ├── memory/            # Memory browser
│   ├── agents/            # Agent management
│   ├── communication/     # Email/messaging
│   ├── connectors/        # GitHub/Google OAuth
│   ├── dashboard/         # AI dashboard
│   ├── overlay/           # Floating assistant
│   ├── settings/          # App settings
│   └── beta/              # Beta feedback
├── gradle/wrapper/
├── build.gradle.kts       # Root build config
├── settings.gradle.kts    # Module declarations
└── gradlew                # Gradle wrapper script
```

## Signing

### Beta (default — debug key)
No configuration needed. Uses Android debug keystore automatically.

### Production (requires secrets)
Set these environment variables or GitHub secrets:
```
SIGNING_STORE_FILE=path/to/release.keystore
SIGNING_STORE_PASSWORD=<password>
SIGNING_KEY_ALIAS=<alias>
SIGNING_KEY_PASSWORD=<password>
```

## Version Info

| Field | Value |
|-------|-------|
| Package | com.sona.ai |
| versionName | 0.2.0-beta |
| versionCode | 2 |
| minSdk | 26 (Android 8.0+) |
| targetSdk | 35 |

## Installation

1. Download APK from GitHub Actions artifacts
2. Transfer to device
3. Settings → Security → Allow unknown sources
4. Open APK → Install
5. Launch "Sona AI"
6. Configure backend URL in Settings
