# TASK-000 - Bootstrap Codex docs and source-of-truth

## Task

Create the initial repository source-of-truth for Codex workflow and Android QA project governance.

## Mode

`BOUNDED_AUTONOMOUS` for this run after explicit user authorization on 2026-06-05.

Default branch merge/push is allowed only after documented gates pass. Force-push remains forbidden.

## Thread title

```text
TASK-000 - Bootstrap Codex docs and source-of-truth
```

## Branch

```text
qa/task-000-bootstrap-codex-docs
```

If repository is empty and no default branch exists, initialize `main` first, then create this task branch from `main`.

## Scope

In scope:

- `AGENTS.md`;
- `CODEX_ANDROID_QA_PROJECT_TZ.md`;
- `docs/codex/*`;
- `docs/context/*`;
- `docs/tasks/backlog.md`;
- task/goal/handoff templates;
- starter pack import plan;
- public-safe reverse-analysis summary import.

Out of scope:

- Android runtime testing;
- raw APK analysis publication;
- application source/decompiled code;
- private endpoints/secrets;
- production actions.

## Multi-agent plan

Required:

- Planner;
- Documentation Auditor;
- Git/Workflow Reviewer;
- QA Strategy Reviewer;
- Security/Prod-safety Reviewer;
- Docs/Scribe;
- Orchestrator.

## Acceptance criteria

- Source-of-truth docs exist.
- Autonomy modes documented.
- Thread lifecycle documented.
- Strict multi-agent documented.
- Branch-per-task documented.
- `NON_AUTONOMOUS` and `BOUNDED_AUTONOMOUS` merge/push rules documented.
- Prod-safe policy documented.
- Initial backlog documented.
- Fresh-thread rule and subagent reuse rule documented.
- Public-safe reverse-analysis summaries exist without raw dumps or executable runtime recipes.
- Final Russian report produced.

## Verification

- `git status --short --branch`;
- inspect Markdown diff;
- scan for forbidden raw/cache/runtime artifacts;
- Security reviewer confirms no secrets/private endpoints/raw dumps;
- QA reviewer confirms starter QA areas are preserved as public-safe planning summaries.
