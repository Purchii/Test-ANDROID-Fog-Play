# Task selection and backlog policy

## Source of tasks

Default source:

```text
docs/tasks/backlog.md
```

Planner may select a task only from the backlog unless the user explicitly provides a new bounded task.

## Selection criteria

Prioritize:

1. R0/R1 risk reduction.
2. Repository/source-of-truth bootstrap.
3. Runtime discovery evidence.
4. Smoke automation skeleton.
5. Exported component guards.
6. Evidence/reporting/release gates.
7. Manual runtime maps.
8. Compatibility/network/WebView/payment after fixtures.

## In fresh continuation thread

If a continuation thread starts with unknown next task:

1. read backlog;
2. choose next bounded task;
3. record rationale;
4. rename thread to task title;
5. create task goal;
6. create task branch from current default branch;
7. continue implementation in the same thread.
