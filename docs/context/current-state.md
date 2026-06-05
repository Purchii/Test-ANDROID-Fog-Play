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
- `BOUNDED_AUTONOMOUS`: verified task branch may be merged/pushed to default branch.
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

## Runtime readiness

- Approved APK/build for runtime automation: `unknown`.
- Approved Android TV device/emulator/config: `unknown`.
- Approved QA accounts, stream fixtures and staging payment fixtures: `unknown`.
- TASK-001 created blocked-report tooling and public-safe discovery templates; TASK-002 created exported component guard skeleton tooling. Runtime/device execution remains blocked until a future task satisfies safety gates.
- TASK-003 created shared evidence schema, release gate template and local fail-closed release gate generator. Release gate generation remains local/public-safe and does not perform runtime/device execution; runtime-dependent gates remain blocked/not_run until approved evidence exists.

## Evidence status policy

All facts use:

- `confirmed`;
- `likely`;
- `hypothesis`;
- `unknown`.

Do not treat static names or guesses as confirmed runtime behavior.
