# TASK-003 - Reporting, evidence schema and release gate generator

## Task

Create the shared public-safe reporting layer for evidence schema validation and release gate report generation.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-003 - Reporting, evidence schema and release gate generator
```

## Branch

```text
qa/task-003-evidence-release-gates
```

## Scope

In scope:

- shared evidence schema documentation;
- release gate report template update;
- fail-closed local release gate report generator;
- unit tests for schema vocabulary, redaction, blocked/not-run behavior and release decision logic;
- source-of-truth updates for backlog, handoff, current state, risk register and verification memory.

Out of scope:

- runtime/device execution;
- APK/AAB/DEX/native/signing artifacts;
- source or decompiled application code;
- smali or method bodies;
- private endpoints, secrets, credentials, cookies or sessions;
- raw logs, screenshots, videos or real user data;
- executable Android runtime/device command recipes;
- production mutation, load/fuzz probing or real payments.

## Multi-agent plan

Required:

- Planner;
- Builder;
- QA Reviewer A;
- QA Reviewer B;
- Security/Prod-safety Reviewer;
- Docs/Scribe;
- Orchestrator.

## Acceptance criteria

- No forbidden artifact is requested or committed.
- No executable runtime/device recipe is added.
- Generator performs no Android, APK, network, WebView, WebRTC or production interaction.
- Missing release metadata produces `overall_status=blocked`.
- Complete public-safe metadata without runtime evidence produces only `blocked` or `not_run` runtime-dependent gate results, never a fake runtime `pass`.
- All evidence statuses normalize to `confirmed`, `likely`, `hypothesis` or `unknown`.
- Notes and artifact references are redacted by default.
- Release decision is `blocked` when any R0/R1 gate is `blocked`, `fail` or missing confirmed evidence.
- Documentation explains how TASK-001 and TASK-002 report outputs feed release gates without publishing raw evidence.
- Russian handoff report is produced.

## Verification

- `git status --short --branch`;
- `git diff --check`;
- `python -m pytest -q`;
- `python -m compileall automation tests`;
- local release gate generator dry-run with no metadata;
- local release gate generator dry-run with public-safe sample metadata;
- public-safety scan for forbidden artifacts, secrets/private endpoints, APK binaries, raw logs/screenshots and executable runtime/device recipes.
