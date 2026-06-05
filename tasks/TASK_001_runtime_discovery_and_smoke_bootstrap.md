# TASK-001 - Runtime discovery and smoke bootstrap

## Task

Create the first safe QA automation/process foundation for Android TV black-box testing based on sanitized reverse-analysis context.

## Mode

Start in a fresh Codex thread. Default mode is `BOUNDED_AUTONOMOUS` only if all safety/verification gates are clear; otherwise downgrade to `NON_AUTONOMOUS` and ask for missing approvals.

## Thread title

```text
TASK-001 - Runtime discovery and smoke bootstrap
```

## Branch

```text
qa/task-001-runtime-discovery-smoke-bootstrap
```

## Scope

In scope:

- QA repo structure;
- evidence/reporting model;
- manual runtime discovery templates;
- smoke planning skeleton for startup/focus/evidence capture;
- exported component guard skeleton links;
- release gate report template/generator stub;
- blocked-report behavior for missing approved build/device/config;
- unknowns/risk updates.

Out of scope:

- source/decompiled code;
- secrets/endpoints;
- APK patching;
- security bypass;
- real payments;
- destructive production testing;
- full E2E stream automation before fixtures are confirmed;
- runtime/device execution until a future task satisfies safety gates.

## Multi-agent plan

Required:

- Planner;
- Builder;
- QA Reviewer A;
- QA Reviewer B;
- Security/Prod-safety Reviewer;
- Docs/Scribe;
- Orchestrator.

Optional:

- Android TV Automation Reviewer.

## Acceptance criteria

- No forbidden artifact requested.
- No unsafe test action added.
- Missing approved build/device/credentials produce `blocked` reports, not crashes.
- Every conclusion has evidence status.
- Runtime discovery template exists.
- Smoke skeleton is blocked safely when approved build/device/config is missing.
- Russian handoff report produced.

## Verification

- `git status --short --branch`;
- unit tests if framework exists;
- report generation dry-run;
- no secrets/private endpoints in committed config;
- runtime/device checks only if approved build/device/config is available and classified before execution.
