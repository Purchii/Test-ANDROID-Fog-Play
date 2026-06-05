# Fixtures Approval Checklist

Task: `TASK-006 - Test data and fixtures contract draft`

Production safety classification: `PROD_SAFE` for this checklist. Future fixture use is `PROD_CONDITIONAL` and must remain `blocked` until all required approvals are confirmed.

Use this checklist before any task attempts runtime, device, auth/session, stream, WebView, payment, network or offline fixture execution. This checklist is public-safe and must not include credentials, private endpoints, raw accounts, real payment data, raw evidence or executable Android runtime/device command recipes.

## Approval Summary

| Field | Value |
|---|---|
| Task ID | `TASK-___` |
| Branch | `qa/task-___` |
| Mode | `NON_AUTONOMOUS` / `BOUNDED_AUTONOMOUS` |
| Fixture owner role | `Product/QA/Security/Backend/Payments/Streaming` |
| Fixture class | `synthetic_user/auth_session/stream/webview/payment_staging/network/evidence` |
| Fixture ID | `fixture-___-001` |
| Environment class | `QA/staging/production-like category only` |
| Production safety classification | `PROD_CONDITIONAL` |
| Evidence status | `confirmed` / `likely` / `hypothesis` / `unknown` |
| Approval status | `approved` / `pending` / `blocked` / `revoked` |
| Review date | `YYYY-MM-DD` |

## Fail-Closed Gate

If any required row below is not `approved` with `evidence_status=confirmed`, runtime-dependent use of the fixture is `blocked`.

| Gate | Required status | Evidence status | Notes |
|---|---|---:|---|
| Owner named | `approved` | `confirmed` | Owner role can approve, revoke and reset the fixture. |
| Scope bounded | `approved` | `confirmed` | Task, branch, fixture class and allowed journey are documented. |
| Synthetic-only data | `approved` | `confirmed` | No real user, credential, endpoint or payment data. |
| Environment class approved | `approved` | `confirmed` | Public-safe class only; no private endpoint values. |
| Resource budget approved | `approved` | `confirmed` | Duration, retry, stream, payment and network budgets are bounded. |
| Redaction policy approved | `approved` | `confirmed` | Evidence can be redacted before publication. |
| Evidence storage approved | `approved` | `confirmed` | Raw artifacts stay in ignored approved local storage. |
| Cleanup/rollback approved | `approved` | `confirmed` | Mutable state has reset, rollback or no-mutation proof. |
| Security review | `approved` | `confirmed` | No secret, privacy, payment, endpoint or bypass blocker. |
| QA review | `approved` | `confirmed` | Test oracle and blocked behavior are understood. |

## Synthetic QA User Checklist

| Item | Status | Evidence status | Notes |
|---|---|---:|---|
| Fixture ID is public-safe alias only | `pending` | `unknown` | Example shape: `user-auth-basic-001`. |
| Account is synthetic/test-only | `pending` | `unknown` | No real customer or employee data. |
| Credential handling is outside repo | `pending` | `unknown` | No secrets in docs, commits or reports. |
| Allowed auth/session flows are listed | `pending` | `unknown` | Category-level only. |
| Disallowed flows are listed | `pending` | `unknown` | Real payment and unsupported mutation blocked. |
| Logout/session reset is defined | `pending` | `unknown` | Cleanup required for reuse. |
| Expiration or rotation rule exists | `pending` | `unknown` | Prevent stale shared fixtures. |

## Auth And Session Checklist

| Item | Status | Evidence status | Notes |
|---|---|---:|---|
| Logged-out state fixture approved | `pending` | `unknown` | Guard behavior can be tested. |
| Valid synthetic session fixture approved | `pending` | `unknown` | No token or cookie values recorded. |
| Expired session fixture approved | `pending` | `unknown` | Re-auth behavior can be tested. |
| Invalid input fixture approved | `pending` | `unknown` | Synthetic-only input. |
| Session restore boundary approved | `pending` | `unknown` | Restart/process-death scenario. |
| Session cleanup verified | `pending` | `unknown` | Logout/reset or equivalent. |

## Stream Fixture Checklist

| Item | Status | Evidence status | Notes |
|---|---|---:|---|
| Stream fixture alias approved | `pending` | `unknown` | No private media or server identifiers. |
| Synthetic entitlement approved | `pending` | `unknown` | No real customer stream. |
| Duration and retry budget approved | `pending` | `unknown` | Prevent uncontrolled resource use. |
| Concurrency budget approved | `pending` | `unknown` | No load test without explicit budget. |
| Expected stream oracle documented | `pending` | `unknown` | Category-level result only. |
| End-session cleanup defined | `pending` | `unknown` | Release resource and reset state. |
| Evidence redaction approved | `pending` | `unknown` | No raw WebRTC, WebSocket or media logs in public docs. |

