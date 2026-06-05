# Test Data And Fixtures Contract

Task: `TASK-006 - Test data and fixtures contract draft`

Production safety classification: `PROD_SAFE` for this document. Any future use of fixtures in runtime, device, WebView, WebRTC, network or payment-like testing is `PROD_CONDITIONAL` and remains blocked until the approval conditions in this contract and in `docs/qa/fixtures-approval-checklist.md` are satisfied.

This contract is public-safe. It must not contain real accounts, credentials, tokens, cookies, sessions, private endpoints, real payment data, raw logs, screenshots, videos, APK artifacts, endpoint inventories or executable Android runtime/device command recipes.

## Core Rule

No approved fixture, no runtime-dependent execution.

If any required approval is missing, expired, non-confirmed or outside the task scope, the dependent task status is `blocked`. Missing approval is not a soft warning and must not be treated as `not_run` when the task needs the fixture to execute.

## Evidence Status Rules

Every fixture, approval, test result, risk and release gate uses exactly one evidence status:

| Status | Meaning |
|---|---|
| `confirmed` | Backed by explicit team approval, approved runtime evidence or an approved sanitized artifact. |
| `likely` | Supported by public-safe planning context, but not approved for execution. |
| `hypothesis` | A testable expectation that still needs approval or evidence. |
| `unknown` | No sufficient approved information is available. |

Future runtime work may use a fixture only when the fixture approval itself has `evidence_status=confirmed`.

## Fixture Classes

| Fixture class | Purpose | Future safety class | Default status before approval |
|---|---|---:|---:|
| Synthetic QA users | Auth, session, profile, logout, restore and account-bound UI coverage. | `PROD_CONDITIONAL` | `blocked` |
| Auth/session states | Valid, invalid, expired, logged-out and restored session boundaries. | `PROD_CONDITIONAL` | `blocked` |
| Stream fixtures | Safe stream startup, reconnect, latency, sleep/wake and termination coverage. | `PROD_CONDITIONAL` | `blocked` |
| WebView fixtures | Legal/support/auth-like web content, redirects, cookies and offline/cache boundaries. | `PROD_CONDITIONAL` | `blocked` |
| Payment staging fixtures | Non-real-payment cancel, failure, pending, duplicate callback and success-return paths. | `PROD_CONDITIONAL` | `blocked` |
| Network/offline profiles | Approved offline, latency, packet loss, reconnect and recovery conditions. | `PROD_CONDITIONAL` | `blocked` |
| Evidence fixtures | Redacted artifact IDs, ignored local storage and report metadata. | `PROD_CONDITIONAL` | `blocked` |

## Universal Approval Conditions

Future fixture use requires all conditions below:

| Condition | Required state |
|---|---|
| Owner named | Product, QA, Security, Backend, Payments or Streaming owner is listed by role. |
| Scope bounded | Task ID, branch, environment class and allowed journey are documented. |
| Synthetic-only | No real user data, real customer state, real payment instrument or production credential is used. |
| Environment approved | The environment class is approved for the fixture. Do not publish endpoints or private environment names. |
| Resource budget | Runtime, account, stream, payment and network budgets are documented at category level. |
| Redaction approved | Logs, screenshots, videos and summaries have redaction rules before capture. |
| Evidence storage approved | Raw local artifacts, if any, stay in approved ignored storage and are not committed. |
| Cleanup approved | Mutable state has reset, cleanup, rollback or explicit no-mutation proof. |
| Audit trail | Operator, task, timestamp, fixture ID and reviewer sign-off are recorded. |
| Evidence confirmed | Approval record uses `evidence_status=confirmed`. |

If a fixture cannot satisfy all required conditions, dependent runtime tasks remain `blocked`.

## Synthetic QA Users

Synthetic QA users are test-only identities approved for repeatable QA. They must not represent real customers, employees or private user data.

Required contract fields:

| Field | Requirement |
|---|---|
| Fixture ID | Public-safe alias such as `user-auth-basic-001`. |
| Owner | Role or team that can approve, rotate, disable and reset the fixture. |
| Allowed flows | Auth entry, logout, session restore, catalog, stream guard or other category-level flow. |
| Disallowed flows | Any flow that could create real payment, real user mutation or unsupported production impact. |
| Data shape | Category-level traits only, such as `active`, `expired`, `no_entitlement` or `locked`. |
| Credential handling | Credentials are never committed, pasted into reports or stored in source docs. |
| Reset policy | Clear statement for logout, session invalidation, state reset and fixture reuse. |
| Expiry and rotation | Date or rule for review, rotation and disablement. |

