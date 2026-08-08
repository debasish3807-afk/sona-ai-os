# Android Release Signing Guide

This document explains how to set up production release signing for the Sona AI Android app.

---

## Table of Contents

1. [Overview](#overview)
2. [Generate a Production Keystore](#generate-a-production-keystore)
3. [Configure GitHub Actions Secrets](#configure-github-actions-secrets)
4. [CI Pipeline Explanation](#ci-pipeline-explanation)
5. [Local Verification](#local-verification)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The Android release signing pipeline uses GitHub Actions secrets to securely sign release APKs without committing any private key material to the repository.

**Required Secrets:**

| Secret Name | Description |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | Base64-encoded keystore file |
| `ANDROID_KEYSTORE_PASSWORD` | Password to open the keystore |
| `ANDROID_KEY_ALIAS` | Alias of the signing key within the keystore |
| `ANDROID_KEY_PASSWORD` | Password for the specific key |

**Security Rules:**
- NEVER commit keystore files (*.jks, *.keystore) to version control
- NEVER hardcode passwords in build scripts or workflow files
- NEVER share keystore credentials in plain text (use a password manager)
- Store a backup of the production keystore in a secure, offline location

---

## Generate a Production Keystore

### Step 1: Generate the Keystore

```bash
keytool -genkeypair \
  -v \
  -keystore sona-ai-production.jks \
  -keyalg RSA \
  -keysize 4096 \
  -validity 10000 \
  -alias sona-ai-release \
  -storepass '<STRONG_STORE_PASSWORD>' \
  -keypass '<STRONG_KEY_PASSWORD>' \
  -dname "CN=Sona AI, OU=Mobile Development, O=Sona AI, L=<City>, ST=<State>, C=<Country>"
```

**Important considerations:**
- Use **RSA 4096-bit** for production (2048 is minimum, 4096 recommended)
- Set **validity to 10000+ days** (27+ years) - Android requires the certificate to be valid beyond the expected app lifetime
- Use **strong, unique passwords** for both store and key passwords
- The **Distinguished Name (DN)** should identify your organization

### Step 2: Verify the Keystore

```bash
keytool -list -v -keystore sona-ai-production.jks -storepass '<STORE_PASSWORD>'
```

Confirm:
- Key algorithm: RSA
- Key size: 4096
- Validity: 10000+ days
- Alias matches what you specified

### Step 3: Back Up the Keystore

Store the keystore file and credentials in at least two secure locations:
- Encrypted password manager (e.g., 1Password, Bitwarden)
- Encrypted USB drive stored securely
- Company key management system

**If you lose the production keystore, you cannot update the app on the Play Store.** There is no recovery mechanism.

---

## Configure GitHub Actions Secrets

### Step 1: Base64 Encode the Keystore

The keystore file must be base64-encoded to be stored as a GitHub secret (secrets are text-only).

**macOS/Linux:**
```bash
base64 -i sona-ai-production.jks | tr -d '\n' > keystore-base64.txt
```

**Alternative (works on all platforms):**
```bash
openssl base64 -in sona-ai-production.jks -out keystore-base64.txt -A
```

### Step 2: Add Secrets to GitHub

1. Navigate to your GitHub repository
2. Go to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret** for each:

| Secret Name | Value |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | Contents of `keystore-base64.txt` |
| `ANDROID_KEYSTORE_PASSWORD` | The keystore password you chose |
| `ANDROID_KEY_ALIAS` | `sona-ai-release` (or your chosen alias) |
| `ANDROID_KEY_PASSWORD` | The key password you chose |

### Step 3: Clean Up

```bash
# Delete the base64 file - it contains your keystore!
rm keystore-base64.txt

# Move the keystore to secure storage
# Do NOT leave it in the repository directory
mv sona-ai-production.jks /path/to/secure/storage/
```

### Step 4: Verify Secrets Are Set

Trigger the release workflow with `signed: true`. The workflow will:
1. Validate all 4 secrets exist (fails immediately if any are missing)
2. Decode the keystore from base64
3. Build the signed APK
4. Verify the signature with `apksigner`

---

## CI Pipeline Explanation

### Workflow Trigger

The release workflow (`.github/workflows/android-release.yml`) is triggered manually via `workflow_dispatch` with an input parameter:

- `signed: false` (default) - Builds an unsigned APK labeled as `unsigned-debug` for development testing
- `signed: true` - Builds a signed release APK using production secrets

### Pipeline Steps (signed=true)

```
1. Checkout code
2. Set up JDK 17
3. Set up Android SDK
4. Validate signing secrets (FAIL if any missing)
5. Decode keystore from ANDROID_KEYSTORE_BASE64
6. Run lint checks
7. Run unit tests
8. Build release APK with signing env vars:
   - ANDROID_KEYSTORE_FILE = path to decoded keystore
   - ANDROID_KEYSTORE_PASSWORD = from secret
   - ANDROID_KEY_ALIAS = from secret
   - ANDROID_KEY_PASSWORD = from secret
9. Verify APK signature (apksigner verify --verbose --print-certs)
10. Verify APK metadata (aapt2 dump badging)
11. Generate SHA-256 hash
12. Upload signed APK as workflow artifact
13. Generate build summary with signing status
```

### How Signing Works in Gradle

The `apps/android/app/build.gradle.kts` signing configuration:

1. Reads `ANDROID_KEYSTORE_FILE` environment variable
2. If set and the file exists, configures the release signing config with all credentials
3. If NOT set, `signingConfig = null` for the release build type
4. No debug key fallback - unsigned builds are explicitly unsigned

This ensures:
- Local development builds without env vars produce unsigned APKs (safe for testing)
- CI builds with secrets produce properly signed APKs
- No accidental debug-signed release APKs

---

## Local Verification

### Verify an APK Signature

```bash
# Full verification with certificate details
/opt/android-sdk/build-tools/35.0.0/apksigner verify --verbose --print-certs app-release.apk

# Quick pass/fail check
/opt/android-sdk/build-tools/35.0.0/apksigner verify app-release.apk
echo $?  # 0 = valid, non-zero = invalid or unsigned
```

### Verify APK Metadata

```bash
# Check package name, version, and permissions
/opt/android-sdk/build-tools/35.0.0/aapt2 dump badging app-release.apk

# Extract specific fields
/opt/android-sdk/build-tools/35.0.0/aapt2 dump badging app-release.apk | grep -E "package:|versionCode|versionName"
```

### Generate SHA-256 Hash

```bash
sha256sum app-release.apk
```

### Build a Signed APK Locally

```bash
cd apps/android

# Set environment variables pointing to your local keystore
export ANDROID_KEYSTORE_FILE=/path/to/your/keystore.jks
export ANDROID_KEYSTORE_PASSWORD=your_store_password
export ANDROID_KEY_ALIAS=your_key_alias
export ANDROID_KEY_PASSWORD=your_key_password

# Build
./gradlew :app:assembleRelease

# Output location
ls -la app/build/outputs/apk/release/app-release.apk
```

---

## Troubleshooting

### "SigningConfig 'release' is missing required property 'storeFile'"

**Cause:** The `ANDROID_KEYSTORE_FILE` environment variable is set but the file does not exist at the specified path.

**Fix:**
- Verify the file path is correct and accessible
- If using CI, ensure the base64 decode step completed successfully
- Check file permissions on the keystore file

### "Failed to read key from store"

**Cause:** Incorrect keystore password, key alias, or key password.

**Fix:**
- Verify `ANDROID_KEYSTORE_PASSWORD` matches the keystore's password
- Verify `ANDROID_KEY_ALIAS` matches an alias in the keystore (`keytool -list -keystore your.jks`)
- Verify `ANDROID_KEY_PASSWORD` matches the key's password

### "Secret validation failed" in CI

**Cause:** One or more GitHub Actions secrets are not configured.

**Fix:**
1. Go to GitHub repository Settings > Secrets and variables > Actions
2. Verify all four secrets exist:
   - `ANDROID_KEYSTORE_BASE64`
   - `ANDROID_KEYSTORE_PASSWORD`
   - `ANDROID_KEY_ALIAS`
   - `ANDROID_KEY_PASSWORD`
3. Ensure secret names match exactly (case-sensitive)

### APK is unsigned after build

**Cause:** `ANDROID_KEYSTORE_FILE` environment variable was not set during the build.

**Fix:**
- For local builds: export the environment variable before running Gradle
- For CI builds: ensure the keystore decode step runs before the build step
- Check that the workflow input `signed` is set to `true`

### Play Protect still blocks after signing

**Cause:** Play Protect uses multiple signals beyond signing:

1. **New certificate** - First-time certificates have no reputation. Solution: distribute through Play Store to build reputation.
2. **Sideload distribution** - APKs not from Play Store are always lower trust. Solution: use Play Store (even internal/closed testing track).
3. **Sensitive permissions** - High-risk permissions raise the risk score. Solution: this is by design for the app's features; cannot be changed without removing functionality.

**What to do:**
- Ensure you are using a production certificate (not debug, not test)
- Submit to Google Play Console (internal testing track is sufficient)
- Enroll in Google Play App Signing
- Wait for certificate reputation to establish (may take multiple update cycles)

### "apksigner: file does not exist"

**Cause:** Android SDK build tools not installed or wrong path.

**Fix:**
```bash
# Find apksigner on your system
find $ANDROID_HOME -name "apksigner" -type f

# Install build-tools if missing
sdkmanager "build-tools;35.0.0"
```

### Keystore file too large for GitHub Secrets

**Cause:** GitHub secrets have a 48KB limit. A standard JKS keystore is well under this limit.

**Fix:**
- Verify you are encoding only the keystore file, not other files
- A typical keystore with one RSA 4096-bit key is approximately 3-4 KB
- If your encoded file is larger, ensure it is the correct file

### Build succeeds but APK is not in expected location

**Default output path:**
```
apps/android/app/build/outputs/apk/release/app-release.apk
```

If not found:
- Check for `app-release-unsigned.apk` (indicates signing was not configured)
- Run `find app/build/outputs -name "*.apk"` to locate all APK outputs
- Ensure you ran `:app:assembleRelease` (not `assembleDebug`)