## WebView Checklist

| Item | Status | Evidence status | Notes |
|---|---|---:|---|
| WebView fixture alias approved | `pending` | `unknown` | Page category alias only. |
| Environment class approved | `pending` | `unknown` | No private URLs or redirect chains. |
| Cookie/session boundary approved | `pending` | `unknown` | No cookies, headers or tokens recorded. |
| Offline/cache scenario approved | `pending` | `unknown` | Network profile must be approved. |
| TLS/security controls preserved | `pending` | `unknown` | No bypass or pinning changes. |
| D-pad/back behavior oracle documented | `pending` | `unknown` | Public-safe expected outcome. |

## Payment Staging Checklist

| Item | Status | Evidence status | Notes |
|---|---|---:|---|
| Staging-only fixture approved | `pending` | `unknown` | Must not charge real funds. |
| Non-real payment instrument boundary approved | `pending` | `unknown` | No card, wallet, bank or billing token data. |
| Cancel path approved | `pending` | `unknown` | Safe no-charge path. |
| Failure path approved | `pending` | `unknown` | Safe no-charge path. |
| Pending path approved | `pending` | `unknown` | Safe wait/resume path. |
| Duplicate callback behavior approved | `pending` | `unknown` | Idempotency expectation documented. |
| Payment cleanup/rollback approved | `pending` | `unknown` | Staging transaction reset or no-mutation proof. |
| Security/payment owner sign-off exists | `pending` | `unknown` | Required before execution. |

## Network And Offline Checklist

| Item | Status | Evidence status | Notes |
|---|---|---:|---|
| Network profile alias approved | `pending` | `unknown` | Example shape: `offline` or `high_latency`; no command recipes. |
| Scope and duration approved | `pending` | `unknown` | Prevent accidental load or disruption. |
| Retry budget approved | `pending` | `unknown` | Avoid uncontrolled backend pressure. |
| Environment class approved | `pending` | `unknown` | No private endpoint publication. |
| TLS/security controls preserved | `pending` | `unknown` | No bypass. |
| Normal network restoration defined | `pending` | `unknown` | Cleanup required. |
| Evidence redaction approved | `pending` | `unknown` | No packet dumps or raw logs in public docs. |

## Evidence And Redaction Checklist

| Item | Status | Evidence status | Notes |
|---|---|---:|---|
| Raw evidence storage path is ignored | `pending` | `unknown` | Do not commit raw artifacts. |
| Redacted artifact ID scheme approved | `pending` | `unknown` | Public reports use aliases only. |
| Screenshot/video/log redaction approved | `pending` | `unknown` | Required before capture. |
| Endpoint and secret redaction approved | `pending` | `unknown` | No endpoint inventories. |
| Reviewer sign-off required before publish | `pending` | `unknown` | Security/Prod-safety gate. |
| Retention and deletion rule exists | `pending` | `unknown` | Minimal retention. |

## Stop Conditions

Stop fixture use and mark the dependent task `blocked` when any condition is true:

- approval is missing, expired, revoked or non-confirmed;
- fixture would require real credentials, tokens, cookies, sessions or private endpoints;
- fixture would use real user data, real accounts or real payment instruments;
- payment path is not staging-only and non-real-payment;
- stream path could consume uncontrolled resources or affect real users;
- network/offline profile lacks budget, cleanup or security review;
- evidence cannot be redacted before publication;
- cleanup or rollback cannot be verified;
- task would require APK patching, source/decompiled analysis, security bypass, destructive production action or executable Android runtime/device command recipes.

## Reviewer Sign-Off

| Role | Result | Evidence status | Notes |
|---|---|---:|---|
| Product owner | `pending` | `unknown` |  |
| QA owner | `pending` | `unknown` |  |
| Security/Prod-safety Reviewer | `pending` | `unknown` |  |
| Backend/Streaming owner | `pending` | `unknown` | Required for auth, session, stream or network fixtures. |
| Payments owner | `pending` | `unknown` | Required for payment staging fixtures. |
| Docs/Scribe | `pending` | `unknown` | Confirms public-safe summary only. |

## Approval Decision

Decision: `blocked` until every required gate for the selected fixture class is `approved` with `evidence_status=confirmed`.

Decision rationale:

- Fixture approval allows future execution planning only; it does not confirm runtime behavior.
- Runtime results require approved execution evidence and independent QA/Security review.
- Public docs must stay redaction-by-default.
