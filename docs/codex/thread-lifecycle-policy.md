# Codex thread lifecycle policy

## Main rule

Every new independent bounded task must start in a fresh Codex thread / agent run.

A completed task thread is historical/inactive and must not implement the next independent task.

The fresh-thread rule also applies to autonomous continuation: after one task is integrated, the next independent task starts from a new thread that reads current `main` and source-of-truth docs.

## Thread and branch naming

Thread title:

```text
TASK-001 — Runtime discovery and smoke bootstrap
```

Branch:

```text
qa/task-001-runtime-discovery-smoke-bootstrap
```

Thread title is human-readable. Branch name is Git-safe. Both must share the same task ID.

## Next task selection

If the next task is not known when a completed thread hands off:

1. Create fresh continuation thread titled `NEXT_TASK_SELECTION_FROM_<default>@<sha>`.
2. In that fresh thread, Planner reads `docs/tasks/backlog.md`.
3. Planner selects the next bounded task.
4. Rename the same fresh thread to the selected task title.
5. Create a goal and task branch in that same thread.
6. Do not create a second thread after task selection.

## create_thread-first algorithm

For new autonomous independent tasks:

```text
Attempt 1: create_thread normal/default project thread
Attempt 2: create_thread normal/default project thread
Attempt 3: create_thread normal/default project thread
Fallback: Codex Worktree / worktree thread
```

For every attempt:

- wait patiently;
- verify visible/manageable thread;
- verify repo/cwd/source docs;
- verify title/task scope;
- verify not `systemError`;
- do not run duplicate creation attempts in parallel;
- do not treat pending handles as final success/failure.

## Stable acceptance gate

A thread is accepted only if:

- it is visible/manageable;
- it can receive messages;
- it is attached to the intended repo;
- cwd/project root are correct;
- source-of-truth docs exist;
- title/task scope are correct;
- active goal matches task;
- branch/worktree state is clear;
- it is not `systemError`;
- it is not a duplicate for the same task.

## Old thread inactive statuses

After completion, set one:

```text
inactive_completed
inactive_blocked
inactive_orphan_thread_creation_attempt
```

Inactive thread may:

- write final handoff;
- record blockers;
- answer clarifying questions about its own task;
- create/send one fresh continuation thread.

Inactive thread must not:

- implement next independent task;
- create branch for next independent task;
- bypass failed thread creation by continuing locally.

## Agent cleanup

After the next fresh thread is accepted, close subagents from the previous inactive thread when they are no longer needed.

Do not close subagents whose results are still needed for review, handoff, blocker diagnosis or audit.

## Subagent reuse

Current-task subagents may be reused for follow-up review, clarification or verification inside the same task when that improves speed without reducing review quality.

Do not reuse old subagents to implement a new independent task. A new task needs a fresh Orchestrator thread and a fresh multi-agent cycle, unless a prior agent is used only as read-only historical context during handoff.
