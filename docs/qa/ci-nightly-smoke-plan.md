# CI Nightly Smoke Plan

Task: `TASK-010 - CI/nightly smoke plan`

Production safety classification: `PROD_SAFE` for this plan and local report generation. Any future live CI schedule, CI secret, private runner, artifact upload, Android runtime, device/emulator, APK, WebView, WebRTC, payment, backend, network or production execution is `PROD_CONDITIONAL` and remains blocked until approved scope, schedule policy, repository safety policy, resource budget, redaction, evidence storage, artifact retention, dependency policy, Security review and QA review prerequisites are recorded with `evidence_status=confirmed`.

This document is public-safe. It must not contain private endpoints, raw evidence, credentials, tokens, cookies, sessions, real user data, payment data, APK artifacts, raw device identifiers, packet captures, proxy configuration, TLS bypass details or executable Android runtime/device/network recipes.

## Core Rule

No confirmed static CI scope and schedule policy, no nightly smoke execution.

TASK-010 tooling creates a local JSON plan only. It does not create a live CI schedule, access secrets, upload artifacts, install dependencies from private services, interact with Android, a device, APK, WebView, WebRTC session, payment surface, backend, network service or production environment.

## Evidence Status

Use exactly one evidence status for every prerequisite, planned check, risk and report field:

| Status | Meaning |
|---|---|
| `confirmed` | Backed by explicit approved metadata, team approval or approved sanitized artifact. |
| `likely` | Supported by planning context but not approved for execution. |
| `hypothesis` | A testable expectation that still needs approval or evidence. |
| `unknown` | No sufficient approved information is available. |

Only `evidence_status=confirmed` with `present=true` satisfies a prerequisite.

## Required Prerequisites

| Prerequisite | Required public-safe approval |
|---|---|
| `approved_static_ci_scope` | Approved local-only checks are in scope and require no device, APK, secrets or private services. |
| `approved_schedule_policy` | Nightly cadence, branch scope, manual dispatch rules and disabled runtime lanes are approved. |
| `repository_safety_policy` | Public repository constraints, ignored artifacts and forbidden file classes are approved. |
| `resource_budget` | Timeout, retry, concurrency and runner resource limits are bounded. |
| `redaction_policy` | Log, report and artifact redaction rules are approved before capture. |
| `evidence_storage` | Raw evidence, if approved later, stays in ignored local or approved restricted storage. |
| `artifact_retention_policy` | Public CI artifacts are restricted to sanitized JSON summaries and logs without sensitive values. |
| `dependency_policy` | Dependency installation/update behavior is pinned, reviewable and does not require secrets. |
| `security_review` | Security/Prod-safety Reviewer approves the boundary. |
| `qa_review` | QA Reviewer approves coverage and blocked/not-run expectations. |

Missing, malformed, non-object, `present` not true or non-confirmed prerequisite metadata keeps the report `blocked`.

## Static Nightly Scope

Allowed planned CI/nightly check categories:

| Category | Purpose | Default result |
|---|---|---:|
| `repository_hygiene` | Verify branch status, diff cleanliness and forbidden public artifacts. | `not_run` |
| `python_unit_tests` | Run local Python unit tests for fail-closed report generators. | `not_run` |
| `python_compileall` | Compile local automation and tests without runtime/device access. | `not_run` |
| `release_gate_dry_run` | Generate local release gate reports that fail closed without approved evidence. | `not_run` |
| `runtime_blocked_report_dry_run` | Generate local runtime blocked reports without device/APK interaction. | `not_run` |
| `network_offline_plan_dry_run` | Generate local network/offline plans without network interaction. | `not_run` |
| `webview_payment_plan_dry_run` | Generate local WebView/payment plans without WebView/payment interaction. | `not_run` |
| `compatibility_matrix_plan_dry_run` | Generate local compatibility plans without device inventory or runtime execution. | `not_run` |
| `public_safety_scan` | Scan changed or repository files for forbidden public artifact classes. | `not_run` |
| `redacted_summary_publish` | Publish only sanitized JSON summaries after approval. | `not_run` |

The generator must never emit a successful live CI, runtime or device result. Complete confirmed metadata means prerequisites are ready for a future CI implementation task, not that CI execution has run.

## Forbidden CI Content

The following remain forbidden in public docs and TASK-010 tooling:

- live Android device or emulator commands;
- APK, AAB, DEX, native, signing or decompiled artifacts;
- private endpoints, URLs, redirect chains, headers, payloads, cookies, sessions or authorization values;
- CI secrets, private runner credentials, cloud tokens or deploy keys;
- raw screenshots, videos, logs, packet captures, dumps or endpoint inventories;
- proxy setup, interception or traffic mutation recipes;
- TLS, certificate, pinning, authentication or security-control bypass;
- production load, fuzzing or unbounded retry behavior;
- real user data, real payment data, real payment instruments or production mutation.

## Future Execution Gate

Future CI/nightly execution may start only after a separate approved task records:

- confirmed approved static CI scope and schedule policy;
- approved public-safe dependency and repository safety boundaries;
- approved resource budget, timeout, retry and concurrency limits;
- approved redaction, evidence storage and artifact retention policy;
- Security and QA review approval before enabling live schedules;
- confirmed runtime/device/build/fixture approvals for any runtime-dependent lane.

If any gate is missing, CI/nightly smoke reports remain `blocked` or `not_run`.
