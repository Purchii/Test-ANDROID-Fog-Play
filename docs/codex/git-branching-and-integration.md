# Git branching and integration rules

## Default branch

Do not assume `master` literally. Determine default branch.

User wording such as `master`, `trunk` or `default` means the actual detected repository default branch. In this repository the default branch is currently `main`.

Suggested detection:

```bash
git remote show origin | sed -n '/HEAD branch/s/.*: //p'
```

If unavailable:

```bash
git fetch origin --prune
git show-ref --verify refs/remotes/origin/main || true
git show-ref --verify refs/remotes/origin/master || true
```

If the repository is empty and the remote has no published default branch, use `main` as the initial default branch unless the user says otherwise.

For this project bootstrap, GitHub remote was empty on 2026-06-05, so `main` is the initial default branch and `qa/task-000-bootstrap-codex-docs` is created from `main`.

## Branch per task

Never implement directly on default branch.

For each task:

```bash
git fetch origin --prune
git checkout <default-branch>
git pull --ff-only origin <default-branch>
git checkout -b qa/task-xxx-short-slug
```

If worktree mode is used, verify branch/worktree state before editing.

## Task branch push

Task branch may be pushed after checks:

```bash
git push -u origin qa/task-xxx-short-slug
```

## Default branch integration

### NON_AUTONOMOUS

Forbidden without explicit user command:

```bash
git checkout <default-branch>
git merge qa/task-xxx-short-slug
git push origin <default-branch>
```

In `BOUNDED_AUTONOMOUS`, the user has authorized Codex to push verified default-branch changes autonomously after the documented gates pass. This does not allow force-push, destructive rebase, unsafe production actions or bypassing multi-agent review.

Final report must give these commands as a proposed next action, not execute them.

### BOUNDED_AUTONOMOUS

Allowed only after:

- all checks pass;
- QA reviewers approve;
- Security reviewer approves;
- docs updated;
- no R0/R1 blocker;
- no force push required;
- branch is based on current default or safely updated.

Then:

```bash
git checkout <default-branch>
git pull --ff-only origin <default-branch>
git merge --no-ff qa/task-xxx-short-slug
# rerun relevant checks if merge changes working tree
git push origin <default-branch>
```

Autonomous continuation rule:

- every completed `BOUNDED_AUTONOMOUS` task must be pushed to the remote default/trunk branch before Codex starts the next independent task;
- do not create or continue the next task branch from a stale default branch;
- if default-branch push fails, record the blocker and do not start the next task.

## Forbidden git actions

Never do without explicit user approval:

- `git push --force`;
- `git reset --hard` on shared/user changes;
- destructive rebase of default branch;
- deleting remote branches not created by the task;
- discarding uncommitted user changes;
- merging failing/unverified task branch.
