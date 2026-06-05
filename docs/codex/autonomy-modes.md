# Codex autonomy modes

## Modes

The project supports two explicit modes:

- `NON_AUTONOMOUS` — supervised mode.
- `BOUNDED_AUTONOMOUS` — guarded autonomous mode.

Autonomy is never implicit. Every task prompt, goal and `docs/context/handoff/active-run.md` must declare the mode.

If mode is missing, default to `NON_AUTONOMOUS`.

---

## NON_AUTONOMOUS

Use for:

- first repository bootstrap;
- unknown scope;
- planning;
- policy changes;
- production-risk tasks;
- tasks needing user/product/security approval.

Allowed:

- inspect repository;
- read docs;
- spawn planning/review subagents;
- create task plan;
- create task branch if prompt permits;
- implement bounded task branch if approved;
- run safe checks;
- push task branch if approved by task prompt.

Forbidden without explicit user command:

- merge task branch into default branch;
- push default branch;
- run production-impact commands;
- use real credentials/payments/user data;
- expand task scope;
- perform destructive git operations.

Final state:

- task branch pushed or local diff ready;
- default branch untouched unless user explicitly commanded merge/push;
- final report gives exact next approval needed.

---

## BOUNDED_AUTONOMOUS

Use only when all are true:

- fresh task thread exists;
- task has a bounded goal;
- task branch is created from current default branch;
- strict multi-agent cycle is available;
- acceptance criteria are explicit;
- verification commands are known;
- production-safety classification is `PROD_SAFE` or satisfied `PROD_CONDITIONAL`;
- no external product/security decision is required.

Allowed:

- implement within scope;
- run checks;
- update docs;
- push task branch;
- merge verified task branch into default branch;
- push default branch;
- create the next fresh thread after completion.

Required before autonomous continuation:

- after a `BOUNDED_AUTONOMOUS` task is complete and gates pass, Codex must merge the verified task branch into the detected default/trunk branch and push that default branch before starting the next independent task;
- user wording such as `master` means the repository default/trunk branch, not necessarily a literal branch named `master`.

Stop and ask when:

- tests fail and cannot be fixed within scope;
- R0/R1 risk appears;
- production action is not clearly safe;
- credentials/private endpoints/real data are needed;
- branch conflicts imply scope expansion;
- real subagents are unavailable;
- fresh thread cannot be created or accepted.

---

## Active-run required fields

`docs/context/handoff/active-run.md` must include:

```text
Mode:
Thread title:
Thread status:
Fresh thread verified:
Task ID:
Task goal:
Task branch:
Default branch:
Base commit:
Production safety classification:
Multi-agent status:
Allowed files:
Forbidden files/actions:
Acceptance criteria:
Verification plan:
Merge/push authority:
Stop conditions:
```