Synthetic user approvals must define whether tests may create, reuse or only observe account state. Any account-bound mutable action without cleanup and rollback keeps the task `blocked`.

## Auth And Session Boundaries

Auth/session fixtures must prove boundaries without exposing tokens, cookies, session IDs or private backend details.

Required states:

| State | Purpose | Default before approval |
|---|---|---:|
| `logged_out` | Verify guarded entry and login prompt behavior. | `blocked` |
| `valid_session` | Verify permitted synthetic account journey. | `blocked` |
| `expired_session` | Verify re-auth and protected state cleanup. | `blocked` |
| `invalid_code` | Verify auth error handling with synthetic input. | `blocked` |
| `logout_reset` | Verify session removal and safe re-entry. | `blocked` |
| `restore_after_restart` | Verify state after restart or process death. | `blocked` |

Rules:

- Do not log, screenshot, commit or summarize tokens, cookies, SMS codes, credentials or session identifiers.
- Do not infer auth guard success from static planning context; runtime behavior stays `unknown` until approved evidence exists.
- Do not use real user sessions, shared employee accounts or production credentials.
- Any session mutation requires cleanup or rollback proof.

## Stream Fixtures

Stream fixtures are approved synthetic stream scenarios for WebRTC and remote-play lifecycle coverage. They must avoid real-user sessions and uncontrolled resource consumption.

Required contract fields:

| Field | Requirement |
|---|---|
| Fixture ID | Public-safe alias such as `stream-reconnect-001`. |
| Entitlement | Synthetic entitlement or approved test access only. |
| Media/session class | Category-level purpose, such as startup, reconnect, latency, black-screen recovery or safe end. |
| Capacity budget | Maximum duration, concurrency and retry budget approved at category level. |
| Network profile | Approved condition alias; no private endpoints or command recipes. |
| Expected oracle | Category-level outcome, such as preloader reaches active stream or error state is recoverable. |
| Cleanup | End session, release resource and verify account state reset where applicable. |

Rules:

- Do not start real customer streams.
- Do not perform load, endurance or concurrency tests without explicit budget.
- Do not publish WebSocket events, private media IDs, server names, endpoints or raw logs.
- Do not classify stream behavior as `confirmed` without approved runtime evidence.

## WebView Fixtures

WebView fixtures cover legal/support content, redirects, auth-like web states, cookie boundaries and offline/cache behavior.

Rules:

- Use only approved environment classes and fixture aliases.
- Do not bypass TLS, certificate pinning, WebView security controls or app security settings.
- Do not publish private URLs, redirect chains, cookies, headers, payloads or raw WebView logs.
- Use public-safe aliases for page categories, such as `web-legal-001` or `web-payment-return-001`.
- Any web auth or session fixture must follow the auth/session boundary rules above.

## Payment Staging Fixtures

Payment-like QA must use staging-only, non-real-payment fixtures.

Required states:

| State | Purpose | Default before approval |
|---|---|---:|
| `staging_cancel` | Verify safe cancel path. | `blocked` |
| `staging_failure` | Verify failure and retry copy. | `blocked` |
| `staging_pending` | Verify wait and resume behavior. | `blocked` |
| `staging_duplicate_callback` | Verify idempotent handling. | `blocked` |
| `staging_success_return` | Verify return-to-app behavior without real charge. | `blocked` |

Rules:

- Real payments are `PROD_FORBIDDEN` unless the user provides an explicit approved staging/test fixture that cannot charge real funds.
- Do not store or publish card, bank, wallet, billing token or receipt data.
- Payment callback behavior must be idempotent or reviewed by product/security before execution.
- Payment evidence must be redacted before any summary is referenced.

## Network And Offline Prerequisites

Network/offline work is `PROD_CONDITIONAL`.

Required approvals:

| Area | Requirement |
|---|---|
| Environment class | Approved QA, staging or production-like class with no private endpoint publication. |
| Network profile | Category-level alias such as `offline`, `high_latency`, `packet_loss`, `wifi_to_ethernet_switch` or `captive_portal_like`. |
| Scope and budget | Duration, retry and traffic limits. |
| No bypass | TLS, pinning, auth and security controls remain intact. |
| Cleanup | Restore normal connectivity and verify fixture state. |
| Evidence | Redacted summaries only; no packet dumps, endpoint inventories or raw logs in public docs. |

