# TASK-013 - Next-task selection blocker and safe backlog refresh

## Task

Record the post-TASK-012 next-task selection blocker and refresh the public-safe backlog so autonomous work can continue only on tasks that do not require user approvals, runtime prerequisites or private data.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-013 - Next-task selection blocker and safe backlog refresh
```

## Branch

```text
qa/task-013-next-task-selection-safe-backlog-refresh
```

## Context

TASK-012 completed the safe task prioritization and approval-dependency map. A subsequent next-task selection checkpoint confirmed that `main` and `origin/main` were aligned at `3cee73e441f0fa945ed4632b47d2880cfae9951f`, and all completed task branches were merged into the detected default branch.

The checkpoint also confirmed that `docs/tasks/backlog.md` had no eligible unfinished public-safe task after TASK-012. The only unfinished listed task was TASK-005, which remains blocked until approved build/APK, Android TV target, runtime configuration, fixtures, redaction, evidence storage, cleanup/rollback, QA review and Security/Prod-safety review are confirmed.

TASK-013 turns that blocker into explicit source-of-truth state and adds proposed public-safe follow-up tasks that can run without user secrets, private endpoints, APK handling, device execution, real accounts, real payments or production interaction.

## Production safety classification

This TASK-013 work is `PROD_SAFE` because it is docs-only and repository-local.

Runtime/device/APK/WebView/WebRTC/payment/network/live CI execution remains `PROD_CONDITIONAL` and blocked until every required dependency is recorded with `present=true`, `evidence_status=confirmed` and independent QA/Security review.

The following remain `PROD_FORBIDDEN`:

- application source code, decompiled code, smali or method bodies;
- secrets, tokens, cookies, sessions, production credentials or private endpoints;
- raw logs, screenshots, videos, packet captures, dumps or endpoint inventories;
- APK patching, modification, resigning or security-control bypass;
- executable Android/device/network/WebView/WebRTC/payment/live CI command recipes in public docs;
- real user data, real payments, destructive actions, unbudgeted load tests or production mutation.

## Scope

In scope:

- task specification for TASK-013;
- update `docs/tasks/backlog.md` with TASK-013 and proposed public-safe follow-up tasks;
- update `docs/context/handoff/active-run.md` with the current TASK-013 run state;
- update `docs/context/current-state.md` with the post-TASK-012 next-task blocker and TASK-013 purpose;
- update `docs/context/engineering/verification-memory.md` after verification;
- optional quality/risk wording only if required by reviewers;
- docs/static verification and strict multi-agent review.

Out of scope:

- runtime/device/APK execution;
- Android runtime command recipes;
- WebView, WebRTC, browser, redirect, payment, network, backend, proxy, packet or live CI execution;
- fixture approval itself;
- approval of TASK-005 or any runtime-dependent work;
- private fixture values, endpoint values, account identifiers, payment values or raw evidence;
- automation code or report generator changes.

## Proposed safe follow-up task classes

TASK-013 may add proposed public-safe tasks such as:

- public repository safety scan checklist or generator;
- approval metadata schema validator;
- TASK-005 specification draft only, with runtime execution still blocked;
- synthetic redaction policy test corpus;
- docs consistency and link sanity checks.

These proposed tasks do not approve runtime execution by themselves.

## Acceptance criteria

- TASK-013 remains docs-only and public-safe.
- The post-TASK-012 next-task selection blocker is recorded without blaming runtime prerequisites as completed.
- `docs/tasks/backlog.md` no longer presents TASK-012 as the current selected next task.
- Backlog contains proposed public-safe follow-up tasks that do not require user answers, credentials, private endpoints, APK handling, device execution, real accounts, real payments or production interaction.
- TASK-005 remains explicitly blocked until required approvals are `confirmed`.
- No private value, raw evidence, endpoint, APK path, executable runtime/device/network recipe, secret, real account or payment data is introduced.
- Verification memory records the docs-only checks actually run.
- Multi-agent Planner, Builder, QA Reviewer A, QA Reviewer B, Security/Prod-safety Reviewer and Docs/Scribe reviews complete.

## Verification

Docs-only verification:

- `git status --short --branch`;
- `git diff --check`;
- inspect changed diff;
- ASCII check for TASK-013 markdown deliverables;
- changed-file public-safety scan;
- `python -m pytest -q`;
- `python -m compileall automation tests`;
- multi-agent QA, Security/Prod-safety and Docs/Scribe review.

Runtime/device/APK/WebView/WebRTC/browser/redirect/payment/backend/network/live CI validation is not run for TASK-013.

## Stop conditions

Stop and ask for user or Orchestrator guidance if any requested change would require:

- runtime/device/APK execution;
- executable Android/device/network command recipes;
- fixture values, credentials, private endpoints, account identifiers, payment data or raw evidence;
- source code or decompiled code;
- production mutation, real payments, security bypasses, load testing or destructive actions;
- edits that turn proposed public-safe tasks into approved execution tasks.
