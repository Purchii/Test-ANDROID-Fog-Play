# Approval Dependency Map

Task: `TASK-012 - Safe task prioritization and approval-dependency map`

Production safety classification: `PROD_SAFE` for this document. It maps category-level approvals only. It does not grant approval, does not record private values and does not authorize runtime/device/APK/WebView/WebRTC/payment/network/live CI execution.

## Core Rule

Approvals must be explicit, scoped and `confirmed` before dependent execution can begin.

A dependency is not satisfied when it is missing, expired, revoked, out of scope, `unknown`, `hypothesis` or only `likely`. Missing approval keeps dependent work `blocked`.

## Public-Safe Approval Record Shape

Future approval summaries may use this category-level shape:

```text
Approval ID: approval-___-001
Approval area: build/target/config/fixture/redaction/storage/cleanup/budget/review
Present: true/false
Owner role: Product/QA/Security/Backend/Payments/Streaming/Infra
Scope: task ID and category-level journey only
Allowed use: category-level description
Disallowed use: category-level description
Evidence status: confirmed/likely/hypothesis/unknown
Production safety classification: PROD_CONDITIONAL when used for execution
Expiration or review date: YYYY-MM-DD
Public notes: sanitized notes only
```

Do not include secrets, private endpoints, URLs, routes, redirect chains, credentials, cookies, sessions, real account identifiers, payment data, raw logs, screenshots, videos, packet captures, APK artifacts, device serials or executable command recipes.

## Universal Approval Categories

| Approval category | Required for | Required evidence status | Default without approval |
|---|---|---:|---:|
| Approved build/APK category | Runtime/device/APK observation | `confirmed` | `blocked` |
| Approved target class | Android TV device/emulator execution | `confirmed` | `blocked` |
| Approved runtime configuration | Any runtime smoke or observation | `confirmed` | `blocked` |
| Synthetic user or account boundary | Auth/session/account-bound journeys | `confirmed` | `blocked` |
| Stream fixture boundary | WebRTC or playback lifecycle checks | `confirmed` | `blocked` |
| WebView fixture boundary | Hybrid/WebView checks | `confirmed` | `blocked` |
| Payment staging boundary | Payment-like checks | `confirmed` | `blocked` |
| Network/offline profile policy | Network variation checks | `confirmed` | `blocked` |
| Resource budget | Runtime, retry, stream, network, CI or payment attempts | `confirmed` | `blocked` |
| Redaction policy | Any evidence capture or artifact publication | `confirmed` | `blocked` |
| Evidence storage policy | Raw local artifact capture or retention | `confirmed` | `blocked` |
| Cleanup or rollback policy | Any mutable session, account, stream, payment or network state | `confirmed` | `blocked` |
| QA review | Coverage readiness and blocked/not-run expectations | `confirmed` | `blocked` |
| Security/Prod-safety review | Public safety, privacy and production safety boundary | `confirmed` | `blocked` |

## Task Dependency Matrix

| Task or task class | Depends on | Execution status until confirmed |
|---|---|---:|
| TASK-005 Android TV install/launch/focus smoke | Build/APK, target, config, fixture boundary, redaction, storage, cleanup, QA review, Security review | `blocked` |
| Runtime screen/focus observation | Build/APK, target, config, screen alias policy, input policy, redaction, storage, cleanup, reviews | `blocked` |
| Navigation transition execution | Build/APK, target, config, transition scope, input policy, fixture boundary, budget, redaction, storage, cleanup, reviews | `blocked` |
| Exported component guard execution | Approved guard scope, build/APK, target, config, redaction, storage, reviews | `blocked` |
| Stream/WebRTC lifecycle execution | Build/APK, target, config, synthetic user, stream fixture, budget, redaction, storage, cleanup, reviews | `blocked` |
| WebView execution | Build/APK, target, config, WebView fixture, synthetic user when needed, redaction, storage, cleanup, reviews | `blocked` |
| Payment-like execution | Staging-only non-real-payment fixture, synthetic user, budget, redaction, storage, cleanup, Payments review, QA review, Security review | `blocked` |
| Network/offline execution | Build/APK, target, config, network profile, budget, redaction, storage, cleanup, reviews | `blocked` |
| Compatibility/device execution | Device matrix policy, build/APK, target classes, config, fixtures, redaction, storage, cleanup, reviews | `blocked` |
| Live CI/nightly scheduling | Static scope, schedule, resource budget, dependency policy, artifact retention, redaction, QA review, Security review | `blocked` |
| Release-gate pass decisions for R0/R1 runtime gates | Runtime result `pass` plus `evidence_status=confirmed` | `blocked` |

## Approval Flow

1. Define the task scope using public-safe category names only.
2. Identify every required approval category from the matrix.
3. Confirm owner roles and expiration or review date.
4. Confirm allowed and disallowed use.
5. Confirm resource budget, redaction, evidence storage and cleanup or rollback.
6. Record only sanitized approval metadata.
7. Obtain QA and Security/Prod-safety review.
8. Keep execution `blocked` until every required approval is `confirmed`.

This flow is descriptive. It is not an executable runtime recipe.

## Blocked-By-Default Areas

The following areas are `blocked` in the absence of confirmed approvals:

| Area | Why blocked |
|---|---|
| TASK-005 runtime smoke | Build/APK, target, runtime config and fixture approvals are `unknown`. |
| Device or emulator execution | Target and execution boundary approvals are required. |
| APK handling | Approved build handling and storage boundaries are required. |
| Auth/session journeys | Synthetic user and session cleanup approvals are required. |
| Streaming/WebRTC checks | Stream fixture and resource budget approvals are required. |
| WebView and redirect checks | WebView fixture, redaction and storage approvals are required. |
| Payment-like checks | Staging-only non-real-payment approvals are required. |
| Network/offline checks | Network profile, budget and cleanup approvals are required. |
| Live CI with artifacts | Schedule, retention, dependency and redaction approvals are required. |

## Forbidden Approval Requests

Do not request or record approvals that depend on:

- application source code or decompiled code;
- extracting secrets, private endpoints or endpoint inventories;
- publishing private URLs, routes, redirect chains, headers or payloads;
- APK patching, resigning or modification;
- TLS, pinning, authentication or security-control bypass;
- real user data or real payment instruments;
- destructive production actions or load tests without explicit budget;
- raw logs, screenshots, videos, packet captures or dumps in public source control.

## Safe Unblocking Work

When execution dependencies are missing, safe next work should be limited to:

- public-safe approval templates;
- redaction and storage policy docs;
- blocked/not-run report templates;
- local static checks and docs sanity checks;
- release-gate false-pass prevention;
- category-level risk and dependency maps;
- reviewer checklists.

These activities may make future approval easier, but they do not approve execution by themselves.

## Release Gate Impact

R0/R1 release gates remain `blocked` unless both are true:

- required execution approvals are `confirmed`;
- approved execution evidence records `status=pass` and `evidence_status=confirmed`.

All other states, including `not_run`, `blocked`, `unknown`, `hypothesis` and `likely`, must fail closed for runtime-dependent release decisions.
