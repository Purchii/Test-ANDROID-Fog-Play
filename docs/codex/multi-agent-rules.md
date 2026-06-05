# Strict multi-agent rules

## Requirement

Every bounded task must use strict multi-agent workflow.

Single-agent role-playing is not enough for completed work.

If real subagent/delegation tooling is unavailable:

- record `MULTI_AGENT_BLOCKED_TOOL_UNAVAILABLE` in `active-run.md`;
- do not mark the task complete;
- ask user whether to allow temporary fallback.

## Required roles

Minimum required roles for every task:

| Role | Responsibility |
|---|---|
| Orchestrator | Owns run framing, scope, thread lifecycle, final consolidation. |
| Planner | Reads source-of-truth, defines task plan, files, acceptance, verification. |
| Builder | Implements only accepted bounded scope. |
| QA Reviewer A | Checks acceptance criteria, tests, edge cases. |
| QA Reviewer B | Checks Android TV/runtime/evidence/flakiness perspective. |
| Security/Prod-safety Reviewer | Checks prod safety, secrets, privacy, destructive actions, exported component risk. |
| Docs/Scribe | Updates docs, active-run, verification-memory, decisions-log, handoff. |

Optional roles:

- Android TV Automation Reviewer;
- Streaming/WebRTC Reviewer;
- WebView/Hybrid Reviewer;
- CI/Tooling Reviewer;
- Release Gate Reviewer.

## Execution order

1. Orchestrator frames the run.
2. Planner produces plan before implementation.
3. Security/Prod-safety Reviewer approves/blocks plan.
4. Builder implements.
5. QA Reviewer A reviews tests/acceptance.
6. QA Reviewer B reviews runtime risks/flakiness/evidence.
7. Security/Prod-safety Reviewer repeats final safety review.
8. Docs/Scribe updates memory docs.
9. Orchestrator consolidates final Russian report.

## Independence rules

QA reviewers must not simply trust Builder output.

They must inspect:

- diff;
- changed files;
- acceptance criteria;
- verification logs;
- docs updates;
- unverified zones;
- production safety classification.

Any R0/R1 concern blocks merge/push to default branch until resolved or explicitly signed off.
