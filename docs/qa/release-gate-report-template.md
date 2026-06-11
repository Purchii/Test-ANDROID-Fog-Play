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
| Evidence storage | `pass` / `blocked` / `not_run` | `unknown` |  |
| Cleanup/rollback | `pass` / `blocked` / `not_run` | `unknown` |  |

## Release Gate Summary

| Gate ID | Gate | Source | Status | Evidence status | Risk level | Notes |
|---|---|---|---:|---:|---:|---|
| `RG-001` | Prerequisites are approved | TASK-003/future approvals | `blocked` | `unknown` | `R0` | Requires approved build, target, config, redaction and synthetic fixture metadata. |
| `RG-002` | Runtime startup reaches first visible state | TASK-001/future runtime | `not_run` | `unknown` | `R0` | Runtime execution blocked until prerequisites are approved. |
| `RG-003` | First focus is visible and usable | TASK-001/TASK-004/future runtime | `not_run` | `unknown` | `R1` | Runtime execution blocked until prerequisites are approved. |
| `RG-004` | Exported component guard plan exists | TASK-002 | `not_run` | `unknown` | `R0` | Skeleton exists; runtime guard behavior remains unknown. |
| `RG-005` | Auth/session guard remains enforced | TASK-001/TASK-002/future runtime | `not_run` | `unknown` | `R0` | Requires approved synthetic fixtures and product/security expectation. |
| `RG-006` | Evidence is redacted | TASK-003/TASK-004/future runtime | `blocked` | `unknown` | `R1` | Requires approved capture/redaction policy before raw evidence exists. |
| `RG-007` | Network/offline recovery remains bounded | TASK-007/future runtime | `not_run` | `unknown` | `R1` | Requires confirmed network profile, budget, redaction, evidence storage and cleanup before execution. |
| `RG-008` | Compatibility/device matrix baseline covered | TASK-009/future runtime | `not_run` | `unknown` | `R1` | Requires confirmed approved build, target classes, configuration, fixtures, redaction and real runtime evidence. |
| `RG-009` | WebView/payment-safe boundary remains enforced | TASK-008/future runtime | `not_run` | `unknown` | `R1` | Requires confirmed WebView fixtures, staging-only non-real-payment fixtures, redaction, cleanup and real runtime evidence. |
| `RG-010` | CI/nightly smoke readiness remains bounded | TASK-010/future CI | `not_run` | `unknown` | `R1` | Requires confirmed static CI scope, schedule policy, resource budget, artifact retention, redaction and reviewer approvals before live scheduling. |

## Release Decision

Decision: `blocked`

Decision rationale:

- R0/R1 gates require `status=pass` and `evidence_status=confirmed`.
- Missing approved build/device/config/fixtures keeps runtime-dependent gates `blocked` or `not_run`.
- TASK-003 release gate generation is local and public-safe; it does not execute runtime checks.
- TASK-004 manual maps provide public-safe screen/focus templates only; they do not execute runtime checks.
- TASK-006 fixture contract defines approval prerequisites only; fixture approval does not prove runtime behavior.
- TASK-007 network/offline safe runner creates blocked/not-run plans only; it does not execute network or runtime checks.
- TASK-008 WebView/payment safe runner creates blocked/not-run plans only; it does not execute WebView, browser, redirect, payment, network or runtime checks.
- TASK-009 compatibility/device matrix creates blocked/not-run plans only; it does not execute Android TV compatibility checks.
- TASK-010 CI/nightly smoke runner creates blocked/not-run plans only; it does not create live CI schedules, access CI secrets or execute runtime checks.

## Risks

| ID | Risk | Level | Evidence status | Mitigation |
|---|---|---:|---:|---|
| RISK-008 | Runtime tests could be claimed as passed without device/build evidence. | High | `likely` | Release gates fail closed on absent runtime evidence. |
| RISK-007 | Evidence could expose private values. | Critical | `likely` | Redaction-by-default and reviewer approval. |
| RISK-015 | Release gates could emit false confidence from blocked/not-run inputs. | High | `hypothesis` | R0/R1 gates require confirmed pass evidence. |
| RISK-019 | Network/offline checks could affect production traffic or publish private network evidence if run without approvals. | Critical | `likely` | TASK-007 keeps execution blocked until profile, budget, redaction, storage, cleanup and review are confirmed. |
| RISK-020 | Compatibility/device matrix planning could be mistaken for confirmed device coverage. | High | `likely` | TASK-009 keeps rows blocked/not-run until approved runtime evidence exists. |
| RISK-021 | WebView/payment planning could be mistaken for safe payment execution or could expose private redirect/payment data. | Critical | `likely` | TASK-008 keeps execution blocked until staging-only non-real-payment fixtures, redaction, cleanup and reviewer approvals are confirmed. |
| RISK-022 | CI/nightly smoke planning could be mistaken for live CI approval or could publish raw CI artifacts/secrets. | High | `likely` | TASK-010 keeps live scheduling blocked until scope, schedule, retention, redaction, resource budget and reviewer approvals are confirmed. |

## Unknowns

| ID | Question | Evidence status | Owner |
|---|---|---:|---|
| U-001 | Which build is approved for runtime QA? | `unknown` | Product/QA |
| U-002 | Which Android TV target is approved? | `unknown` | QA |
| U-003 | Which fixtures and accounts are safe? | `unknown` | Product/QA/Security |
| U-007 | Which R0/R1 gate threshold is accepted for release readiness? | `unknown` | Product/QA/Security |
| U-008 | Which fixture approvals are confirmed for synthetic users, streams, WebView, payment staging and network/offline work? | `unknown` | Product/QA/Security/Backend/Payments/Streaming |
| U-009 | Which network/offline profiles and recovery oracle are approved for Android TV runtime QA? | `unknown` | Product/QA/Security/Backend |
| U-010 | Which Android TV device classes, OS/API buckets and compatibility scope are approved for QA? | `unknown` | Product/QA/Security |
| U-011 | Which WebView fixtures and staging-only non-real-payment states are approved for QA? | `unknown` | Product/QA/Security/Payments |
| U-012 | Which CI/nightly scope, cadence, artifact retention and runner resource budget are approved? | `unknown` | QA/Security/DevOps |

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
