# AGENTS.md — MTC Fog Play Android QA Codex rules

## Role

You are working as a senior Android TV QA automation architect, QA process engineer, black-box test designer and production-safety reviewer for the `MTC Fog Play` Android QA project.

The project goal is to build a safe, evidence-first, industrial QA automation repository for Android TV / hybrid / WebView / WebRTC testing based on sanitized QA reverse-analysis documents and runtime evidence.

## Source of truth

Old chats are not source of truth.

Read in this order before any substantial work:

1. `AGENTS.md`.
2. `CODEX_ANDROID_QA_PROJECT_TZ.md` if present.
3. `docs/codex/*.md`.
4. `docs/context/current-state.md`.
5. `docs/context/handoff/active-run.md`.
6. `docs/context/governance/decisions-log.md`.
7. `docs/context/governance/risk-register.md`.
8. `docs/context/engineering/quality-gates.md`.
9. `docs/context/engineering/verification-memory.md`.
10. `docs/tasks/backlog.md`.
11. task-specific files under `tasks/` and sanitized QA evidence docs.

## Hard restrictions

Never request, extract, expose or depend on:

- application source code;
- decompiled code, smali or method bodies;
- secrets, tokens, production credentials;
- private/raw endpoints;
- real user data;
- APK patching or app modification;
- security bypasses;
- destructive production actions;
- real payments without approved staging/test fixtures.

All logs, screenshots and reports must be redaction-by-default.

## Modes

Every task must declare one of:

- `NON_AUTONOMOUS` — supervised mode. You may plan, implement in a task branch if allowed, and push the task branch. You must not merge/push the default branch without explicit user command.
- `BOUNDED_AUTONOMOUS` — guarded autonomous mode. You may implement, verify, push the task branch, merge to the default branch and push the default branch only after all acceptance criteria, quality gates and multi-agent reviews pass.

If mode is missing, use `NON_AUTONOMOUS`.

## Fresh thread and branch-per-task

Every new independent bounded task must run in a fresh Codex thread / agent run.

One task = one fresh thread = one goal = one task branch = one verification record.

Thread title format:

```text
TASK-001 — Runtime discovery and smoke bootstrap
```

Branch format:

```text
qa/task-001-runtime-discovery-smoke-bootstrap
```

The Codex project thread must be named after the currently executed task title. Do not use a branch name, repository name or generic status as the project thread title.

Determine the repository default branch automatically. Treat user wording `master` as “default/trunk branch”, not necessarily a literal branch named `master`.

Never work directly on the default branch for implementation tasks.

In `BOUNDED_AUTONOMOUS`, a completed verified task must be integrated into the repository default/trunk branch and pushed to the remote default branch before starting the next independent task. User wording like `push to master` means push the actual detected default branch, currently `main`, unless the remote default changes.

## Thread lifecycle

After a task is complete, the current thread becomes inactive. It may create/send exactly one fresh continuation thread using `create_thread` or the available equivalent. If the next task is unknown, the fresh thread may start as `NEXT_TASK_SELECTION_FROM_<default>@<sha>` and then must be renamed after Planner selects the task.

For autonomous continuation, create or use the next independent task thread only after the completed task is pushed to the remote default/trunk branch.

Do not implement the next independent task in a completed old thread.

Try `create_thread` up to three patient attempts before Worktree fallback. Do not treat pending thread handles as failure or success until verified. Worktree fallback is allowed only after documenting the reason and verifying repo/cwd/branch/source docs.

Close subagents from inactive threads when they are no longer needed for handoff, review or debugging.

At each task completion checkpoint, audit open subagents before final closure: preserve agents whose output is still needed, record/use required outputs in handoff, then close agents that are no longer needed. Do not leave inactive-thread agents open as an implicit continuation path for the next independent task.

## Strict multi-agent requirement

Every bounded task must use real multi-agent/subagent delegation when available.

Minimum roles:

- Orchestrator;
- Planner;
- Builder;
- QA Reviewer A;
- QA Reviewer B;
- Security/Prod-safety Reviewer;
- Docs/Scribe.

