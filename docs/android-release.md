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

### Unsigned (default)
Without signing configuration, the release build produces an unsigned APK. There is no debug key fallback. Unsigned APKs cannot be installed on real devices without disabling security checks and will be blocked by Google Play Protect.

### Production (requires secrets)
Set these environment variables for local builds, or configure them as GitHub Actions secrets for CI:
```
ANDROID_KEYSTORE_FILE=path/to/release.keystore
ANDROID_KEYSTORE_PASSWORD=<password>
ANDROID_KEY_ALIAS=<alias>
ANDROID_KEY_PASSWORD=<password>
```

For CI, the keystore is provided as a base64-encoded secret (`ANDROID_KEYSTORE_BASE64`) and decoded at build time. See [Android Release Signing Guide](android-release-signing.md) for full setup instructions.

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
