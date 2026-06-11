# Current state — MTC Fog Play Android QA

## Project

Repository:

```text
https://github.com/Purchii/Test-ANDROID-Fog-Play
```

Goal: build a safe, evidence-first Android TV QA automation and QA process repository for `MTC Fog Play`.

## Known inputs

The project starts from a sanitized QA reverse-analysis pack for a signed Android TV APK. The pack contains manifest/surface/navigation/network/WebView/SDK/risk/smoke/regression/exploratory recommendations without source code, decompiled code, secrets or raw private endpoints.

## Core QA areas

- Android TV runtime startup;
- D-pad/focus navigation;
- auth/session;
- catalog/search;
- WebRTC/stream lifecycle;
- WebView/hybrid/payment-safe flows;
- exported component guard checks;
- network/offline;
- update/install/backup;
- accessibility/localization;
- privacy/logging/security-oriented QA without bypass.

## Current workflow policy

- Strict multi-agent for every bounded task.
- Fresh Codex thread per independent task.
- One goal per task thread.
- Branch per task from current default branch.
- `NON_AUTONOMOUS`: no merge/push default branch without explicit user command.
- `BOUNDED_AUTONOMOUS`: verified task branch must be merged/pushed to the detected default/trunk branch before starting the next independent task.
- Old completed threads become inactive, not deleted.
- Subagents from inactive threads are closed when no longer needed.

## Bootstrap state

- GitHub remote was empty during TASK-000 bootstrap; `main` is initialized as the first default branch.
- TASK-000 implementation branch is `qa/task-000-bootstrap-codex-docs`.
- GitHub remote HEAD/default is confirmed as `main`.
- Public source-of-truth excludes `qa_reverse_analysis/raw/`, compiled cache files and the local reverse-analysis zip by default.
- Public reverse-analysis context is summarized in `docs/context/reverse-analysis/`.
- TASK-001 completed the runtime discovery and smoke bootstrap foundation in fresh thread `TASK-001 - Runtime discovery and smoke bootstrap` on branch `qa/task-001-runtime-discovery-smoke-bootstrap` from `main` commit `5a17c0f`.
- TASK-002 completed the exported component guard checks skeleton in fresh thread `TASK-002 - Exported component guard checks skeleton` on branch `qa/task-002-exported-component-guards` from `main` commit `07cad5a`.
- TASK-003 completed the shared reporting, evidence schema and release gate generator foundation in fresh thread `TASK-003 - Reporting, evidence schema and release gate generator` on branch `qa/task-003-evidence-release-gates` from `main` commit `e260b84`.
- TASK-004 completed the manual runtime screen and TV focus map template foundation in fresh thread `TASK-004 - Manual runtime screen and TV focus map templates` on branch `qa/task-004-runtime-screen-focus-map` from `main` commit `3840a00`.
- TASK-006 completed in fresh thread `TASK-006 - Test data and fixtures contract draft` on branch `qa/task-006-test-fixtures-contract` from `main` commit `474d0de`. Planner selected TASK-006 because TASK-005 runtime smoke remains blocked by missing approved build/device/config/fixture prerequisites. TASK-006 default-branch merge/push was authorized by explicit user command in `NON_AUTONOMOUS` mode.
- TASK-007 completed in fresh thread `TASK-007 - Network/offline policy and safe runner` on branch `qa/task-007-network-offline-policy` from `main` commit `46a7e0f`. TASK-007 is scoped to public-safe network/offline policy and local fail-closed report generation only.
- TASK-009 completed in fresh thread `TASK-009 - Compatibility/device matrix and report format` on branch `qa/task-009-device-matrix` from `main` commit `b50fb53`. Planner selected TASK-009 because TASK-005 runtime smoke remains blocked and TASK-008 is `NON_AUTONOMOUS` WebView/payment planning with fixture-sensitive approval boundaries.
- TASK-008 completed in fresh thread `TASK-008 - WebView/payment safe QA plan` on branch `qa/task-008-webview-payment-safe-qa` from `main` commit `d5887ca`. Planner and Security/Prod-safety selected TASK-008 before TASK-010 so CI/nightly planning can inherit an explicit WebView/payment safety boundary. TASK-008 was implemented in `NON_AUTONOMOUS`; default branch merge/push was authorized by explicit user command on 2026-06-06.
- TASK-010 completed in fresh thread `TASK-010 - CI/nightly smoke plan` on branch `qa/task-010-ci-nightly-smoke` from `main` commit `61c8e05`. Planner selected TASK-010 because TASK-005 runtime smoke remains blocked and CI/nightly planning can now inherit the explicit WebView/payment, network/offline and compatibility safety boundaries.

## Runtime readiness

- Approved APK/build for runtime automation: `unknown`.
- Approved Android TV device/emulator/config: `unknown`.
- Approved QA accounts, stream fixtures and staging payment fixtures: `unknown`.
- TASK-001 created blocked-report tooling and public-safe discovery templates; TASK-002 created exported component guard skeleton tooling. Runtime/device execution remains blocked until a future task satisfies safety gates.
- TASK-003 created shared evidence schema, release gate template and local fail-closed release gate generator. Release gate generation remains local/public-safe and does not perform runtime/device execution; runtime-dependent gates remain blocked/not_run until approved evidence exists.
- TASK-004 added public-safe manual runtime screen/focus map templates and local fail-closed map report generation. Runtime screen/focus observation remains blocked until a future task records approved build/device/config/fixture/redaction/storage/cleanup prerequisites.
- TASK-006 drafted the public-safe fixture approval contract and checklist for synthetic users, auth/session, stream, WebView, payment staging, network/offline, redaction, evidence storage and cleanup/rollback. This does not approve any real fixture values and does not execute runtime/device checks.
- TASK-007 adds a public-safe network/offline policy and local safe runner. This does not approve any real network profile, does not execute device/network/backend/proxy/packet checks and does not confirm runtime behavior.
- TASK-009 adds a public-safe compatibility/device matrix, report template and local fail-closed report generator. This does not approve any real device class, does not execute Android/device/APK/WebView/WebRTC/payment/network checks and does not confirm compatibility behavior.
- TASK-008 adds a public-safe WebView/payment QA plan, report template and local fail-closed report generator. This does not approve any real WebView fixture, payment staging fixture, account, redirect, endpoint or payment flow; it does not execute Android/device/APK/WebView/browser/payment/network checks and does not confirm runtime behavior.
- TASK-010 adds a public-safe CI/nightly smoke plan, report template and local fail-closed report generator. This does not approve live CI scheduling, CI secrets, private runners, artifact uploads, Android/device/APK/WebView/WebRTC/payment/network checks or production interaction; it does not confirm live CI or runtime behavior.

## Evidence status policy

All facts use:

- `confirmed`;
- `likely`;
- `hypothesis`;
- `unknown`.

Do not treat static names or guesses as confirmed runtime behavior.