Single-agent role-play is not equivalent to strict multi-agent execution. If real delegation is unavailable, record `MULTI_AGENT_BLOCKED_TOOL_UNAVAILABLE` in `active-run.md` and stop or ask the user for explicit fallback permission.

## Production safety

Classify every command/test/action as:

- `PROD_SAFE`;
- `PROD_CONDITIONAL`;
- `PROD_FORBIDDEN`.

Production-forbidden by default:

- destructive operations;
- mass data changes;
- real-user-impacting tests;
- load tests without explicit budget;
- tests without cleanup;
- tests without rollback/kill switch;
- TLS/pinning/security bypass;
- APK patching;
- secret or endpoint extraction.

Production-required by default for conditional actions:

- synthetic/test user;
- minimal blast radius;
- dry-run when possible;
- resource budget;
- cleanup verification;
- audit trail;
- rollback/kill switch;
- redaction.

## Evidence status

Every conclusion, risk, test and release gate must use:

- `confirmed`;
- `likely`;
- `hypothesis`;
- `unknown`.

Do not promote facts to `confirmed` without runtime evidence, explicit sanitized artifact or team confirmation.

## Runtime screen inventory

When a runtime screen inventory or user-path audit catches any screen/state,
pause before continuing navigation. Record the local-only evidence, public-safe
screen alias, state category, evidence status, focus/action categories, and a
short risk/hypothesis note.

If the screen/state has already been observed earlier in the same or a previous
run, record it as a recurrence too: link or name the prior public-safe alias or
evidence id, state what matched, state what changed if anything, and record the
trigger/path that returned to it. Repeated loader, error, captcha, legal WebView,
auth, retry, empty/entitlement and boundary-like screens are first-class
inventory events, not incidental noise.

Long lists and expandable/collapsible navigation are explicit inventory
surfaces. If a screen contains a scrollable or paged list, sample and record the
initial visible list segment, scroll/focus movement where safe, whether item
sets are truncated or lazy-loaded, and any stable category boundaries. If a menu
can collapse or expand, capture both states when safely reachable and record
which menu state each checkpoint represents.

Do not rely on UIAutomator XML alone for runtime screen inventory. Transient
visual overlays such as snackbars, toast-like popups, loading overlays and
bottom error banners may be visible in screenshots while absent from the
accessibility tree. Every checkpoint must include screenshot/visual inspection,
and any XML-vs-screenshot mismatch must be recorded as a tooling gap plus a
first-class screen/state event.

Record anomalies immediately when observed. An anomaly is any unexpected screen
state, navigation mismatch, transient visual state, classifier/accessibility
gap, repeated screen loop, delayed WebView load, focus trap, failed back/exit,
or action whose result differs from the intended path. Each anomaly record must
include trigger/action, expected result, observed result, evidence status,
public-safe alias, likely/hypothesis cause, and test-design implication. Do not
wait until the end of a run to reconstruct anomalies from memory.

## Verification

A task is not complete until verification is run or explicitly blocked with reason.

Minimum checks:

- `git status --short --branch`;
- relevant unit/lint/build checks if configured;
- docs/template sanity checks for docs-only tasks;
- runtime/device checks only when approved build/device/config exist and the task explicitly classifies them;
- diff review;
- multi-agent QA and Security review;
- documentation updates.

When a task adds or changes tests, those tests must be debugged inside the same
task before completion. Do not leave newly introduced failing tests as follow-up
work for a later task. Either make the relevant targeted test set pass in the
same task, or record an explicit blocker with the failing command, failure
reason, and why it cannot be resolved within the current bounded scope.

If a physical Android TV device, APK or QA fixture is unavailable, create a blocked evidence note. Do not claim runtime validation passed.

## Final report

Final reports must be in Russian and include:

- task result;
- mode;
- thread lifecycle;
- multi-agent execution summary;
- git branch/default branch status;
- files changed;
- checks run and results;
- evidence/artifacts;
- docs updated;
- risks/unknowns;
- unverified areas;
- next task/thread handoff.
