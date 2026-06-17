# TASK-012 - Safe task prioritization and approval-dependency map

## Task

Create public-safe docs-only decision support for choosing safe next QA tasks while runtime-dependent work remains blocked.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-012 - Safe task prioritization and approval-dependency map
```

## Branch

```text
qa/task-012-safe-task-prioritization
```

## Context

TASK-001 through TASK-011 created public-safe QA foundations, templates, policies and local fail-closed planning/reporting layers. TASK-005 Android TV runtime smoke remains blocked because approved build/APK, Android TV target, runtime configuration, fixture approvals, redaction, evidence storage and cleanup/rollback prerequisites are still `unknown`.

TASK-012 defines a category-level prioritization model and approval dependency map so future Planner and Orchestrator roles can choose safe next work without requesting secrets, private endpoints, raw evidence, application source, decompiled code, device execution or production actions.

## Production safety classification

This TASK-012 documentation work is `PROD_SAFE`.

Future runtime/device/APK/WebView/WebRTC/payment/network/live CI execution is `PROD_CONDITIONAL` and remains blocked until all task-specific approvals are recorded with `evidence_status=confirmed`.

The following remain `PROD_FORBIDDEN`:

- application source code, decompiled code, smali or method bodies;
- secrets, tokens, cookies, sessions, production credentials or private endpoints;
- raw logs, screenshots, videos, packet captures, dumps or endpoint inventories;
- APK patching, modification, resigning or security-control bypass;
- executable Android/device/network command recipes in public docs;
- real user data, real payments, destructive actions, load tests without budget or production mutation.

## Scope

In scope:

- task specification for TASK-012;
- public-safe safe-next-task prioritization model;
- public-safe approval dependency map;
- category-level dependency matrix for completed, blocked and proposed task classes;
- explicit confirmation that TASK-005 and runtime-dependent tasks remain blocked until approvals are confirmed;
- docs-only acceptance criteria and verification steps.

Out of scope:

- runtime/device/APK execution;
- local or remote Android command recipes;
- automation code, tests, CI workflow files or report generators;
- fixture approval itself;
- private fixture values, endpoint values, account identifiers, payment values or raw evidence;
- runtime approval or fixture approval itself.

## Deliverables

- `tasks/TASK_012_safe_task_prioritization_approval_dependency_map.md`
- `docs/qa/safe-task-prioritization.md`
- `docs/qa/approval-dependency-map.md`

Source-of-truth updates:

- `docs/context/current-state.md`
- `docs/context/handoff/active-run.md`
- `docs/context/governance/risk-register.md`
- `docs/context/engineering/quality-gates.md`
- `docs/context/engineering/verification-memory.md`
- `docs/tasks/backlog.md`

## Evidence status rules

Every conclusion, dependency, task readiness statement and release gate uses exactly one evidence status:

| Status | Meaning |
|---|---|
| `confirmed` | Backed by explicit team approval, approved sanitized artifact or approved runtime evidence. |
| `likely` | Supported by current public-safe project docs but not approved for execution. |
| `hypothesis` | A testable expectation that still needs approval or evidence. |
| `unknown` | No sufficient approved information is available. |

Only `confirmed` approvals can unblock runtime-dependent execution. Planning value, completed docs or static templates do not confirm runtime behavior.

## Acceptance criteria

- The three deliverable files exist and are ASCII-only Markdown.
- Content is public-safe and category-level only.
- TASK-005 remains explicitly blocked until approved build/device/config/fixture/redaction/storage/cleanup prerequisites are `confirmed`.
- Runtime-dependent WebView, WebRTC, payment, network/offline, compatibility, navigation transition and live CI tasks remain blocked until their own approvals are `confirmed`.
- The prioritization model favors `PROD_SAFE` docs, templates, local static checks, fail-closed generators, redaction work and release-gate planning when runtime approvals are missing.
- The dependency map separates `PROD_SAFE`, `PROD_CONDITIONAL` and `PROD_FORBIDDEN` work.
- No executable Android/device/network command recipe, private endpoint, raw evidence, secret, payment data, app source, decompiled code, APK artifact or production action is included.
- Verification steps are docs-only and do not require device, APK, account, network, WebView, WebRTC, payment, backend, live CI or production access.

## Verification

Docs-only verification:

- `git status --short --branch`;
- `git diff --check`;
- inspect the changed diff;
- verify ASCII-only content for TASK-012 Markdown deliverables;
- scan changed TASK-012 files for forbidden public-repo content categories;
- confirm no runtime/device/APK/WebView/WebRTC/payment/network/live CI execution was run.

Runtime/device/APK/WebView/WebRTC/browser/redirect/payment/backend/network/live CI validation is not run for TASK-012.

## Stop conditions

Stop and ask for Orchestrator or user guidance if any requested change would require:

- runtime/device/APK execution;
- executable Android/device/network command recipes;
- fixture values, credentials, private endpoints, account identifiers, payment data or raw evidence;
- source code or decompiled code;
- production mutation, real payments, security bypasses, load testing or destructive actions;
- edits outside the three Builder-owned files without explicit approval.
