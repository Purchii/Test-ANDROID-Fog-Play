# TASK-010 - CI/nightly smoke plan

## Task

Create a public-safe CI/nightly smoke plan and local fail-closed report foundation for future approved continuous QA checks.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-010 - CI/nightly smoke plan
```

## Branch

```text
qa/task-010-ci-nightly-smoke
```

Base commit:

```text
origin/main@61c8e050384ada878dc1955f396439eb5546754f
```

## Context

TASK-001 through TASK-004 created public-safe runtime discovery, reporting and manual screen/focus foundations. TASK-006 defined fixture approval boundaries. TASK-007, TASK-008 and TASK-009 added local fail-closed planning runners for network/offline, WebView/payment and compatibility/device coverage.

TASK-005 Android TV runtime smoke remains blocked because approved build/APK, Android TV target, runtime configuration, fixture approvals, redaction, evidence storage and cleanup/rollback prerequisites are still `unknown`.

TASK-010 adds a CI/nightly planning layer that composes the existing fail-closed foundations without enabling live device, APK, runtime, WebView, WebRTC, payment, network or production execution.

## Production safety classification

This TASK-010 documentation and local report generation work is `PROD_SAFE`.

Future live CI scheduling, CI secrets, shared runner configuration, artifact upload, Android runtime checks, device/emulator execution, APK handling, WebView, WebRTC, payment, network or backend checks are `PROD_CONDITIONAL` and remain blocked until all required prerequisites are approved with `present=true` and `evidence_status=confirmed`.

Real payments, production mutation, endpoint discovery, private URL or redirect publication, credential use, raw evidence publication, APK patching and security-control bypass are `PROD_FORBIDDEN`.

## Scope

In scope:

- task specification for TASK-010;
- public-safe CI/nightly smoke plan;
- public-safe CI/nightly smoke report template;
- local fail-closed JSON report generator;
- unit tests for metadata loading, fail-closed behavior, status normalization, CLI output and redaction;
- UTF-8 BOM metadata support;
- redaction of URLs, emails, secret-like values, sessions, cookies, authorization values, API keys, local paths, CI token-like values and opaque long values;
- release gate wiring for CI/nightly smoke readiness planning;
- source-of-truth updates for current state, active run, backlog, quality gates, risk register and verification memory.

Out of scope:

- creating or enabling a live scheduled CI workflow;
- CI secrets, private runners, runner credentials or external service mutation;
- runtime/device/APK execution;
- executable Android device or runtime command recipes;
- WebView, WebRTC, browser, redirect, backend, network or payment execution;
- endpoint discovery, extraction, publication or inventory;
- private URLs, redirect chains, headers, payloads, cookies, sessions, account identifiers or payment data;
- source code, decompiled code, smali or method bodies;
- raw logs, screenshots, videos, packet captures, dumps or raw evidence;
- APK patching, resigning or modification;
- TLS, pinning, auth or security-control bypass;
- real user data, real payments, production mutation, load testing or destructive actions.

## Deliverables

- `tasks/TASK_010_ci_nightly_smoke_plan.md`
- `docs/qa/ci-nightly-smoke-plan.md`
- `docs/qa/ci-nightly-smoke-report-template.md`
- `automation/ci_nightly_smoke/__init__.py`
- `automation/ci_nightly_smoke/generate_ci_nightly_smoke_report.py`
- `tests/test_ci_nightly_smoke.py`

Source-of-truth updates:

- `automation/README.md`
- `automation/reporting/generate_release_gate_report.py`
- `tests/test_release_gate_report.py`
- `docs/qa/evidence-schema.md`
- `docs/qa/release-gate-report-template.md`
- `docs/context/current-state.md`
- `docs/context/handoff/active-run.md`
- `docs/context/governance/risk-register.md`
- `docs/context/engineering/quality-gates.md`
- `docs/context/engineering/verification-memory.md`
- `docs/tasks/backlog.md`

## Required prerequisites

The CI/nightly smoke report generator requires all metadata keys below:

- `approved_static_ci_scope`;
- `approved_schedule_policy`;
- `repository_safety_policy`;
- `resource_budget`;
- `redaction_policy`;
- `evidence_storage`;
- `artifact_retention_policy`;
- `dependency_policy`;
- `security_review`;
- `qa_review`.

Each prerequisite must be a JSON object with:

- `present=true`;
- `evidence_status=confirmed`;
- optional public-safe `note`.

Missing metadata, malformed JSON, non-object JSON, missing prerequisite objects, `present` not true or any non-confirmed evidence status blocks the report. Invalid evidence status normalizes to `unknown`.

## Generator behavior

- `--metadata` accepts an optional public-safe JSON file.
- `--output` writes JSON to a file; otherwise JSON is written to stdout.
- Input is read with UTF-8 BOM support.
- Missing, malformed or non-object metadata emits `overall_status=blocked`.
- Partial or non-confirmed metadata emits `overall_status=blocked`.
- Complete confirmed metadata emits `overall_status=not_run`.
- Planned CI/nightly checks remain `result=not_run` and `evidence_status=unknown`.
- Optional `ci_jobs` are normalized as public-safe aliases only.
- Optional `artifacts` are normalized as public-safe redacted references only.
- The generator must never emit a successful runtime or live CI result.
- The generator performs no Android, device, APK, WebView, WebRTC, payment, backend, network, live CI or production interaction.

## Acceptance criteria

- TASK-010 runs in a fresh task thread and task branch.
- No forbidden artifact, credential, private endpoint, redirect chain, cookie, token, real account, real payment value, raw evidence, APK artifact or executable runtime/device/network recipe is requested or committed.
- CI/nightly plan is public-safe and fail-closed.
- Live CI scheduling and runtime execution remain blocked unless future approvals are confirmed.
- Required prerequisites are enforced exactly as fail-closed gates.
- Missing metadata, missing metadata path, malformed metadata and non-object metadata block.
- Invalid evidence status normalizes to `unknown` and blocks.
- Complete confirmed metadata produces only `not_run` planned checks with `unknown` evidence, never a successful runtime or live CI result.
- CLI supports stdout and `--output`.
- Redaction covers URLs, emails, secret-like values, sessions, cookies, authorization values, API keys, local paths, CI token-like values and opaque long values.
- Release gate reporting includes CI/nightly smoke readiness as runtime-dependent R1 gate `RG-010`.
- Unit tests cover required fail-closed and redaction behavior.
- Multi-agent Planner, Builder, QA Reviewer A, QA Reviewer B, Security/Prod-safety Reviewer and Docs/Scribe reviews complete.

## Verification

- `git status --short --branch`;
- `git diff --check`;
- inspect changed diff;
- verify ASCII-only content for TASK-010 markdown deliverables;
- `python -m pytest -q tests/test_ci_nightly_smoke.py`;
- `python -m pytest -q tests/test_release_gate_report.py`;
- `python -m pytest -q`;
- `python -m compileall automation tests`;
- local dry-run with no metadata;
- local dry-run with public-safe confirmed sample metadata;
- changed-file public-safety scan;
- diff-only forbidden-value scan;
- multi-agent QA, Security/Prod-safety and Docs/Scribe review.

Runtime/device/APK/WebView/WebRTC/browser/redirect/payment/backend/network/live CI execution is not run for TASK-010.

## Stop conditions

Stop and ask for user or Orchestrator guidance if any requested change would require:

- live CI scheduling, CI secrets or private runner configuration;
- runtime/device/APK execution;
- Android runtime command recipes;
- WebView, WebRTC, browser, redirect, payment, network, backend, proxy or packet interaction;
- endpoint, private URL, redirect chain, cookie, token or payment data discovery, extraction or publication;
- source code or decompiled code;
- private endpoints, secrets, tokens, cookies, sessions or production credentials;
- real accounts, real user data or real payment instruments;
- raw logs, screenshots, videos, packet captures, dumps or endpoint inventories;
- production mutation, load testing, security bypasses or destructive actions;
- failing quality gates, unavailable real subagents or R0/R1 reviewer blockers.
