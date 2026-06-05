# Network Offline Policy

Task: `TASK-007 - Network/offline policy and safe runner`

Production safety classification: `PROD_SAFE` for this policy and local report generation. Any future Android TV network/offline runtime work is `PROD_CONDITIONAL` and remains blocked until approved build, target, configuration, network profile, budget, redaction, evidence storage, cleanup, Security review and QA review prerequisites are recorded with `evidence_status=confirmed`.

This document is public-safe. It must not contain private endpoints, raw traffic evidence, credentials, tokens, cookies, sessions, real user data, payment data, APK artifacts, packet captures, proxy configuration, TLS bypass details or executable Android runtime/device/network recipes.

## Core Rule

No approved network/offline prerequisites, no network/offline execution.

TASK-007 tooling creates a local JSON plan only. It does not interact with Android, a device, APK, backend, proxy, packet capture, network service or production environment.

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
| `approved_build` | Approved build identifier and handling rules exist outside this report. |
| `approved_target` | Approved Android TV target category is in scope. |
| `approved_config` | Approved configuration and environment class are known without endpoint values. |
| `network_profile_policy` | Approved profile aliases and allowed conditions are recorded at category level. |
| `resource_budget` | Duration, retry, account, stream and traffic budgets are bounded. |
| `redaction_policy` | Evidence redaction rules are approved before capture. |
| `evidence_storage` | Raw evidence, if approved later, stays in ignored local storage. |
| `cleanup_rollback` | Normal connectivity and mutable fixture state can be restored. |
| `security_review` | Security/Prod-safety Reviewer approves the boundary. |
| `qa_review` | QA Reviewer approves coverage and blocked/not-run expectations. |

Missing, malformed, non-object, `present` not true or non-confirmed prerequisite metadata keeps the report `blocked`.

## Allowed Future Profile Categories

Future tasks may use only approved category-level aliases. Public docs must not include commands, endpoint values, proxy rules or packet details.

| Profile alias | Purpose | Default status |
|---|---|---:|
| `offline` | Observe startup, guarded UI and recovery when connectivity is unavailable. | `blocked` |
| `reconnect` | Observe recovery after approved connectivity restoration. | `blocked` |
| `high_latency` | Observe user-visible waiting and timeout categories within budget. | `blocked` |
| `intermittent_connectivity` | Observe interruption and recovery category behavior. | `blocked` |
| `transport_switch` | Observe category-level transition between approved connection types. | `blocked` |
| `captive_portal_like` | Observe approved blocked-access category behavior without private network details. | `blocked` |

## Forbidden Categories

The following remain forbidden in public docs and TASK-007 tooling:

- endpoint discovery, extraction or publication;
- packet capture instructions or packet dumps;
- proxy setup, interception or traffic mutation recipes;
- TLS, certificate, pinning, authentication or security-control bypass;
- production load, fuzzing or unbounded retry behavior;
- private headers, payloads, cookies, sessions or authorization values;
- raw logs, screenshots, videos, dumps or endpoint inventories;
- APK modification, resigning, patching or source/decompiled analysis.

## Planned Check Categories

TASK-007 report output may include these categories only as `not_run` with `evidence_status=unknown`:

| Check | Purpose |
|---|---|
| `offline_startup` | Future observation of startup behavior under an approved offline profile. |
| `offline_recovery` | Future observation of recovery after approved connectivity restoration. |
| `reconnect_during_stream_guard` | Future category-level reconnect observation around stream guard behavior. |
| `high_latency_guard` | Future waiting, timeout and retry-category observation within budget. |
| `interruption_error_state` | Future approved interruption and user-visible error-state observation. |
| `redacted_network_evidence` | Future public-safe evidence reference validation. |

The safe runner must never emit a successful runtime result. Complete confirmed metadata means prerequisites are ready for a future task, not that behavior is verified.

## Redaction Rules

Before any public report is written, redact:

- URLs and endpoint-like values;
- email addresses and user identifiers;
- secrets, tokens, cookies, sessions, authorization values and API keys;
- local paths;
- opaque long values.

Allowed public output is limited to aliases, blocked/not-run status, redacted artifact references, risk summaries, unknowns and reviewer status.

## Cleanup And Recovery

Future runtime tasks must prove or record:

- normal connectivity can be restored;
- fixture state is reset or no mutable state was changed;
- retry and duration budgets were respected;
- evidence storage is ignored by source control;
- raw evidence remains outside public reports;
- Security and QA review remain in scope.

If cleanup or rollback cannot be confirmed, network/offline release gates remain `blocked`.
