# Decisions log

| ID | Date | Decision | Status | Rationale | Consequences |
|---|---|---|---|---|---|
| DEC-001 | 2026-06-05 | Use repository docs, not old chats, as source of truth. | accepted | Prevent context drift and stale decisions. | Codex must update docs for persistent rules. |
| DEC-002 | 2026-06-05 | Every independent bounded task starts in a fresh Codex thread. | accepted | Reduces context rot and keeps tasks isolated. | Completed threads become inactive. |
| DEC-003 | 2026-06-05 | Use strict multi-agent workflow for every bounded task. | accepted | User requires maximum quality and independent review. | If real subagents unavailable, task is blocked or needs explicit fallback approval. |
| DEC-004 | 2026-06-05 | One task branch per task, created from current default branch. | accepted | Prevents cross-task contamination and simplifies rollback. | Next task starts only after previous integration policy is satisfied. |
| DEC-005 | 2026-06-05 | In NON_AUTONOMOUS mode, default branch merge/push requires explicit user command. | accepted | Supervised safety. | Codex can push task branch but not trunk. |
| DEC-006 | 2026-06-05 | In BOUNDED_AUTONOMOUS mode, fully verified task branch may be merged/pushed to default branch. | accepted | Enables unattended progress with gates. | Requires tests, docs, QA/security approval, no R0/R1 blockers. |
| DEC-007 | 2026-06-05 | Thread title uses task ID + human title; branch uses same ID + Git-safe slug. | accepted | Better UI readability and Git traceability. | Temporary next-task thread must be renamed after Planner selects task. |
| DEC-008 | 2026-06-05 | GitHub remote was empty, so initial default branch is `main`. | accepted | No remote HEAD or branches existed; `main` is the GitHub default convention. | TASK-000 branches from `main`. |
| DEC-009 | 2026-06-05 | Task branches use the `qa/task-xxx-slug` format. | accepted | Starter pack and user preference allow `qa/`; it keeps QA task branches grouped. | Branch names must include task ID. |
| DEC-010 | 2026-06-05 | In `BOUNDED_AUTONOMOUS`, Codex may push verified default branch changes autonomously. | accepted | User authorized autonomous continuation beyond TASK-000. | Requires documented gates, no force-push and multi-agent review. |
| DEC-011 | 2026-06-05 | New independent tasks must start in fresh threads; current agents may be reused only when it does not reduce speed or quality. | accepted | Keeps task context clean while allowing efficient same-task review. | NEXT task after TASK-000 needs a fresh thread. |
| DEC-012 | 2026-06-05 | Public repo source-of-truth excludes raw reverse-analysis artifacts, archives and compiled cache files. | accepted | Repository is public and first commit defines public history. | Commit public-safe summaries only; exclude `raw/`, `.pyc` and zip by default. |
| DEC-013 | 2026-06-05 | Codex project thread title must match the currently executed task title. | accepted | Human-readable task names make project navigation and handoff safer than branch names or generic labels. | Every new task thread must be named like `TASK-001 - Runtime discovery and smoke bootstrap`. |
| DEC-014 | 2026-06-05 | Every task completion includes an explicit subagent closure audit. | accepted | Prevents inactive-thread agents from lingering after their review/handoff/debug purpose is finished. | Orchestrator must keep needed agents until outputs are captured, then close no-longer-needed agents before final task closure. |
