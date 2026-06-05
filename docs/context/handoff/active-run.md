# Active run

## Run metadata

Mode: `BOUNDED_AUTONOMOUS`
Thread title: `TASK-000 - Bootstrap Codex docs and source-of-truth`
Thread status: `completed_pending_final_report`
Fresh thread verified: `yes_current_task_started_before_policy_finalization`
Task ID: `TASK-000`
Task branch: `qa/task-000-bootstrap-codex-docs`
Default branch: `main`
Base commit: `9c5e079`
Production safety classification: `PROD_SAFE` for docs/bootstrap only
Multi-agent status: `active`
Merge/push authority: `BOUNDED_AUTONOMOUS - default branch push allowed after gates`

## Goal

Bootstrap repository documentation and Codex workflow rules for Android QA project.

## Scope

In scope:

- create/update `AGENTS.md`;
- create/update `CODEX_ANDROID_QA_PROJECT_TZ.md`;
- create/update `docs/codex/*`;
- create/update `docs/context/*`;
- create/update `docs/tasks/backlog.md`;
- import public-safe starter docs;
- create initial task prompts;
- document fresh-thread and subagent reuse rules.

Out of scope:

- app source/decompiled analysis;
- APK modification;
- runtime/device execution;
- real credentials/payments;
- production actions;
- raw reverse-analysis dumps or compiled cache artifacts.

## Acceptance criteria

- Source-of-truth docs exist.
- Thread lifecycle policy documented.
- Strict multi-agent policy documented.
- Autonomy modes documented.
- Git branch integration policy documented.
- Prod-safe policy documented.
- Initial backlog exists.
- Public-safe reverse-analysis summaries exist.
- Final Russian report produced.

## Verification plan

- `git status --short --branch`;
- Markdown file sanity/readability check;
- inspect diff;
- multi-agent reviews;
- no secrets/private endpoints introduced;
- no raw reverse-analysis dumps, compiled cache files or executable runtime recipes committed.

## Verification result

- Local git baseline created: `main` at `9c5e079`.
- Task branch created from `main`: `qa/task-000-bootstrap-codex-docs`.
- Docs/security/QA multi-agent reviews: `PASS`.
- Staged forbidden artifact scan: `PASS`.
- `git diff --cached --check`: `PASS`.
- Runtime/device checks: not run; out of scope for TASK-000.

## Stop conditions

- real subagents unavailable and no explicit fallback is allowed;
- any file appears to contain secrets/private endpoints;
- multi-agent review identifies unresolved R0/R1 blocker;
- force-push or destructive default-branch rewrite would be required.
