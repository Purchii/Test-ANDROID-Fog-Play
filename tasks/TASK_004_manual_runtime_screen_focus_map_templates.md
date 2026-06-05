# TASK-004 - Manual runtime screen and TV focus map templates

## Task

Create public-safe manual runtime screen and Android TV focus map templates for future approved runtime observation.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-004 - Manual runtime screen and TV focus map templates
```

## Branch

```text
qa/task-004-runtime-screen-focus-map
```

## Context

TASK-001 created runtime discovery and startup/focus smoke planning. TASK-003 added shared reporting and fail-closed release gate behavior. TASK-004 adds the manual mapping layer needed before automated Android TV focus smoke execution.

## Scope

In scope:

- manual runtime screen map template;
- manual Android TV focus map template;
- public-safe map report expectations and blocked/not-run behavior;
- local fail-closed screen/focus map report generator;
- unit tests for missing metadata, no-runtime behavior, redaction and invalid status normalization;
- source-of-truth updates for backlog, handoff, current state, quality/verification memory and risks.

Out of scope:

- runtime/device execution;
- APK/AAB/DEX/native/signing artifacts;
- source or decompiled application code;
- smali or method bodies;
- private endpoints, secrets, credentials, cookies or sessions;
- raw logs, screenshots, videos, endpoint inventories or real user data;
- executable Android runtime/device command recipes;
- production mutation, load/fuzz probing or real payments.

## Constraints

- Runtime behavior remains `unknown` until approved runtime evidence exists.
- Public docs may reference redacted artifact IDs or category-level summaries only.
- Screens, routes and focus targets must use public-safe aliases rather than private package/class names, raw text with user data or endpoint-like values.
- Every conclusion must use `confirmed`, `likely`, `hypothesis` or `unknown`.
- TASK-004 local tooling must not report runtime `pass`.

## Required workflow

- Orchestrator frames scope, branch and verification.
- Planner confirms scope and acceptance criteria.
- Security/Prod-safety Reviewer checks public-safety boundaries before and after implementation.
- Builder implements bounded generator/test scope.
- QA Reviewer A checks acceptance criteria and tests.
- QA Reviewer B checks Android TV focus/runtime evidence gaps.
- Docs/Scribe checks source-of-truth updates.

## Acceptance criteria

- No forbidden artifact is requested or committed.
- No executable runtime/device recipe is added.
- Manual runtime screen map template exists and is linked from source-of-truth docs.
- Manual TV focus map template exists and is linked from source-of-truth docs.
- Templates include prerequisites, evidence status, redaction, screen aliases, transition mapping, initial focus, D-pad movement, focus trap, Back/Home and accessibility/localization fields.
- Missing approved metadata produces `overall_status=blocked`.
- Complete public-safe metadata produces only a `not_run` mapping plan, never a fake runtime `pass`.
- Notes and artifact-like references are redacted by default.
- Runtime/device execution remains blocked until a future task records approved prerequisites.
- Russian final/handoff report is produced.

## Verification

- `git status --short --branch`;
- `git diff --check`;
- `python -m pytest -q`;
- `python -m compileall automation tests`;
- local screen/focus map generator dry-run with no metadata;
- local screen/focus map generator dry-run with public-safe sample metadata;
- public-safety scan for forbidden artifacts, secrets/private endpoints, APK binaries, raw logs/screenshots, endpoint inventories and executable runtime/device recipes.

## Documentation updates

- `docs/qa/runtime-screen-map-template.md`;
- `docs/qa/tv-focus-map-template.md`;
- `docs/qa/evidence-schema.md`;
- `docs/qa/release-gate-report-template.md`;
- `docs/context/current-state.md`;
- `docs/context/handoff/active-run.md`;
- `docs/context/governance/risk-register.md`;
- `docs/context/engineering/quality-gates.md`;
- `docs/context/engineering/verification-memory.md`;
- `docs/tasks/backlog.md`;
- `automation/README.md`.

## Stop conditions

Stop and ask for user guidance if the task would require runtime/device execution, APK handling, source/decompiled analysis, private endpoints, credentials, raw evidence publication, production mutation, real payments, failing quality gates, unavailable real subagents or R0/R1 reviewer blockers.
