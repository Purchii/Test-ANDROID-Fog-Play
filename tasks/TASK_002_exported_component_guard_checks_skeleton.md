# TASK-002 - Exported component guard checks skeleton

## Task

Create the public-safe exported component guard checks skeleton for future Android TV black-box QA.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-002 - Exported component guard checks skeleton
```

## Branch

```text
qa/task-002-exported-component-guards
```

## Scope

In scope:

- exported component guard checklist;
- exported component guard report template;
- fail-closed local guard report generator;
- unit tests for missing metadata, redaction and no-runtime behavior;
- source-of-truth updates for backlog, handoff, risks and verification memory.

Out of scope:

- runtime/device execution;
- direct component launch/probing;
- source or decompiled code;
- smali or method bodies;
- raw manifest/component inventories;
- private package/class names, endpoints, secrets or credentials;
- APK patching, resigning or modification;
- real payments, production mutation or load/fuzz probing.

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
- No executable device/runtime recipe is added.
- No raw component names, private app identifiers, endpoints, secrets, logs or screenshots are published.
- Missing approved build/target/config/guard scope produces `overall_status=blocked`.
- Complete public-safe metadata produces only a `not_run` guard plan, never a fake runtime `pass`.
- Every conclusion uses `confirmed`, `likely`, `hypothesis` or `unknown`.
- Runtime/device execution remains blocked until a future task records approved prerequisites.
- Russian handoff report is produced.

## Verification

- `git status --short --branch`;
- `git diff --check`;
- `python -m pytest -q`;
- `python -m compileall automation tests`;
- local guard report dry-run with no metadata;
- public-safety scan for forbidden artifacts, secrets/private endpoints, APK binaries, raw logs/screenshots and executable runtime/device recipes.
