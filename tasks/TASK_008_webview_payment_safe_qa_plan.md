# TASK-008 - WebView/payment safe QA plan

## Task

Create a public-safe WebView/payment QA plan and local fail-closed report foundation for future approved hybrid, WebView and staging-only payment QA work.

## Mode

`NON_AUTONOMOUS`

## Thread title

```text
TASK-008 - WebView/payment safe QA plan
```

## Branch

```text
qa/task-008-webview-payment-safe-qa
```

## Context

TASK-006 defined fixture approval boundaries for synthetic users, auth/session, stream, WebView, payment staging, network/offline, redaction, evidence storage and cleanup. TASK-007 and TASK-009 added local fail-closed planning runners for network/offline and compatibility/device coverage.

TASK-008 closes the WebView/payment safety planning gap before CI/nightly smoke design. It defines public-safe categories, prerequisites and blocked/not-run report behavior without executing Android, device, APK, WebView, browser, redirect, payment, backend, network or production flows.

## Production safety classification

This TASK-008 documentation and local report generation work is `PROD_SAFE`.

Future WebView or payment-like execution is `PROD_CONDITIONAL` and remains blocked until all required prerequisites are approved with `present=true` and `evidence_status=confirmed`.

Real payments, private endpoint or redirect discovery, cookies/tokens/session extraction, TLS/pinning/security-control bypass, APK patching and source/decompiled analysis are `PROD_FORBIDDEN`.

## Scope

In scope:

- task specification for TASK-008;
- public-safe WebView/payment QA plan;
- public-safe WebView/payment report template;
- local fail-closed JSON report generator;
- unit tests for metadata loading, fail-closed behavior, status normalization, CLI output and redaction;
- UTF-8 BOM metadata support;
- redaction of URLs, emails, secret-like values, sessions, cookies, authorization values, API keys, local paths, payment-like identifiers and opaque long values;
- release gate wiring for WebView/payment-safe boundary planning.

Out of scope:

- runtime/device/APK execution;
- executable Android device command recipes;
- WebView, browser, redirect, backend, network or payment execution;
- private URL, redirect chain, endpoint, header, cookie, payload or payment data publication;
- source code, decompiled code, smali or method bodies;
- secrets, tokens, cookies, sessions, production credentials or private endpoints;
- raw logs, screenshots, videos, packet captures, dumps or raw evidence;
- APK patching, resigning or modification;
- TLS, pinning, auth or security-control bypass;
- real user data, real payments, production mutation, load testing or destructive actions;
- default branch merge/push in `NON_AUTONOMOUS` mode.

## Deliverables

- `tasks/TASK_008_webview_payment_safe_qa_plan.md`
- `docs/qa/webview-payment-safe-qa-plan.md`
- `docs/qa/webview-payment-safe-report-template.md`
- `automation/webview_payment_safe_runner/__init__.py`
- `automation/webview_payment_safe_runner/generate_webview_payment_safe_report.py`
- `tests/test_webview_payment_safe_runner.py`

## Required prerequisites

The WebView/payment safe runner requires all metadata keys below:

- `approved_build`;
- `approved_target`;
- `approved_config`;
- `webview_fixture_policy`;
- `payment_staging_policy`;
- `synthetic_user_policy`;
- `resource_budget`;
- `redaction_policy`;
- `evidence_storage`;
- `cleanup_rollback`;
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
- Planned WebView/payment checks remain `result=not_run` and `evidence_status=unknown`.
- Optional `artifacts` are normalized as public-safe redacted references only.
- The generator must never emit a successful runtime or payment result.
- The generator performs no Android, device, APK, WebView, browser, redirect, payment, backend, network or production interaction.

## Acceptance criteria

- TASK-008 remains `NON_AUTONOMOUS`; default branch merge/push is not performed without explicit user approval.
- No forbidden artifact, credential, private endpoint, redirect chain, cookie, token, real account, real payment value, raw evidence, APK artifact or executable runtime/device/network recipe is requested or committed.
- WebView/payment execution remains blocked unless staging-only non-real-payment fixture approvals are `confirmed`.
- Required prerequisites are enforced exactly as fail-closed gates.
- Missing metadata, malformed metadata and non-object metadata block.
- Invalid evidence status normalizes to `unknown` and blocks.
- Complete confirmed metadata produces only `not_run` planned checks with `unknown` evidence, never a successful runtime or payment result.
- CLI supports stdout and `--output`.
- Redaction covers URLs, emails, secret-like values, sessions, cookies, authorization values, API keys, local paths, payment-like identifiers and opaque long values.
- Release gate reporting includes WebView/payment-safe boundary as runtime-dependent R1 gate `RG-009`.
- Unit tests cover required fail-closed and redaction behavior.
- Multi-agent Planner, Builder, QA Reviewer A, QA Reviewer B, Security/Prod-safety Reviewer and Docs/Scribe review complete.

## Verification

- `git status --short --branch`;
- `git diff --check`;
- inspect changed diff;
- verify ASCII-only content for TASK-008 markdown deliverables;
- `python -m pytest -q tests/test_webview_payment_safe_runner.py`;
- `python -m pytest -q tests/test_release_gate_report.py`;
- `python -m pytest -q`;
- `python -m compileall automation tests`;
- local dry-run with no metadata;
- local dry-run with public-safe confirmed sample metadata;
- changed-file public-safety scan;
- diff-only forbidden-value scan;
- multi-agent QA, Security/Prod-safety and Docs/Scribe review.

Runtime/device/APK/WebView/browser/redirect/payment/backend/network execution is not run for TASK-008.

## Stop conditions

Stop and ask for user or Orchestrator guidance if any requested change would require:

- runtime/device/APK execution;
- Android runtime command recipes;
- WebView, browser, redirect, payment, network, backend, proxy or packet interaction;
- endpoint, private URL, redirect chain, cookie, token or payment data discovery, extraction or publication;
- source code or decompiled code;
- private endpoints, secrets, tokens, cookies, sessions or production credentials;
- real accounts, real user data or real payment instruments;
- raw logs, screenshots, videos, packet captures, dumps or endpoint inventories;
- production mutation, load testing, security bypasses or destructive actions;
- default branch merge/push.
