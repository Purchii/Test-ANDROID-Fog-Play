# Exported Component Guard Planning Links

Task: `TASK-001 - Runtime discovery and smoke bootstrap`

Production safety classification: `PROD_SAFE` for planning links only. This file does not define executable device/runtime recipes.

## Purpose

Prepare traceability for future exported component guard work without performing runtime probing in TASK-001.

## Evidence Status

Use `confirmed`, `likely`, `hypothesis` or `unknown` for every future guard conclusion. TASK-001 uses `likely` only for public-safe planning links and `unknown` for runtime behavior that has not been approved and observed.

## Planning Links

| Future task | Link target | Purpose | Evidence status |
|---|---|---|---:|
| TASK-002 | `docs/tasks/backlog.md` | Exported component guard checks skeleton. | `likely` |
| TASK-002 | `docs/qa/exported-component-guard-checklist.md` | Category-level guard checklist and stop rules. | `likely` |
| TASK-002 | `docs/qa/exported-component-guard-report-template.md` | Public-safe guard report template. | `likely` |
| TASK-002 | `automation/exported_component_guards/generate_guard_report.py` | Local fail-closed guard skeleton report generator. | `likely` |
| TASK-002 | `docs/context/reverse-analysis/public-risk-summary.md` | Public-safe risk context for exported surfaces. | `likely` |
| TASK-002 | `docs/context/reverse-analysis/open-questions.md` | Product/security questions about intentional exposure and expected guards. | `unknown` |
| TASK-003 | `docs/qa/evidence-schema.md` | Shared report fields and status vocabulary. | `likely` |
| TASK-003 | `docs/qa/release-gate-report-template.md` | Release gate visibility for guard outcomes. | `likely` |

## Future Guard Categories

These categories are planning placeholders only:

| Category | Safety expectation | Current status |
|---|---|---:|
| Intentional exposure inventory | Product/security confirms which exported surfaces are expected. | `unknown` |
| Benign direct-start guard | Future checks verify protected paths do not bypass auth/session state. | `unknown` |
| Input validation | Future checks use synthetic, non-private inputs only. | `unknown` |
| No production mutation | Future checks avoid destructive or real-user-impacting state changes. | `unknown` |
| Redacted evidence | Future results include only public-safe summaries. | `unknown` |

## Stop Rules For Future Tasks

Future guard work must stop if it requires:

- source or decompiled code;
- private endpoints, secrets, tokens, cookies or sessions;
- APK patching, resigning or modification;
- security bypasses;
- real user data;
- production mutation without cleanup and rollback;
- raw artifact publication.

## TASK-001 Boundary

TASK-001 creates links and planning language only. Actual guard-check implementation belongs to TASK-002 or a later approved task with its own branch, verification plan and safety review.

## TASK-002 Boundary

TASK-002 creates the public-safe guard skeleton only. Actual runtime guard execution remains blocked until a future approved task records build, target, configuration, guard scope, fixture and redaction approvals.
