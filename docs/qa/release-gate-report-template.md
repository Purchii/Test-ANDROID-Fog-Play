# Release Gate Report Template

Task: `TASK-003 - Reporting, evidence schema and release gate generator`

Use this template for public-safe release gate summaries. Do not attach raw artifacts, raw component inventories, private endpoints, credentials or executable runtime/device recipes.

## Metadata

| Field | Value |
|---|---|
| Task ID | `TASK-___` |
| Branch | `qa/task-___` |
| Mode | `NON_AUTONOMOUS` / `BOUNDED_AUTONOMOUS` |
| Generated at UTC | `YYYY-MM-DDTHH:MM:SSZ` |
| Reporter | `role/name` |
| Production safety classification | `PROD_SAFE` / `PROD_CONDITIONAL` / `PROD_FORBIDDEN` |
| Evidence status | `confirmed` / `likely` / `hypothesis` / `unknown` |
| Overall status | `pass` / `fail` / `blocked` / `not_run` |
| Release decision | `pass` / `fail` / `blocked` / `not_run` |

## Prerequisite Gate

| Gate | Status | Evidence status | Notes |
|---|---|---:|---|
| Approved build | `pass` / `blocked` / `not_run` | `unknown` |  |
| Approved Android TV target | `pass` / `blocked` / `not_run` | `unknown` |  |
| Approved configuration | `pass` / `blocked` / `not_run` | `unknown` |  |
| Redaction policy | `pass` / `blocked` / `not_run` | `unknown` |  |
| Synthetic fixture policy | `pass` / `blocked` / `not_run` | `unknown` |  |

## Release Gate Summary

| Gate | Source | Status | Evidence status | Risk level | Notes |
|---|---|---:|---:|---:|---|
| Runtime startup reaches first visible state | TASK-001/future runtime | `not_run` | `unknown` | `R0` | Runtime execution blocked until prerequisites are approved. |
| First focus is visible and usable | TASK-001/TASK-004/future runtime | `not_run` | `unknown` | `R1` | Runtime execution blocked until prerequisites are approved. |
| Exported component guard plan exists | TASK-002 | `not_run` | `unknown` | `R1` | Skeleton exists; runtime guard behavior remains unknown. |
| Auth/session guard remains enforced | TASK-001/TASK-002/future runtime | `not_run` | `unknown` | `R0` | Requires approved synthetic fixtures and product/security expectation. |
| Evidence is redacted | TASK-003/TASK-004/future runtime | `blocked` | `unknown` | `R1` | Requires approved capture/redaction policy before raw evidence exists. |

## Release Decision

Decision: `blocked`

Decision rationale:

- R0/R1 gates require `status=pass` and `evidence_status=confirmed`.
- Missing approved build/device/config/fixtures keeps runtime-dependent gates `blocked` or `not_run`.
- TASK-003 release gate generation is local and public-safe; it does not execute runtime checks.
- TASK-004 manual maps provide public-safe screen/focus templates only; they do not execute runtime checks.

## Risks

| ID | Risk | Level | Evidence status | Mitigation |
|---|---|---:|---:|---|
| RISK-008 | Runtime tests could be claimed as passed without device/build evidence. | High | `likely` | Release gates fail closed on absent runtime evidence. |
| RISK-007 | Evidence could expose private values. | Critical | `likely` | Redaction-by-default and reviewer approval. |
| RISK-015 | Release gates could emit false confidence from blocked/not-run inputs. | High | `hypothesis` | R0/R1 gates require confirmed pass evidence. |

## Unknowns

| ID | Question | Evidence status | Owner |
|---|---|---:|---|
| U-001 | Which build is approved for runtime QA? | `unknown` | Product/QA |
| U-002 | Which Android TV target is approved? | `unknown` | QA |
| U-003 | Which fixtures and accounts are safe? | `unknown` | Product/QA/Security |
| U-007 | Which R0/R1 gate threshold is accepted for release readiness? | `unknown` | Product/QA/Security |

## Reviewer Sign-off

| Role | Result | Notes |
|---|---|---|
| QA Reviewer A | `pending` |  |
| QA Reviewer B | `pending` |  |
| Security/Prod-safety Reviewer | `pending` |  |
| Docs/Scribe | `pending` |  |

## Public-Safe Artifact References

Use only redacted artifact references or category-level summary IDs:

```json
[
  {
    "id": "artifact-runtime-summary-001",
    "type": "redacted_summary",
    "evidence_status": "confirmed",
    "note": "Approved redacted runtime summary reference."
  }
]
```

Do not include raw file contents, raw paths with private identifiers, screenshots, logs, videos, endpoint inventories or executable device/runtime commands.
