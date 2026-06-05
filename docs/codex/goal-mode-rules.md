# Goal-mode rules

## Goal shape

Every task must have one bounded goal.

Goal prompt must include:

- Task;
- Context;
- Source of truth;
- Scope;
- Out of scope;
- Constraints;
- Required workflow;
- Multi-agent plan;
- Acceptance criteria;
- Verification;
- Documentation updates;
- Final report;
- Stop conditions.

## Forbidden goals

Do not use broad goals:

- “make the project production-ready”;
- “implement all QA automation”;
- “fix everything”;
- “cover all tests”;
- “improve architecture everywhere”.

## Planning boundary

In `NON_AUTONOMOUS`, Codex stops after plan unless prompt explicitly allows implementation.

In `BOUNDED_AUTONOMOUS`, Codex may implement only inside accepted goal scope.

## Goal completion

A goal is complete only when:

- deliverables exist;
- verification is complete or blocked with reason;
- QA reviewers approve;
- Security/Prod-safety reviewer approves;
- docs updated;
- final report produced;
- thread handoff prepared.
