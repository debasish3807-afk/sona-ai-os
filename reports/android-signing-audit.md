# Android Signing Audit Report

**Date:** 2024-08-08
**Version:** 0.2.0-beta (versionCode 2)
**Package:** com.sona.ai

---

## 1. Root Cause Analysis: Play Protect Block

### Primary Causes

1. **Debug Certificate Signing (CN=Android Debug)** - The main trigger. Prior to this fix, the release build fell back to the Android debug signing key when production signing secrets were not configured. Play Protect is significantly more suspicious of APKs signed with debug certificates because they indicate a development build, not a production release.

2. **Sideloading Without Play Store Reputation** - APKs distributed outside the Google Play Store have zero trust reputation. Play Protect cannot verify the developer identity or app history, resulting in an elevated risk assessment.

### Secondary Contributors

3. **Sensitive Permissions** - The app requests several high-risk permissions (READ_SMS, READ_CALL_LOG, READ_CONTACTS, BIND_NOTIFICATION_LISTENER_SERVICE, SYSTEM_ALERT_WINDOW) that raise the computed risk score. These alone would not block installation but compound the primary factors.

4. **No Google Play App Signing Enrollment** - Without Play App Signing, Google cannot establish a chain of trust for the certificate. Production signing with a consistent, enrolled certificate is required for full reputation.

### Resolution Path

The combination of debug certificate + sideloading + sensitive permissions crosses Play Protect's block threshold. The fix is:

- Sign with a dedicated, stable production certificate (not debug)
- Enroll in Google Play App Signing
- Distribute through the Play Store (or at minimum, establish certificate reputation)
- None of the sensitive permissions should be removed, as they are required for legitimate app features

---

## 2. Signing Configuration Analysis

### Before (Original Configuration)

```kotlin
// apps/android/app/build.gradle.kts (BEFORE)
signingConfigs {
    create("release") {
        val storeFilePath = System.getenv("SIGNING_STORE_FILE")
        if (!storeFilePath.isNullOrEmpty()) {
            storeFile = file(storeFilePath)
            storePassword = System.getenv("SIGNING_STORE_PASSWORD")
            keyAlias = System.getenv("SIGNING_KEY_ALIAS")
            keyPassword = System.getenv("SIGNING_KEY_PASSWORD")
        }
    }
}

buildTypes {
    release {
        // PROBLEM: fell back to debug signing when env vars not set
        signingConfig = signingConfigs.getByName("release")
            ?: signingConfigs.getByName("debug")
    }
}
```

**Issues Identified:**
- Environment variable names did not match GitHub Actions secret names
- Explicit fallback to `signingConfigs.getByName("debug")` for release builds
- No validation that signing credentials were actually present
- CI workflow used `|| echo` to suppress signing failures

### After (Fixed Configuration)

```kotlin
// apps/android/app/build.gradle.kts (AFTER)
signingConfigs {
    create("release") {
        val storeFilePath = System.getenv("ANDROID_KEYSTORE_FILE")
        if (!storeFilePath.isNullOrEmpty() && file(storeFilePath).exists()) {
            storeFile = file(storeFilePath)
            storePassword = System.getenv("ANDROID_KEYSTORE_PASSWORD") ?: ""
            keyAlias = System.getenv("ANDROID_KEY_ALIAS") ?: ""
            keyPassword = System.getenv("ANDROID_KEY_PASSWORD") ?: ""
        }
    }
}

buildTypes {
    release {
        val keystoreEnv = System.getenv("ANDROID_KEYSTORE_FILE")
        signingConfig = if (!keystoreEnv.isNullOrEmpty()) {
            signingConfigs.getByName("release")
        } else {
            null  // No fallback to debug - APK will be unsigned
        }
    }
}
```

**Improvements:**
- Environment variables renamed to match GitHub Actions secrets (ANDROID_KEYSTORE_FILE, ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS, ANDROID_KEY_PASSWORD)
- No debug signing fallback for release builds
- `signingConfig = null` when env vars are not set, producing a truly unsigned APK
- File existence check prevents cryptic errors
- CI workflow validates all secrets before building signed release

---

## 3. CI Workflow Improvements

### GitHub Actions Workflow (.github/workflows/android-release.yml)

