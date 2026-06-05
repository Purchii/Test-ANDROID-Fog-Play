# Release Gate Report Template

Task: `TASK-001 - Runtime discovery and smoke bootstrap`

Use this template for public-safe gate summaries. Do not attach raw artifacts or executable runtime/device recipes.

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

## Prerequisite Gate

| Gate | Status | Evidence status | Notes |
|---|---|---:|---|
| Approved build | `pass` / `blocked` / `not_run` | `unknown` |  |
| Approved target | `pass` / `blocked` / `not_run` | `unknown` |  |
| Approved configuration | `pass` / `blocked` / `not_run` | `unknown` |  |
| Redaction policy | `pass` / `blocked` / `not_run` | `unknown` |  |
| Synthetic fixture policy | `pass` / `blocked` / `not_run` | `unknown` |  |

## Runtime Gate Summary

| Gate | Status | Evidence status | Risk level | Notes |
|---|---|---:|---:|---|
| Startup reaches first visible state | `not_run` | `unknown` | `unknown` | Runtime execution blocked until prerequisites are approved. |
| First focus is visible and usable | `not_run` | `unknown` | `unknown` | Runtime execution blocked until prerequisites are approved. |
| Focus movement avoids traps | `not_run` | `unknown` | `unknown` | Runtime execution blocked until prerequisites are approved. |
| Auth/session guard remains enforced | `not_run` | `unknown` | `unknown` | Requires approved fixtures. |
| Evidence is redacted | `not_run` | `unknown` | `unknown` | Requires approved capture policy. |

## Release Decision

Decision: `blocked`

Decision rationale:

- Approved build/device/config are not confirmed.
- Runtime behavior is `unknown`.
- TASK-001 provides foundation docs and a fail-closed local report generator only.

## Risks

| ID | Risk | Level | Evidence status | Mitigation |
|---|---|---:|---:|---|
| RISK-008 | Runtime tests could be claimed as passed without device/build evidence. | High | `likely` | Require blocked report when prerequisites are absent. |
| RISK-007 | Evidence could expose private values. | Critical | `likely` | Redaction-by-default and reviewer approval. |

## Unknowns

| ID | Question | Evidence status | Owner |
|---|---|---:|---|
| U-001 | Which build is approved for runtime QA? | `unknown` | Product/QA |
| U-002 | Which Android TV target is approved? | `unknown` | QA |
| U-003 | Which fixtures and accounts are safe? | `unknown` | Product/QA/Security |

## Reviewer Sign-off

| Role | Result | Notes |
|---|---|---|
| QA Reviewer A | `pending` |  |
| QA Reviewer B | `pending` |  |
| Security/Prod-safety Reviewer | `pending` |  |
| Docs/Scribe | `pending` |  |