Network fixtures must not discover, extract or publish endpoints. If a test requires private endpoint knowledge, it is blocked until a public-safe category-level approval is provided.

## Redaction Policy

Redaction is required before evidence is referenced outside approved local storage.

Forbidden in public docs and committed reports:

- real names, user identifiers or account data;
- credentials, tokens, cookies, sessions, SMS codes and secrets;
- private endpoints, domains, paths, headers or payloads;
- raw logs, screenshots, videos, dumps or packet captures;
- payment instruments, receipts, billing tokens or bank data;
- APK/AAB/DEX/native/signing artifacts;
- executable Android runtime/device command recipes.

Allowed public references:

- redacted artifact IDs;
- category-level observations;
- fixture aliases;
- blocked/not-run summaries;
- reviewer sign-off and risk/unknown lists.

## Evidence Storage

Raw evidence, if approved for a future task, must stay outside public source control.

Evidence storage requirements:

| Requirement | Rule |
|---|---|
| Ignored path | Raw local evidence storage is ignored by Git before capture. |
| Minimal retention | Retain only what the task needs and only for the approved period. |
| Access boundary | Access is limited to approved QA/security roles. |
| Redacted summary | Public reports reference only redacted artifact IDs and category-level facts. |
| Review gate | Security/Prod-safety Reviewer approves redaction before publication. |

## Cleanup And Rollback

Any mutable fixture flow requires cleanup or explicit no-mutation proof.

Required cleanup examples:

| Flow | Cleanup or rollback requirement |
|---|---|
| Synthetic auth | Logout, session invalidation or account reset. |
| Stream session | End session and release stream resource. |
| Settings/profile | Restore defaults or record approved persistent change scope. |
| Payment staging | Confirm no real charge and reset staging transaction state where applicable. |
| Network/offline | Restore normal network condition and confirm app is not left in forced error state. |

If cleanup cannot be verified, dependent release gates remain `blocked`.

## Ownership And Approval

Approvals are role-based and must be recorded before use.

| Area | Required owner roles |
|---|---|
| Synthetic users | Product, QA, Security |
| Auth/session states | Product, Backend, QA, Security |
| Stream fixtures | Product, Streaming/Backend, QA, Security |
| WebView fixtures | Product, QA, Security |
| Payment staging fixtures | Product, Payments, QA, Security |
| Network/offline profiles | QA, Backend/Infra, Security |
| Evidence storage/redaction | QA, Security |
| Cleanup/rollback | Owning product/backend area plus QA |

An approval must include fixture ID, scope, expiration or review date, owner role, evidence status, allowed flows, disallowed flows, cleanup rule and redaction rule.

## Release Gate Impact

Fixture approval gates feed future release gates:

| Gate | Missing approval result |
|---|---|
| Auth/session guard | `blocked` |
| Stream lifecycle | `blocked` |
| WebView/payment-safe boundary | `blocked` |
| Network/offline recovery | `blocked` |
| Redacted evidence | `blocked` |
| Cleanup/rollback | `blocked` |

R0/R1 gates require runtime `status=pass` and `evidence_status=confirmed`. Fixture approval alone does not prove runtime behavior; it only allows future approved execution.

## Fixture Record Template

Use this public-safe shape for future approval summaries:

```text
Fixture ID: fixture-___-001
Fixture class: synthetic_user/auth_session/stream/webview/payment_staging/network/evidence
Owner role: Product/QA/Security/Backend/Payments/Streaming
Approved environment class: QA/staging/production-like category only
Allowed flows: category-level list
Disallowed flows: category-level list
Evidence status: confirmed/likely/hypothesis/unknown
Production safety classification: PROD_CONDITIONAL
Redaction rule: approved/pending/blocked
Evidence storage rule: approved ignored local storage/pending/blocked
Cleanup or rollback rule: approved/no-mutation proof/pending/blocked
Expiration or review date: YYYY-MM-DD
Approval status: approved/pending/blocked/revoked
Notes: public-safe notes only
```

Do not put credentials, endpoint values, raw account identifiers, payment data or raw evidence in fixture records.
