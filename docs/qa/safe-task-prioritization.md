# Safe Task Prioritization

Task: `TASK-012 - Safe task prioritization and approval-dependency map`

Production safety classification: `PROD_SAFE` for this document. It is a public-safe planning model only. It does not approve runtime/device/APK/WebView/WebRTC/payment/network/live CI execution and does not contain executable Android/device/network recipes.

## Core Rule

No confirmed approval, no runtime-dependent task execution.

When approved runtime prerequisites are missing or `unknown`, choose the next task from public-safe planning, documentation, static repository checks, fail-closed local generators, redaction policy, report templates, release-gate wiring or reviewer-readiness work.

TASK-005 Android TV install/launch/focus smoke remains `blocked` until approved build/APK, Android TV target, runtime configuration, fixture approvals, redaction policy, evidence storage and cleanup/rollback prerequisites are recorded with `evidence_status=confirmed`.

## Evidence Status

Use exactly one evidence status for every readiness statement, risk, dependency and decision:

| Status | Meaning |
|---|---|
| `confirmed` | Backed by explicit team approval, approved sanitized artifact or approved runtime evidence. |
| `likely` | Supported by public-safe planning context but not approved for execution. |
| `hypothesis` | A testable expectation that still needs approval or evidence. |
| `unknown` | No sufficient approved information is available. |

Planning documents, template rows and local dry-runs are not runtime proof. They can support `likely` planning readiness, but they do not make runtime behavior `confirmed`.

## Decision Inputs

Planner should score candidate tasks using only public-safe category-level information:

| Input | Preferred state | Evidence status before approval |
|---|---|---|
| Production safety class | `PROD_SAFE` | `confirmed` when docs-only scope is explicit |
| Dependency readiness | No runtime, secret, endpoint, account, payment or device dependency | `likely` or `confirmed` from source docs |
| Risk reduction | Reduces R0/R1 process, safety, redaction or release-gate risk | `likely` unless review confirms |
| Verification path | Local docs/static verification only | `confirmed` when commands are local and non-runtime |
| Rollback size | Small, bounded, file-limited task | `likely` until branch diff is known |
| Public repository safety | No raw/private/secret/device/APK content | `confirmed` only after diff scan |
| Reviewer independence | QA and Security can review without private inputs | `likely` until review completes |

## Prioritization Tiers

| Tier | Task class | Default action | Safety class |
|---|---|---|---|
| P0 | Source-of-truth, governance and handoff corrections | Prefer when docs are stale or contradictory | `PROD_SAFE` |
| P1 | Redaction, public-safety scans and forbidden-content guardrails | Prefer when raw/private leakage risk is high | `PROD_SAFE` |
| P2 | Fail-closed local report generators and tests that need no device or secrets | Prefer when they reduce false-pass risk | `PROD_SAFE` |
| P3 | Release-gate mapping and blocked/not-run report templates | Prefer before runtime evidence exists | `PROD_SAFE` |
| P4 | Fixture approval checklists and category-level readiness docs | Prefer when user approvals are missing | `PROD_SAFE` |
| P5 | Runtime/device/WebView/WebRTC/payment/network/live CI execution | Block until all approvals are confirmed | `PROD_CONDITIONAL` |
| P6 | Source extraction, secret discovery, endpoint inventory, APK modification, bypass or destructive production work | Reject | `PROD_FORBIDDEN` |

## Safe Next Task Decision Model

Use this ordered model for each candidate:

| Step | Question | If yes | If no |
|---|---|---|---|
| 1 | Is the task bounded to public-safe docs, static checks or local fail-closed tooling? | Continue | Move to approval dependency review |
| 2 | Does it avoid device, APK, network, WebView, WebRTC, payment, account and production interaction? | Continue | Treat as `PROD_CONDITIONAL` and block until approvals are confirmed |
| 3 | Does it avoid secrets, private endpoints, raw evidence, source code and decompiled code? | Continue | Reject or rescope |
| 4 | Can it be verified with local docs/static checks only? | Continue | Block or split into a planning-only task |
| 5 | Does it reduce a known R0/R1 risk or unblock safer future review? | Prefer | Keep proposed but lower priority |
| 6 | Is the diff small and rollback-sized? | Select | Split the task |

Recommended decision:

- Select the highest-ranked `PROD_SAFE` task that reduces a known risk and has a local verification path.
- Keep runtime-dependent tasks as `blocked` when any required approval is `unknown`, `hypothesis` or `likely`.
- Do not use the existence of a plan, template or generated blocked report as approval to run runtime checks.

## Dependency Matrix

| Task area | Current safe status | Blocking approval categories | Safe next action |
|---|---|---|---|
| TASK-005 runtime smoke | `blocked` | Build/APK, target, config, fixtures, redaction, evidence storage, cleanup/rollback, QA review, Security review | Maintain blocked note; prepare approval checklist only |
| Navigation transition execution | `blocked` | Build, target, config, navigation scope, input policy, fixtures, budget, redaction, storage, cleanup, reviews | Improve category-level map and blocked reports |
| WebView/payment execution | `blocked` | WebView fixture policy, staging-only non-real-payment policy, synthetic user boundary, budget, redaction, storage, cleanup, reviews | Keep payment-safe plan category-level |
| Network/offline execution | `blocked` | Network profile policy, budget, redaction, storage, cleanup, reviews | Keep local runner fail-closed |
| Compatibility/device execution | `blocked` | Device matrix approval, build, target, config, fixtures, redaction, storage, cleanup, reviews | Maintain public-safe matrix aliases |
| Live CI/nightly scheduling | `blocked` | Static scope, schedule, resource budget, dependency policy, artifact retention, redaction, reviews | Keep CI planning local and disabled |
| Release-gate planning | `not_run` or `blocked` until evidence exists | Confirmed runtime evidence for R0/R1 pass gates | Improve templates and false-pass tests |
| Public docs and process maps | `ready_for_docs_work` | None beyond docs-only review | Prefer when runtime prerequisites are missing |

## Approval-Aware Selection Examples

| Candidate | Decision | Rationale |
|---|---|---|
| Add a public-safe approval dependency map | Select | Docs-only, local verification, reduces unsafe task selection risk |
| Add a redaction checklist for future evidence | Select | Public-safe and reduces leakage risk |
| Run Android TV launch smoke | Block | TASK-005 prerequisites are still not `confirmed` |
| Enable live nightly CI with device lane | Block | Runtime lane, schedule and artifact approvals are not confirmed |
| Document payment staging fixture categories | Select if category-level only | Planning is safe; execution remains blocked |
| Publish endpoint inventory or raw redirect data | Reject | `PROD_FORBIDDEN` public-repo content |

## Verification Expectations

For public-safe prioritization tasks:

- inspect changed Markdown diff;
- run `git diff --check`;
- verify ASCII-only deliverables when required;
- scan changed files for forbidden public-repo content categories;
- record runtime/device/APK/WebView/WebRTC/payment/network/live CI as `not_run` or `blocked`, not `passed`.

For conditional future execution tasks, verification cannot start until every required approval has `evidence_status=confirmed`.

## Handoff Rule

If Planner cannot find a `PROD_SAFE` next task, the correct state is not to force runtime work. The correct state is:

- keep TASK-005 and other runtime-dependent tasks `blocked`;
- request the missing category-level approvals through the approved project process;
- create only public-safe proposed tasks that clarify prerequisites, risks, redaction, storage, cleanup or release-gate impact.
