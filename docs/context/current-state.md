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
- Public source-of-truth excludes `qa_reverse_analysis/raw/`, compiled cache files and the local reverse-analysis zip by default.
- Public reverse-analysis context is summarized in `docs/context/reverse-analysis/`.
- The next independent task must start in a fresh Codex thread from current `main`.

## Evidence status policy

All facts use:

- `confirmed`;
- `likely`;
- `hypothesis`;
- `unknown`.

Do not treat static names or guesses as confirmed runtime behavior.
