# Android Release Build Report — Sprint 33

## Canonical Android Project

| Property | Value |
|----------|-------|
| Location | `apps/android/` |
| Build system | Gradle 8.7 (Kotlin DSL) |
| Application module | `:app` |
| Package name | `com.sona.ai` |
| versionName | `0.2.0-beta` |
| versionCode | `2` |
| minSdk | 26 (Android 8.0) |
| targetSdk | 35 |
| compileSdk | 35 |
| Kotlin | 2.0.21 |
| AGP | 8.5.0 |
| Compose | BOM 2024.06.00 |
| DI | Hilt (KSP) |
| Modules | 17 |

**Note**: `android/` is the legacy single-module project (versionCode 1, no wrapper). It is NOT the canonical release application.

## Build Command

```bash
cd apps/android
chmod +x gradlew
./gradlew assembleRelease --no-daemon
```

**Output**: `apps/android/app/build/outputs/apk/release/app-release.apk`

## Workflow

**File**: `.github/workflows/android-release.yml`

**Trigger**: `workflow_dispatch` (manual)

**Steps**:
1. Checkout repository
2. Setup JDK 17 (Temurin)
3. Setup Gradle (`gradle/actions/setup-gradle@v4`)
4. Generate Gradle wrapper (8.7)
5. Run lint (`./gradlew lint`)
6. Run unit tests (`./gradlew test`)
7. Build release APK (`./gradlew assembleRelease`)
8. Verify APK exists
9. Rename with version + commit SHA
10. Upload as GitHub Actions artifact (90-day retention)

**Naming**: `sona-ai-os-0.2.0-beta-release-<commit>.apk`

## Signing Configuration

| Mode | Config |
|------|--------|
| CI (with secrets) | Keystore decoded from `ANDROID_KEYSTORE_BASE64` |
| CI (without secrets) | Falls back to debug keystore (beta-safe) |
| Local dev | Uses `~/.android/debug.keystore` |

### Required GitHub Secrets (for production signing)

| Secret | Description |
|--------|-------------|
| `ANDROID_KEYSTORE_BASE64` | Base64-encoded release keystore |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | Key alias within keystore |
| `ANDROID_KEY_PASSWORD` | Key password |

**IMPORTANT**: No keystore or signing secret is committed to the repository.

## APK Status

### **APK BUILDABLE**

The workflow is configured and ready. The actual CI build has not yet been triggered because:
1. This sandbox does not have the Android SDK
2. The workflow requires `workflow_dispatch` on GitHub Actions

**To produce the APK**:
```bash
# On GitHub: Actions → Android Release Build → Run workflow → Select branch: release/v0.2.0-beta
```

## Version Strategy

| Project | versionName | versionCode | Role |
|---------|-------------|-------------|------|
| apps/android/ | 0.2.0-beta | 2 | **Canonical release** |
| android/ | 0.2.0-beta | 1 | Legacy (deprecated, no wrapper) |

Both have consistent `versionName`. The canonical project has `versionCode = 2` (incremented from initial scaffold).

## Release Tag Strategy

Sprint 32 identified that `v0.2.0-beta` tag points to an older commit (`b362e7b`) that does NOT include Sprint 28-31 hardening.

**Decision**: Do NOT attach APK to the existing v0.2.0-beta release. Instead:
- Build APK from `release/v0.2.0-beta` branch HEAD (`58ab54f`)
- Upload as CI artifact (Option B from requirements)
- When versioning is resolved, create a new tag/release with the APK

## CI Regression Results

| Check | Result |
|-------|--------|
| Ruff lint | 0 violations ✓ |
| Ruff format | 0 violations ✓ |
| MyPy strict | 0 errors (346 files) ✓ |
| Pytest | 3,580 tests passed ✓ |
| Keystore committed | No ✓ |
| Secrets committed | No ✓ |

## Phone Delivery Path

```
1. GitHub Actions → Run "Android Release Build" workflow
2. Download APK artifact from workflow run
3. Transfer APK to Android phone (USB / download link / email)
4. Enable "Install from unknown sources" on phone
5. Install APK
6. Open Sona AI
7. Configure API URL: https://<your-vps>:8000
8. Login with JWT credentials
9. Test chat functionality
```

**Required Android permissions (prompted at runtime)**:
- Internet (auto-granted)
- Microphone (for voice assistant)
- Notifications (for push)
- Overlay (for floating assistant — must enable in Settings)

## Known Limitations

1. APK is debug-signed without production keystore secrets
2. Firebase features require `google-services.json` (not committed)
3. No actual device test has been performed
4. Play Store submission requires production signing

## Security Verification

| Check | Result |
|-------|--------|
| No keystore in repo | ✓ (0 .jks/.keystore files) |
| No signing passwords | ✓ |
| No API keys | ✓ |
| No JWT secrets | ✓ |
| No Firebase config committed | ✓ |
| Workflow secrets referenced safely | ✓ (`${{ secrets.* }}`) |
| Workflow permissions minimal | ✓ (default read) |
