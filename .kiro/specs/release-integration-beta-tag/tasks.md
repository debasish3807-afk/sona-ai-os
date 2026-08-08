# Implementation Plan: Release Integration — Merge, Regression & Beta Tag (v0.2.0-beta)

## Overview

This implementation plan covers the complete release integration process for Sona AI OS v0.2.0-beta. The work is organized into 9 sequential phases, each gated by quality checks. No new features are introduced — scope is limited to merge integration, regression validation, and release preparation.

**Total Estimated Duration**: ~5 hours 47 minutes (347 minutes nominal)
**Retry Budget**: Backend 5 cycles | Android 3 cycles | CI 5 per workflow
**Rollback Levels**: L1 (PR revert) → L2 (partial) → L3 (branch abandon) → L4 (tag delete) → L5 (release retract)

## Tasks


- [ ] 1. Phase 1 — Branch & Merge Preparation (~3 min)
  - [ ] 1.1 Create integration branch from main HEAD
    - Run `git fetch origin main` to ensure local main is up to date
    - Run `git checkout -b release/v0.2.0-beta origin/main` to create integration branch
    - Verify branch creation with `git branch --show-current`
    - Record the base commit SHA (full 40-char) for the Merge Report
    - **Est. Duration**: 1 min
    - _Requirements: 1.1_

  - [ ] 1.2 Fetch all PR refs (#67–#76)
    - Run `git fetch origin pull/{N}/head:pr-{N}` for each N in 67..76
    - Verify each ref is available locally with `git rev-parse pr-{N}`
    - Record each PR HEAD SHA for ancestry verification later
    - **Est. Duration**: 2 min
    - _Requirements: 1.1, 1.6_

  - [ ] 1.3 Pre-flight validation checks
    - Verify tag `v0.2.0-beta` does NOT already exist: `git rev-parse v0.2.0-beta 2>/dev/null` should fail
    - Verify required tools are available: `ruff --version`, `mypy --version`, `pytest --version`
    - Query each PR state via `gh api repos/{owner}/{repo}/pulls/{N}` to identify draft/closed/failing PRs
    - Document any PRs that will be skipped per skip policy (draft, closed, failing required checks)
    - **Est. Duration**: 2 min
    - _Requirements: 1.4, 7.4_


- [ ] 2. Phase 2 — Merge PRs #67–#76 (~53 min)
  - [ ] 2.1 Merge PR #67 into integration branch
    - Check PR state (open/closed/draft) — skip if not mergeable per policy
    - Run `git merge --no-ff pr-67 -m "Merge PR #67: <title>"`
    - If conflict: resolve preserving both sides, never remove function signatures/return values/control flow
    - Verify ancestry: `git merge-base --is-ancestor <pr-67-HEAD> HEAD`
    - Record merge status (merged/skipped/conflicted-and-resolved) for Merge Report
    - **Est. Duration**: 3 min (+ conflict resolution time if needed)
    - _Requirements: 1.2, 1.3, 1.4, 1.6_

  - [ ] 2.2 Merge PR #68 into integration branch
    - Check PR state — skip if not mergeable per policy
    - Run `git merge --no-ff pr-68 -m "Merge PR #68: <title>"`
    - If conflict: resolve preserving both sides per conflict resolution rules
    - Verify ancestry: `git merge-base --is-ancestor <pr-68-HEAD> HEAD`
    - Record merge status for Merge Report
    - **Est. Duration**: 3 min
    - _Requirements: 1.2, 1.3, 1.4, 1.6_

  - [ ] 2.3 Merge PR #69 into integration branch
    - Check PR state — skip if not mergeable per policy
    - Run `git merge --no-ff pr-69 -m "Merge PR #69: <title>"`
    - If conflict: resolve preserving both sides per conflict resolution rules
    - Verify ancestry: `git merge-base --is-ancestor <pr-69-HEAD> HEAD`
    - Record merge status for Merge Report
    - **Est. Duration**: 3 min
    - _Requirements: 1.2, 1.3, 1.4, 1.6_

  - [ ] 2.4 Merge PR #70 into integration branch
    - Check PR state — skip if not mergeable per policy
    - Run `git merge --no-ff pr-70 -m "Merge PR #70: <title>"`
    - If conflict: resolve preserving both sides per conflict resolution rules
    - Verify ancestry: `git merge-base --is-ancestor <pr-70-HEAD> HEAD`
    - Record merge status for Merge Report
    - **Est. Duration**: 3 min
    - _Requirements: 1.2, 1.3, 1.4, 1.6_

  - [ ] 2.5 Merge PR #71 into integration branch
    - Check PR state — skip if not mergeable per policy
    - Run `git merge --no-ff pr-71 -m "Merge PR #71: <title>"`
    - If conflict: resolve preserving both sides per conflict resolution rules
    - Verify ancestry: `git merge-base --is-ancestor <pr-71-HEAD> HEAD`
    - Record merge status for Merge Report
    - **Est. Duration**: 3 min
    - _Requirements: 1.2, 1.3, 1.4, 1.6_


  - [ ] 2.6 Merge PR #72 into integration branch
    - Check PR state — skip if not mergeable per policy
    - Run `git merge --no-ff pr-72 -m "Merge PR #72: <title>"`
    - If conflict: resolve preserving both sides per conflict resolution rules
    - Verify ancestry: `git merge-base --is-ancestor <pr-72-HEAD> HEAD`
    - Record merge status for Merge Report
    - **Est. Duration**: 3 min
    - _Requirements: 1.2, 1.3, 1.4, 1.6_

  - [ ] 2.7 Merge PR #73 into integration branch
    - Check PR state — skip if not mergeable per policy
    - Run `git merge --no-ff pr-73 -m "Merge PR #73: <title>"`
    - If conflict: resolve preserving both sides per conflict resolution rules
    - Verify ancestry: `git merge-base --is-ancestor <pr-73-HEAD> HEAD`
    - Record merge status for Merge Report
    - **Est. Duration**: 3 min
    - _Requirements: 1.2, 1.3, 1.4, 1.6_

  - [ ] 2.8 Merge PR #74 into integration branch
    - Check PR state — skip if not mergeable per policy
    - Run `git merge --no-ff pr-74 -m "Merge PR #74: <title>"`
    - If conflict: resolve preserving both sides per conflict resolution rules
    - Verify ancestry: `git merge-base --is-ancestor <pr-74-HEAD> HEAD`
    - Record merge status for Merge Report
    - **Est. Duration**: 3 min
    - _Requirements: 1.2, 1.3, 1.4, 1.6_

  - [ ] 2.9 Merge PR #75 into integration branch
    - Check PR state — skip if not mergeable per policy
    - Run `git merge --no-ff pr-75 -m "Merge PR #75: <title>"`
    - If conflict: resolve preserving both sides per conflict resolution rules
    - Verify ancestry: `git merge-base --is-ancestor <pr-75-HEAD> HEAD`
    - Record merge status for Merge Report
    - **Est. Duration**: 3 min
    - _Requirements: 1.2, 1.3, 1.4, 1.6_

  - [ ] 2.10 Merge PR #76 into integration branch
    - Check PR state — skip if not mergeable per policy
    - Run `git merge --no-ff pr-76 -m "Merge PR #76: <title>"`
    - If conflict: resolve preserving both sides per conflict resolution rules
    - Verify ancestry: `git merge-base --is-ancestor <pr-76-HEAD> HEAD`
    - Record merge status for Merge Report
    - **Est. Duration**: 3 min
    - _Requirements: 1.2, 1.3, 1.4, 1.6_


  - [ ] 2.11 Generate Merge Report
    - Create `reports/merge-report.md` documenting for each PR (#67–#76): PR number, title, merge status, conflicting files, resolution approach, skip reason
    - Include summary: total PRs targeted (10), merged count, skipped count, conflicted-and-resolved count
    - Include base commit SHA and integration branch HEAD SHA
    - **Est. Duration**: 5 min
    - _Requirements: 1.5_

  - [ ] 2.12 Phase 2 Quality Gate — Merge Integrity Verification
    - Run ancestry verification for ALL merged PRs: `git merge-base --is-ancestor <PR-HEAD> HEAD`
    - Confirm every targeted PR is either merged or explicitly documented as skipped
    - Run quick backend validation: `ruff check services/ libs/ gateway/` to catch obvious merge issues
    - **Rollback Checkpoint**: If >3 PRs have irreconcilable conflicts, trigger L3 rollback (branch abandon)
    - **Est. Duration**: 3 min
    - _Requirements: 1.6, 1.7_


- [ ] 3. Phase 3 — Backend Regression Validation (~46 min)
  - [ ] 3.1 Run Ruff linting across Python monorepo
    - Execute from repo root: `ruff check services/ libs/ gateway/`
    - Target: zero violations
    - If violations found: auto-fix with `ruff check --fix services/ libs/ gateway/`, commit fixes, re-check
    - Record: number of files checked, violations found, violations auto-fixed
    - **Est. Duration**: 2 min
    - _Requirements: 2.1_

  - [ ] 3.2 Run Ruff format check across Python monorepo
    - Execute from repo root: `ruff format --check services/ libs/ gateway/`
    - Target: zero formatting violations
    - If violations found: auto-fix with `ruff format services/ libs/ gateway/`, commit fixes, re-check
    - Record: number of files checked, formatting violations found
    - **Est. Duration**: 1 min
    - _Requirements: 2.2_

  - [ ] 3.3 Run MyPy strict type checking
    - Execute from repo root: `mypy services/ libs/ gateway/ --strict --ignore-missing-imports --exclude "tests/" --exclude "backend/"`
    - Target: zero type errors
    - If errors found: fix type annotations on integration branch, commit, re-run (retry ≤5)
    - Record: number of files checked, type errors found per retry
    - **Est. Duration**: 5 min (+ retry time)
    - _Requirements: 2.3_

  - [ ] 3.4 Run Pytest per-service across all backend services
    - For each service in `services/*/`: `cd $service && pytest tests/ -v --tb=short --cov --cov-fail-under=50`
    - For each lib in `libs/*/`: `cd $lib && pytest tests/ -v --tb=short`
    - For gateway: `cd gateway && pytest tests/ -v --tb=short --cov --cov-fail-under=50`
    - Target: 100% pass rate, ≥50% coverage per service
    - If failures: debug, fix on integration branch, commit, re-run full suite (retry ≤5)
    - Record: total tests executed, passed, failed, pass rate %, coverage %
    - **Est. Duration**: 20 min (+ retry time)
    - _Requirements: 2.4, 2.5_


  - [ ] 3.5 Backend fix & retry cycle (if needed)
    - If any of tasks 3.1–3.4 failed: apply targeted fixes on integration branch
    - Commit fixes with message: `fix: resolve backend regression [retry N/5]`
    - Re-run the complete backend validation suite (Ruff lint → Ruff format → MyPy → Pytest)
    - Maximum 5 retry cycles total across all backend validation steps
    - **Est. Duration**: 15 min (per retry cycle)
    - _Requirements: 2.5_

  - [ ] 3.6 Generate Backend Regression Report section
    - Record tool versions: ruff, mypy, pytest
    - Record per-tool results: status (pass/fail), files checked, violations/errors
    - Record pytest summary: total tests, passed, failed, pass rate %, coverage %
    - Record retry count used
    - Write results to `reports/regression-report.md` (backend section)
    - **Est. Duration**: 3 min
    - _Requirements: 2.6_

  - [ ] 3.7 Phase 3 Quality Gate — Backend Validation Pass
    - Confirm: Ruff lint = 0 violations, Ruff format = 0 violations, MyPy = 0 errors, Pytest = 100% pass rate with ≥50% coverage
    - If maximum 5 retries exhausted without pass: HALT release, record in report, issue NO-GO
    - **Rollback Checkpoint**: If halt triggered, evaluate L2 partial rollback (revert specific problematic PRs)
    - **Est. Duration**: 2 min
    - _Requirements: 2.5, 2.6, 2.7_


- [ ] 4. Phase 4 — Android Client Validation (~67 min)
  - [ ] 4.1 Run Android debug build (both projects)
    - Execute in `android/`: `./gradlew assembleDebug` (timeout: 10 min)
    - Execute in `apps/android/`: `./gradlew assembleDebug` (timeout: 10 min)
    - Target: both builds complete with zero errors
    - Record: build duration, success/failure status per project
    - **Est. Duration**: 15 min
    - _Requirements: 3.1_

  - [ ] 4.2 Run Android release build (both projects)
    - Execute in `android/`: `./gradlew assembleRelease` (timeout: 15 min)
    - Execute in `apps/android/`: `./gradlew assembleRelease` (timeout: 15 min)
    - Target: both builds complete with zero errors
    - Record: build duration, success/failure status per project
    - Retain release APK artifact for GitHub Release attachment
    - **Est. Duration**: 20 min
    - _Requirements: 3.2_

  - [ ] 4.3 Run Android Lint (both projects)
    - Execute in `android/`: `./gradlew lint`
    - Execute in `apps/android/`: `./gradlew lint`
    - Target: zero errors, zero new warnings compared to baseline
    - Record: error count, warning count per project
    - **Est. Duration**: 5 min
    - _Requirements: 3.3_

  - [ ] 4.4 Run Android unit tests (both projects)
    - Execute in `android/`: `./gradlew test` (timeout: 10 min)
    - Execute in `apps/android/`: `./gradlew test` (timeout: 10 min)
    - Target: 100% pass rate across both projects
    - Record: total tests, passed, failed, pass rate %, duration
    - **Est. Duration**: 12 min
    - _Requirements: 3.4_

  - [ ] 4.5 Run Android instrumentation tests (both projects)
    - Execute in `android/`: `./gradlew connectedAndroidTest` (timeout: 20 min)
    - Execute in `apps/android/`: `./gradlew connectedAndroidTest` (timeout: 20 min)
    - Target: 100% pass rate
    - If emulator/device unavailable: mark as BLOCKED (not FAILED), document in report
    - Record: total tests, passed, failed, pass rate %, duration, infrastructure status
    - **Est. Duration**: 30 min
    - _Requirements: 3.5, 3.7_


  - [ ] 4.6 Android fix & retry cycle (if needed)
    - If any of tasks 4.1–4.5 failed (not BLOCKED): apply targeted fixes on integration branch
    - Commit fixes with message: `fix: resolve android regression [retry N/3]`
    - Re-run the full Android validation sequence (debug build → release build → lint → unit tests → instrumentation)
    - Maximum 3 re-validation attempts before escalation
    - **Est. Duration**: 30 min (per retry cycle)
    - _Requirements: 3.6_

  - [ ] 4.7 Generate Android Regression Report section
    - Record per-project (android/, apps/android/): debug build status, release build status, lint error/warning counts
    - Record: total unit test count, unit test pass rate, total instrumentation test count, instrumentation test pass rate
    - Record: total validation duration, integration branch commit SHA
    - Append results to `reports/regression-report.md` (Android section)
    - **Est. Duration**: 3 min
    - _Requirements: 3.8_

  - [ ] 4.8 Phase 4 Quality Gate — Android Validation Pass
    - Confirm: both debug builds pass, both release builds pass, lint = 0 errors, unit tests = 100% pass, instrumentation tests = 100% pass (or BLOCKED)
    - If maximum 3 retries exhausted without pass: ESCALATE, document failure
    - **Rollback Checkpoint**: If escalation triggered, evaluate L1 rollback (revert specific PR causing Android failure)
    - **Est. Duration**: 2 min
    - _Requirements: 3.6, 3.7, 3.8_


- [ ] 5. Phase 5 — Integration Subsystem Validation (~50 min)
  - [ ] 5.1 Validate Voice subsystem
    - Import top-level module from `services/ai-kernel` (or `android/voice`)
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests in subsystem test directory (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.2 Validate Vision subsystem
    - Import top-level module from `apps/android/features/vision`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests in subsystem test directory (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.3 Validate Dashboard subsystem
    - Import top-level module from `apps/android/features/dashboard`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.4 Validate Communication subsystem
    - Import top-level module from `apps/android/features/communication`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.5 Validate Connectors subsystem
    - Import top-level module from `apps/android/features/connectors`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_


  - [ ] 5.6 Validate Memory subsystem
    - Import top-level module from `services/memory-os`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.7 Validate Knowledge subsystem
    - Import top-level module from `services/knowledge-os`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.8 Validate Agents subsystem
    - Import top-level module from `services/workforce-os`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.9 Validate GitHub Integration subsystem
    - Import top-level module from `services/mcp-integration`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.10 Validate Google Integration subsystem
    - Import top-level module from `services/mcp-integration` (Google integration path)
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_


  - [ ] 5.11 Validate Offline Mode subsystem
    - Import top-level module from `apps/android/core` (offline mode component)
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.12 Validate Notifications subsystem
    - Import top-level module from `apps/android/features` (notifications component)
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.13 Validate Widgets subsystem
    - Import top-level module from `android/widgets`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.14 Validate Overlay subsystem
    - Import top-level module from `apps/android/features/overlay`
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_

  - [ ] 5.15 Validate Quick Settings Tile subsystem
    - Import top-level module from `apps/android/features` (quick settings tile component)
    - Invoke initialization entry point — confirm no unhandled exception within 60 seconds
    - Run integration tests (if present)
    - Record: pass/fail, integration tests executed, tests passed, timestamp
    - **Est. Duration**: 3 min
    - _Requirements: 4.1, 4.2_


  - [ ] 5.16 Fix or revert failed subsystems
    - For each failed subsystem: identify the failing PR, attempt fix within 30 minutes
    - If fix successful: commit with `fix: resolve <subsystem> validation failure`, re-run that subsystem validation
    - If cannot fix within 30 min: revert failing PR with `git revert -m 1 <merge-commit-sha> --no-edit`
    - Document revert reason and impacted PR in Regression Report
    - **Est. Duration**: 15 min (per failed subsystem)
    - _Requirements: 4.3, 4.4_

  - [ ] 5.17 Phase 5 Quality Gate — Subsystem Integration Pass
    - Confirm: all 15 subsystems pass validation OR are documented as "no integration tests available"
    - Record per-subsystem in Regression Report: name, pass/fail, tests executed, tests passed, timestamp, reverted PRs
    - **Rollback Checkpoint**: If >3 subsystems fail and cannot be fixed, evaluate L2 partial rollback
    - **Est. Duration**: 3 min
    - _Requirements: 4.5_


- [ ] 6. Checkpoint — All Regression Validations Complete
  - Ensure all tests pass, ask the user if questions arise.
  - Verify: Backend validation passed (Ruff, MyPy, Pytest), Android validation passed (builds, lint, tests), all subsystems validated
  - Confirm integration branch is stable and ready for CI/CD verification

- [ ] 7. Phase 6 — CI/CD Pipeline Verification (~46 min)
  - [ ] 7.1 Push integration branch to remote
    - Run `git push origin release/v0.2.0-beta`
    - Verify push succeeded and branch is visible on GitHub
    - Record push timestamp and commit SHA
    - **Est. Duration**: 2 min
    - _Requirements: 5.1_

  - [ ] 7.2 Verify CI Monorepo Pipeline (ci-monorepo.yml) execution
    - Check if workflow auto-triggered on push; if not, trigger via `workflow_dispatch`
    - Monitor workflow: all jobs must complete with "success" conclusion within 30 min
    - Track jobs: detect-changes → backend-lint → backend-test
    - If failure: diagnose, fix on integration branch, push fix, re-trigger (retry ≤5)
    - Record: run ID, trigger commit SHA, per-job status, total duration
    - **Est. Duration**: 25 min
    - _Requirements: 5.1, 5.3_

  - [ ] 7.3 Verify CI Legacy Pipeline (ci.yml) execution
    - Check if workflow auto-triggered (only fires on `backend/**` path changes)
    - If not auto-triggered and backend changes exist: trigger via `workflow_dispatch`
    - If no backend path changes: document as "not triggered — no qualifying path changes"
    - Monitor if triggered: all jobs must complete with "success" within 30 min
    - Record: run ID or "not triggered" status, per-job status, total duration
    - **Est. Duration**: 5 min (monitoring only if triggered)
    - _Requirements: 5.1, 5.3_


  - [ ] 7.4 Trigger and verify Deploy Development workflow (deploy-dev.yml)
    - Trigger via `workflow_dispatch` targeting the integration branch
    - Monitor: all jobs (ci-gate, build, deploy, verify) must complete with "success" within 20 min
    - If failure: diagnose, fix on integration branch, re-trigger (retry ≤5)
    - Record: run ID, trigger commit SHA, per-job status (ci-gate, build, deploy, verify), total duration
    - **Est. Duration**: 18 min
    - _Requirements: 5.2, 5.3_

  - [ ] 7.5 Generate CI Report
    - Create `reports/ci-report.md` documenting all workflow runs
    - Include per workflow: name, file, run ID, trigger commit SHA, conclusion, per-job status, total duration, re-trigger count
    - Note: `deploy-prod.yml` is NOT triggered (tag pattern `v[0-9]+.[0-9]+.[0-9]+` does not match `v0.2.0-beta`)
    - **Est. Duration**: 3 min
    - _Requirements: 5.4_

  - [ ] 7.6 Phase 6 Quality Gate — CI/CD Pipeline Pass
    - Confirm: ci-monorepo.yml = success, ci.yml = success (or not triggered), deploy-dev.yml = success
    - If maximum 5 retries exhausted per workflow: document as known issue, evaluate impact on release
    - **Rollback Checkpoint**: CI failures typically indicate code issues — may need to revert last fix commit
    - **Est. Duration**: 2 min
    - _Requirements: 5.1, 5.2, 5.3, 5.4_


- [ ] 8. Phase 7 — Release Artifacts (Version Bump, Release Notes, Changelog, Migration) (~32 min)
  - [ ] 8.1 Bump version in pyproject.toml
    - Update `project.version` field from `1.0.0-rc1` to `0.2.0-beta` in root `pyproject.toml`
    - Verify with `grep` that new version string is correct
    - **Est. Duration**: 1 min
    - _Requirements: 6.1_

  - [ ] 8.2 Bump version in android/app/build.gradle.kts
    - Update `versionName` from `1.0.0-rc1` to `0.2.0-beta`
    - Verify with `grep` that new version string is correct
    - **Est. Duration**: 1 min
    - _Requirements: 6.1_

  - [ ] 8.3 Bump version in apps/android/app/build.gradle.kts
    - Update `versionName` from `0.1.0-beta` to `0.2.0-beta`
    - Verify with `grep` that new version string is correct
    - **Est. Duration**: 1 min
    - _Requirements: 6.1_

  - [ ] 8.4 Bump version in backend API constants
    - Locate `API_VERSION` or `app_version` setting in backend code
    - Update to `0.2.0-beta`
    - Verify with `grep` that new version string is correct
    - **Est. Duration**: 1 min
    - _Requirements: 6.1_

  - [ ] 8.5 Verify version consistency across all config files
    - Run grep verification: confirm `0.2.0-beta` appears in all 4 target files
    - Confirm no other version strings remain that conflict
    - **Est. Duration**: 1 min
    - _Requirements: 6.1_


  - [ ] 8.6 Generate RELEASE_NOTES.md
    - Create `RELEASE_NOTES.md` in repository root with sections: Summary, New Capabilities (one entry per PR with user-facing features), Improvements, Known Limitations
    - Reference each PR in range #67–#76 with `#<number>` format
    - Summarize new capabilities from merged PRs
    - **Est. Duration**: 10 min
    - _Requirements: 6.2, 6.5_

  - [ ] 8.7 Generate CHANGELOG.md entry
    - Add `## [v0.2.0-beta] - <date>` section to `CHANGELOG.md` in Keep a Changelog format
    - Include sections: Added, Changed, Fixed, Deprecated
    - Each item must reference at least one PR number from #67–#76
    - Internal/infrastructure PRs noted as such
    - **Est. Duration**: 10 min
    - _Requirements: 6.3, 6.5, 6.6_

  - [ ] 8.8 Generate MIGRATION.md
    - Create `MIGRATION.md` in repository root documenting upgrade from `1.0.0-rc1` to `v0.2.0-beta`
    - Include: breaking changes, new environment variables, configuration changes
    - Each breaking change must include the action required by the user
    - **Est. Duration**: 8 min
    - _Requirements: 6.4, 6.5_

  - [ ] 8.9 Commit version bump and release documentation
    - Stage all modified files: pyproject.toml, build.gradle.kts (x2), backend API constants, RELEASE_NOTES.md, CHANGELOG.md, MIGRATION.md
    - Commit with message: `release: bump version to v0.2.0-beta and add release documentation`
    - Push to remote: `git push origin release/v0.2.0-beta`
    - **Est. Duration**: 2 min
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 8.10 Phase 7 Quality Gate — Release Artifacts Complete
    - Verify all 4 version files contain `0.2.0-beta`
    - Verify RELEASE_NOTES.md, CHANGELOG.md, MIGRATION.md exist and reference all PRs #67–#76
    - Verify every PR in range is referenced in at least one of the three documents
    - **Est. Duration**: 2 min
    - _Requirements: 6.1, 6.5_


- [ ] 9. Phase 8 — Git Tag & GitHub Release (~9 min)
  - [ ] 9.1 Verify tag does not already exist
    - Run `git rev-parse v0.2.0-beta 2>/dev/null` — must fail (tag should not exist)
    - If tag exists: HALT immediately, report error with existing tag's commit SHA
    - **Est. Duration**: 1 min
    - _Requirements: 7.4_

  - [ ] 9.2 Create annotated Git tag v0.2.0-beta
    - Create tag on integration branch HEAD: `git tag -a v0.2.0-beta -m "<annotation>"`
    - Annotation must include: version (`v0.2.0-beta`), date (ISO 8601), full 40-char commit SHA, bulleted list of merged PR titles with numbers
    - Verify tag: `git describe --exact-match HEAD` must return `v0.2.0-beta`
    - **Est. Duration**: 2 min
    - _Requirements: 7.1, 7.2_

  - [ ] 9.3 Push tag to remote
    - Run `git push origin v0.2.0-beta`
    - Verify tag is visible on GitHub
    - **Rollback Checkpoint**: If post-tag issue discovered, L4 rollback: `git tag -d v0.2.0-beta && git push --delete origin v0.2.0-beta`
    - **Est. Duration**: 1 min
    - _Requirements: 7.1_

  - [ ] 9.4 Create GitHub Release draft
    - Create release via `gh api repos/{owner}/{repo}/releases` with: tag_name=`v0.2.0-beta`, name=`v0.2.0-beta`, body=changelog+summary, prerelease=true, draft=true
    - Attach signed release APK artifact from Android release build
    - Verify release draft is visible on GitHub
    - **Rollback Checkpoint**: If release retraction needed, L5 rollback: delete GitHub Release + delete tag
    - **Est. Duration**: 3 min
    - _Requirements: 7.3_

  - [ ] 9.5 Generate Git Tag Report
    - Create `reports/git-tag-report.md` documenting: tag name, tagged commit SHA (full 40-char), tag author, tag timestamp (ISO 8601), list of PRs included since last tagged release
    - **Est. Duration**: 2 min
    - _Requirements: 7.5_


- [ ] 10. Phase 9 — Beta Readiness Certification (~14 min)
  - [ ] 10.1 Aggregate all phase reports
    - Collect: Merge Report, Backend Regression Report, Android Regression Report, Subsystem Validation results, CI Report, Git Tag Report
    - Verify internal consistency across reports (commit SHAs match, timestamps are sequential)
    - **Est. Duration**: 5 min
    - _Requirements: 8.1_

  - [ ] 10.2 Evaluate all quality gates
    - Check each gate (PASS/FAIL): no unresolved merge conflicts, zero backend test failures, zero Android unit test failures, all CI workflows passing, zero Ruff violations, zero MyPy errors, no application crashes during tests, release builds successful (backend, Android debug, Android release)
    - For each FAIL: document gate name, failure description, identified cause, remediation applied or unresolved status
    - **Est. Duration**: 3 min
    - _Requirements: 8.2, 8.4_

  - [ ] 10.3 Generate Beta Readiness Report
    - Create `reports/beta-readiness-report.md` with:
    - Summary table: total PRs merged (out of 10), total backend tests, total Android tests, test pass rate %, Ruff violations, MyPy errors, build statuses (PASS/FAIL for each target), CI statuses
    - Quality gates section: each gate with PASS/FAIL status
    - Failed gates section (if any): gate name, failure, cause, remediation
    - **Est. Duration**: 5 min
    - _Requirements: 8.2, 8.3, 8.4_

  - [ ] 10.4 Issue GO/NO-GO recommendation
    - If ALL quality gates = PASS: issue "GO" recommendation for releasing v0.2.0-beta
    - If ANY quality gate = FAIL with no successful remediation: issue "NO-GO" with rationale
    - Record recommendation and rationale in Beta Readiness Report
    - **Est. Duration**: 1 min
    - _Requirements: 8.5_

- [ ] 11. Final Checkpoint — Release Integration Complete
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all reports generated: merge-report.md, regression-report.md, ci-report.md, git-tag-report.md, beta-readiness-report.md
  - Verify all release documents committed: RELEASE_NOTES.md, CHANGELOG.md, MIGRATION.md
  - Verify tag `v0.2.0-beta` exists and GitHub Release draft is created
  - Confirm GO/NO-GO status


## Notes

- This is a **release engineering process** — NO new features, ONLY stabilization and release preparation
- Tasks are strictly sequential by phase due to hard gate dependencies (each phase must pass before the next begins)
- Within Phase 2 (PR merges), tasks 2.1–2.10 MUST be sequential (numerical order per requirements)
- Within Phase 5 (subsystem validation), tasks 5.1–5.15 can run in parallel (independent subsystems)
- Retry budgets are cumulative per phase: Backend = 5 total, Android = 3 total, CI = 5 per workflow
- Rollback checkpoints are placed at phase boundaries for safe abort points
- If halt/escalation occurs, the Beta Readiness Report is still generated with NO-GO recommendation
- The `deploy-prod.yml` workflow is intentionally NOT triggered — its tag pattern doesn't match `v0.2.0-beta`
- Instrumentation tests marked BLOCKED (not FAILED) do not block the release
- All reports use both Markdown (human-readable) and JSON (machine-parseable) formats
- Per the design, this process is idempotent — phases can be safely re-executed
- Estimated total duration: ~5h 47m nominal, ~4h 30m best case, ~8h worst case


## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["2.1"] },
    { "id": 4, "tasks": ["2.2"] },
    { "id": 5, "tasks": ["2.3"] },
    { "id": 6, "tasks": ["2.4"] },
    { "id": 7, "tasks": ["2.5"] },
    { "id": 8, "tasks": ["2.6"] },
    { "id": 9, "tasks": ["2.7"] },
    { "id": 10, "tasks": ["2.8"] },
    { "id": 11, "tasks": ["2.9"] },
    { "id": 12, "tasks": ["2.10"] },
    { "id": 13, "tasks": ["2.11"] },
    { "id": 14, "tasks": ["2.12"] },
    { "id": 15, "tasks": ["3.1"] },
    { "id": 16, "tasks": ["3.2"] },
    { "id": 17, "tasks": ["3.3"] },
    { "id": 18, "tasks": ["3.4"] },
    { "id": 19, "tasks": ["3.5"] },
    { "id": 20, "tasks": ["3.6"] },
    { "id": 21, "tasks": ["3.7"] },
    { "id": 22, "tasks": ["4.1", "4.2"] },
    { "id": 23, "tasks": ["4.3", "4.4"] },
    { "id": 24, "tasks": ["4.5"] },
    { "id": 25, "tasks": ["4.6"] },
    { "id": 26, "tasks": ["4.7"] },
    { "id": 27, "tasks": ["4.8"] },
    { "id": 28, "tasks": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9", "5.10", "5.11", "5.12", "5.13", "5.14", "5.15"] },
    { "id": 29, "tasks": ["5.16"] },
    { "id": 30, "tasks": ["5.17"] },
    { "id": 31, "tasks": ["7.1"] },
    { "id": 32, "tasks": ["7.2", "7.3"] },
    { "id": 33, "tasks": ["7.4"] },
    { "id": 34, "tasks": ["7.5"] },
    { "id": 35, "tasks": ["7.6"] },
    { "id": 36, "tasks": ["8.1", "8.2", "8.3", "8.4"] },
    { "id": 37, "tasks": ["8.5"] },
    { "id": 38, "tasks": ["8.6", "8.7", "8.8"] },
    { "id": 39, "tasks": ["8.9"] },
    { "id": 40, "tasks": ["8.10"] },
    { "id": 41, "tasks": ["9.1"] },
    { "id": 42, "tasks": ["9.2"] },
    { "id": 43, "tasks": ["9.3"] },
    { "id": 44, "tasks": ["9.4", "9.5"] },
    { "id": 45, "tasks": ["10.1"] },
    { "id": 46, "tasks": ["10.2"] },
    { "id": 47, "tasks": ["10.3"] },
    { "id": 48, "tasks": ["10.4"] }
  ]
}
```
