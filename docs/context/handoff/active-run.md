# Active run

## Run metadata

Mode: `NON_AUTONOMOUS`
Thread title: `TASK-005 - Android TV limited install/launch/focus smoke on Philips new`
Thread status: `blocked_preflight`
Fresh thread verified: `fresh TASK-005 worktree/thread delegated from source thread`
Task ID: `TASK-005`
Task branch: `qa/task-005-android-tv-smoke`
Default branch: `main`
Base commit: `a7d983d`
Merge/push authority: `NON_AUTONOMOUS; default branch merge/push forbidden without explicit user command`
Production safety classification:

- `PROD_SAFE` for repository/source-of-truth reads, branch setup, local path checks and docs updates.
- `PROD_CONDITIONAL` for Android device/APK install/launch/logcat/screenshot observation, allowed only after local preflight confirms the selected APK and selected public-safe target.

## Goal

Prepare and, if gates pass, execute the minimal TASK-005 limited runtime smoke
for the owner-selected Philips new target represented publicly as
`tv-tpv-013` / `tv-tpv-a12-013`.

The run stopped before any device interaction because local preflight did not
find the selected TASK-005 APK directory in this worktree and `adb` was not
available in PATH.

## Allowed scope

- local source-of-truth and approval docs review;
- task branch creation from detected default branch;
- local ignored APK/evidence path checks;
- local ADB tooling availability check;
- blocked evidence note under ignored `.qa_local/evidence/task-005/`;
- public-safe documentation updates.

## Runtime scope that did not run

- APK install/update;
- uninstall+install on install conflict;
- app launch;
- first visible state observation;
- initial focus observation;
- minimal D-pad navigation;
- Back/Home;
- background/foreground;
- force-stop/relaunch;
- crash/ANR logcat observation;
- screenshots, videos or raw log capture.

## Forbidden actions

- source code, decompiled code, smali or method bodies;
- APK patching, resigning, decompilation or modification;
- TLS/security bypass;
- private endpoint extraction;
- secrets, tokens, production credentials or real user data;
- real payments, subscription, purchase or billing flows;
- WebView, redirect, WebRTC, stream or media playback scope;
- production mutation or destructive production actions;
- raw device identifiers, raw IP addresses, raw screenshots, raw logs or raw
  videos in public docs.

## Acceptance criteria

- Mode is declared as `NON_AUTONOMOUS`.
- Task branch is created from detected default branch `main`.
- Multi-agent delegation is used when available.
- APK presence is checked before runtime.
- Device/tooling preflight runs only inside approved conditional scope.
- If APK/tooling/device identity gates fail, runtime stops before install or
  launch.
- Evidence remains redaction-by-default and raw/local-only under ignored
  `.qa_local/evidence/task-005/`.
- Public docs use only public aliases for the selected target.

## Verification plan

Required commands for this blocked run:

```text
git status --short --branch
git remote show origin
git switch -c qa/task-005-android-tv-smoke origin/main
Get-ChildItem .qa_local/apks/task-005
Get-Command adb
git diff --check
python -m pytest -q
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
```

Runtime/device checks are blocked until the selected APK exists in this
worktree and ADB tooling is available.

## Current evidence status

- TASK-005 runtime execution: `blocked`
- Selected target identity confirmation: `not_run`
- APK directory presence in this worktree: `blocked_missing`, evidence status `confirmed`
- ADB tooling availability in PATH: `blocked_not_found`, evidence status `confirmed`
- APK install/app launch/logcat/screenshots/videos: `not_run`
- WebView/WebRTC/payment/stream/media playback: `out_of_scope`
- Local blocked evidence note: `.qa_local/evidence/task-005/task005_preflight_blocked_public_safe.json`
- Diff check: `passed`
- Full-tree hygiene: `passed`
- Compileall: `passed`
- Full pytest: `385 passed`

## Multi-agent status

- Orchestrator: `blocked_preflight_finalized`
- Planner: `PASS_READ_ONLY_PLAN`
- Security/Prod-safety Reviewer: `PASS_WITH_CONDITIONS`
- Builder: `PASS_READ_ONLY_BLOCKED_PREFLIGHT_RECOMMENDATION`
- QA Reviewer A: `PASS_AFTER_REMEDIATION`
- QA Reviewer B: `PASS_FINAL_REVIEW`
- Docs/Scribe: `PASS_AFTER_REMEDIATION`
- Subagent closure audit: `ready_for_closure`; all required outputs have been recorded in this handoff and final report.

## Stop conditions

Stop and report blocker if the selected APK is missing, ADB tooling is
unavailable, the selected target cannot be confirmed as the public-safe Philips
new alias, install conflict cannot be resolved by ordinary uninstall+install, or
the task would require secrets, private endpoints, APK modification, security
bypass, real payment, WebView/WebRTC/stream/media playback, production mutation
or raw evidence publication.