**Removed:**
- `|| echo` from lint and test steps (failures now properly fail the workflow)
- `|| true` from any build step
- `continue-on-error` from signing-related steps

**Added:**
- Secret validation step that fails with clear error message when `signed=true` but secrets are missing
- APK verification step using `apksigner verify --print-certs`
- Metadata verification step using `aapt2 dump badging`
- SHA-256 hash generation for artifact integrity
- Unsigned builds labeled as `unsigned-debug` (not presented as release APKs)
- Clear separation between signed release and unsigned development builds

### Environment Variable Mapping

| GitHub Actions Secret | Environment Variable | Purpose |
|---|---|---|
| ANDROID_KEYSTORE_BASE64 | (decoded to file) | Base64-encoded keystore file |
| ANDROID_KEYSTORE_PASSWORD | ANDROID_KEYSTORE_PASSWORD | Keystore password |
| ANDROID_KEY_ALIAS | ANDROID_KEY_ALIAS | Signing key alias |
| ANDROID_KEY_PASSWORD | ANDROID_KEY_PASSWORD | Key password |
| (derived) | ANDROID_KEYSTORE_FILE | Path to decoded keystore file |

---

## 4. Signing Pipeline Architecture

```
GitHub Actions Trigger (workflow_dispatch)
    |
    v
[Secret Validation] -- signed=true required
    |                   All 4 secrets must exist
    v
[Decode Keystore] -- base64 decode ANDROID_KEYSTORE_BASE64
    |                 Write to temp file path
    v
[Set Environment] -- ANDROID_KEYSTORE_FILE=<temp path>
    |                 ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS, ANDROID_KEY_PASSWORD
    v
[Gradle Build] -- ./gradlew :app:assembleRelease
    |
    v
[APK Verification] -- apksigner verify --verbose --print-certs
    |                   aapt2 dump badging
    |                   sha256sum
    v
[Artifact Upload] -- Signed APK with metadata
```

---

## 5. Final Status Report

| Field | Value |
|---|---|
| **ANDROID_SIGNING_STATUS** | Pipeline ready, awaiting production secrets |
| **APK_SIGNATURE_STATUS** | VERIFIED - Signed with APK Signature Scheme v2 (test certificate, non-production) |
| **APK_PACKAGE** | com.sona.ai |
| **APK_VERSION** | 0.2.0-beta |
| **APK_VERSION_CODE** | 2 |
| **CERTIFICATE_SHA256** | f6ff2e4ef6dcae5ee4c12f04c6431defd0b1e03d999e5ba73a787bb29d400f3f |
| **APK_SHA256** | 6b19cf0b60538a256d895f87f349eaf787f4f4894f39a90c9525bb097bda77e1 |
| **APK_SIZE** | 55,779,785 bytes (53.2 MB) |
| **SIGNING_METHOD** | v2 (APK Signature Scheme v2) |
| **PLAY_PROTECT_STATUS** | NOT VERIFIED - requires production certificate + real device testing |
| **SENSITIVE_PERMISSIONS** | INTERNET, RECORD_AUDIO, FOREGROUND_SERVICE, FOREGROUND_SERVICE_MICROPHONE, BLUETOOTH, BLUETOOTH_CONNECT, MODIFY_AUDIO_SETTINGS, POST_NOTIFICATIONS, SYSTEM_ALERT_WINDOW, CAMERA, READ_EXTERNAL_STORAGE (maxSdkVersion=32), BIND_NOTIFICATION_LISTENER_SERVICE, READ_CONTACTS, READ_CALL_LOG, READ_SMS, WAKE_LOCK, ACCESS_NETWORK_STATE |
| **ROOT_CAUSE** | Debug certificate + sideloading (primary), sensitive permissions (secondary) |
| **REMAINING_BLOCKERS** | Production signing secrets not yet configured in GitHub Actions |

### Notes

- The test certificate (CN=CI Test Only, OU=Testing, O=Sona AI) used for validation is NOT a production certificate and was NOT committed to the repository.
- Play Protect verification requires: (1) a production-grade certificate, (2) Google Play App Signing enrollment, (3) testing on a real Android device.
- The signing pipeline is fully functional and will produce properly signed APKs once production secrets (ANDROID_KEYSTORE_BASE64, ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS, ANDROID_KEY_PASSWORD) are configured in GitHub Actions repository secrets.
