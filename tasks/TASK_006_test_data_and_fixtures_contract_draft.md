# TASK-006 - Test data and fixtures contract draft

## Task

Draft the public-safe test data and fixtures contract for future Android TV, hybrid, WebView, WebRTC, auth/session, network/offline and payment-safe QA work.

## Mode

`NON_AUTONOMOUS`

## Thread title

```text
TASK-006 - Test data and fixtures contract draft
```

## Branch

```text
qa/task-006-test-fixtures-contract
```

Base commit:

```text
origin/main@474d0de62a552b48ead820cd2743b54313a07918
```

## Context

TASK-001 through TASK-004 created public-safe runtime discovery, exported component guard, reporting, release gate and manual screen/focus map foundations. Those tasks keep runtime execution blocked while approved build, target, configuration, fixture, redaction, evidence storage and cleanup prerequisites are unknown.

TASK-006 defines the contract that product, QA, security and backend owners must approve before future runtime-dependent tasks may use synthetic users, sessions, streams, WebView, payment, network or offline fixtures.

## Production safety classification

This TASK-006 documentation work is `PROD_SAFE`.

Future fixture usage is `PROD_CONDITIONAL` and remains blocked unless all documented conditions are approved, recorded and reviewed before execution.

## Scope

In scope:

- task specification for TASK-006;
- public-safe test data and fixtures contract;
- approval checklist for future fixture use;
- synthetic QA user rules;
- auth/session boundary rules;
- stream fixture rules;
- WebView and payment staging-only fixture rules;
- network/offline prerequisite rules;
- redaction, evidence storage, cleanup and rollback requirements;
- ownership, approval and evidence status rules;
- fail-closed blocked behavior when approvals are missing.

Out of scope:

- runtime/device execution;
- APK/AAB/DEX/native/signing artifact handling;
- Android device command recipes;
- WebView, WebRTC, network or payment execution steps;
- source code, decompiled code, smali or method bodies;
- secrets, tokens, cookies, sessions, production credentials or private endpoints;
- real user data;
- raw logs, screenshots, videos, endpoint inventories or raw evidence;
- APK patching, resigning or modification;
- TLS, pinning or security-control bypass;
- real payments or production mutation;
- updates to active-run, current-state, backlog, risk, quality or verification memory docs by Builder. Orchestrator and Docs/Scribe may update source-of-truth state within the task scope.

## Deliverables

- `docs/qa/test-data-fixtures-contract.md`
- `docs/qa/fixtures-approval-checklist.md`
- `tasks/TASK_006_test_data_and_fixtures_contract_draft.md`

Source-of-truth updates handled by Orchestrator or Docs/Scribe:

- `docs/context/current-state.md`
- `docs/context/handoff/active-run.md`
- `docs/context/governance/risk-register.md`
- `docs/context/engineering/quality-gates.md`
- `docs/context/engineering/verification-memory.md`
- `docs/tasks/backlog.md`
- `docs/qa/evidence-schema.md`
- `docs/qa/release-gate-report-template.md`

## Required workflow

TASK-006 is part of the strict multi-agent project workflow. This Builder deliverable is limited to the approved write scope. Orchestrator, Planner, independent QA reviewers, Security/Prod-safety Reviewer and Docs/Scribe handle run framing, independent review, governance docs and final handoff outside this Builder scope.

## Acceptance criteria

- Only the three approved deliverable files are created or updated by Builder.
- Documents are public-safe, ASCII-only markdown.
- No real credentials, endpoints, accounts, payment data, raw evidence, private identifiers or executable Android runtime/device command recipes are introduced.
- The contract covers synthetic QA users, auth/session boundaries, stream fixtures, WebView/payment staging-only fixtures, network/offline prerequisites, redaction policy, evidence storage, cleanup/rollback, ownership/approval and evidence status rules.
- Missing approvals explicitly keep runtime-dependent tasks `blocked`.
- Future fixture use is classified as `PROD_CONDITIONAL` with required conditions.
- TASK-006 docs-only work is classified as `PROD_SAFE`.
- Acceptance criteria, verification and stop conditions are present in this task spec.

## Verification

Docs-only verification:

- `git status --short --branch`;
- `git diff --check`;
- inspect changed markdown diff;
- verify ASCII-only content in the three deliverables;
- scan changed files for forbidden content classes such as secrets, private endpoints, raw evidence references, production credentials, real payment data, APK artifacts and executable Android runtime/device recipes.

Runtime/device/APK/WebView/WebRTC/payment/network execution is not run for TASK-006.

## Stop conditions

Stop and ask for user or Orchestrator guidance if any requested change would require:

- runtime/device/APK execution;
- Android runtime command recipes;
- source code or decompiled code;
- private endpoints, secrets, tokens, cookies, sessions or production credentials;
- real accounts, real user data or real payment instruments;
- raw logs, screenshots, videos or endpoint inventories;
- production mutation, load testing, security bypasses or destructive actions;
- edits outside the approved Builder write scope;
- default branch merge/push in `NON_AUTONOMOUS` mode.
