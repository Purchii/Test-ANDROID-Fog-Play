# EPIC-QA-041-055 master execution guide

Use one fresh Codex thread and one task branch per task. Read the corresponding
file under `docs/qa/epics/prompts/`.

Default order:

```text
TASK-041 → TASK-042 → TASK-043 → TASK-044 → TASK-045 → TASK-046
→ TASK-047 → TASK-048 → TASK-049 → TASK-050 → TASK-051 → TASK-052
→ TASK-053 → TASK-054 → TASK-055
```

Each verified completed task is merged and pushed to the actual default branch
before the next independent task starts.

The active epic is independent QA only: no production build, Android
source-level tests, programmer handoff or external prerequisite gate.
