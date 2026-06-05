# WebView Payment Safe QA Plan

Task: `TASK-008 - WebView/payment safe QA plan`

Production safety classification: `PROD_SAFE` for this plan and local report generation. Any future WebView, browser redirect or payment-like runtime execution is `PROD_CONDITIONAL` and remains blocked until approved build, target, configuration, WebView fixture, staging-only non-real-payment fixture, synthetic user, resource budget, redaction, evidence storage, cleanup, Security review and QA review prerequisites are recorded with `evidence_status=confirmed`.

This document is public-safe. It must not contain private URLs, redirect chains, endpoints, headers, payloads, cookies, tokens, sessions, credentials, real user data, real payment data, raw logs, screenshots, videos, APK artifacts, packet captures, proxy configuration, TLS bypass details or executable Android runtime/device/network recipes.

## Core Rule

No confirmed staging-only fixture approval, no WebView/payment execution.

TASK-008 tooling creates a local JSON plan only. It does not interact with Android, a device, APK, WebView, browser, redirect target, payment surface, backend, network service or production environment.

## Evidence Status

Use exactly one evidence status for every prerequisite, planned check, risk and report field:

| Status | Meaning |
|---|---|
| `confirmed` | Backed by explicit approved metadata, team approval or approved sanitized artifact. |
| `likely` | Supported by planning context but not approved for execution. |
| `hypothesis` | A testable expectation that still needs approval or evidence. |
| `unknown` | No sufficient approved information is available. |

Only `evidence_status=confirmed` with `present=true` satisfies a prerequisite.

## Required Prerequisites

| Prerequisite | Required public-safe approval |
|---|---|
| `approved_build` | Approved build identifier and handling rules exist outside this report. |
| `approved_target` | Approved Android TV target category is in scope. |
| `approved_config` | Approved configuration and environment class are known without endpoint values. |
| `webview_fixture_policy` | Approved WebView page categories, redirects and cookie boundaries are described by public-safe aliases only. |
| `payment_staging_policy` | Approved staging-only, non-real-payment fixture states and disallowed real-payment flows are documented. |
| `synthetic_user_policy` | Approved synthetic user/session boundaries exist for any account-bound WebView/payment path. |
| `resource_budget` | Duration, retry, account, redirect and payment-attempt budgets are bounded. |
| `redaction_policy` | Evidence redaction rules are approved before capture. |
| `evidence_storage` | Raw evidence, if approved later, stays in ignored local storage. |
| `cleanup_rollback` | Mutable fixture state, sessions and staging transactions have reset or no-mutation proof. |
| `security_review` | Security/Prod-safety Reviewer approves the boundary. |
| `qa_review` | QA Reviewer approves coverage and blocked/not-run expectations. |

Missing, malformed, non-object, `present` not true or non-confirmed prerequisite metadata keeps the report `blocked`.

## Public-Safe Fixture Aliases

Use aliases and categories. Never publish URLs, redirect chains, accounts or payment identifiers.

| Alias class | Purpose | Default status |
|---|---|---:|
| `web-legal-001` | Future legal/support content rendering category. | `blocked` |
| `web-auth-boundary-001` | Future auth-like WebView state and session boundary category. | `blocked` |
| `web-offline-cache-001` | Future WebView unavailable/cache/error category. | `blocked` |
| `payment-cancel-001` | Future staging-only cancel path category. | `blocked` |
| `payment-failure-001` | Future staging-only failure path category. | `blocked` |
| `payment-pending-001` | Future staging-only pending/resume category. | `blocked` |
| `payment-duplicate-return-001` | Future idempotent duplicate return category. | `blocked` |
| `payment-success-return-001` | Future staging-only success-return category with no real charge. | `blocked` |

Forbidden public fixture fields include private URL, host, path, query, redirect chain, cookies, headers, payloads, account identifiers, receipt identifiers, billing tokens, card, wallet, bank data and raw WebView logs.

## Planned Check Categories

TASK-008 report output may include these categories only as `not_run` with `evidence_status=unknown`:

| Check | Purpose |
|---|---|
| `webview_render_guard` | Future approved observation that WebView content reaches a safe visible state or blocks safely. |
| `webview_navigation_boundary` | Future approved observation of Back/D-pad/focus behavior around WebView surfaces. |
| `webview_session_cookie_boundary` | Future approved observation that cookies/session state are handled without leaking public evidence. |
| `webview_offline_error_state` | Future approved observation of WebView unavailable/cache/error categories. |
| `payment_cancel` | Future approved staging-only cancel path observation. |
| `payment_failure` | Future approved staging-only failure and retry-copy observation. |
| `payment_pending_resume` | Future approved staging-only pending and resume behavior observation. |
| `payment_duplicate_return` | Future approved idempotent duplicate return observation. |
| `payment_success_return` | Future approved staging-only success return observation without real charge. |
| `redacted_web_payment_evidence` | Future validation that evidence references remain public-safe and redacted. |

The generator must never emit a successful runtime or payment result. Complete confirmed metadata means prerequisites are ready for a future task, not that behavior is verified.

## Report Status Rules

| Input state | Report status |
|---|---:|
| Required approval metadata missing or malformed | `blocked` |
| Required approval evidence not confirmed | `blocked` |
| Approved aliases and category-only plan exist | `not_run` |
| Runtime behavior is not observed | `unknown` |
| Any real payment path is requested | `PROD_FORBIDDEN` stop condition |

WebView/payment rows cannot be marked `confirmed` or successful without approved future runtime evidence and reviewer sign-off.

## Redaction Rules

Before any public report is written, redact:

- URLs and endpoint-like values;
- email addresses and user identifiers;
- secrets, tokens, cookies, sessions, authorization values and API keys;
- local paths;
- payment-like numbers, billing tokens, receipt-like identifiers and wallet-like values;
- opaque long values.

Allowed public output is limited to aliases, blocked/not-run status, category-level planned checks, redacted artifact references, risk summaries, unknowns and reviewer status.

## Forbidden Categories

The following remain forbidden in public docs and TASK-008 tooling:

- real payments or real payment instruments;
- private URL, redirect chain, endpoint, header, payload, cookie, token or session publication;
- endpoint discovery, extraction or inventory;
- raw WebView, browser, payment, network, screenshot, video or log evidence;
- executable Android/device/runtime/network command recipes;
- proxy setup, interception or traffic mutation recipes;
- TLS, certificate, pinning, authentication or security-control bypass;
- production load, fuzzing or unbounded retry behavior;
- APK modification, resigning, patching or source/decompiled analysis;
- production mutation or destructive actions.

## Future Execution Gate

Future WebView/payment execution may start only after a separate approved task records:

- confirmed approved build, target and configuration;
- approved public-safe WebView fixture aliases;
- approved staging-only, non-real-payment fixture aliases;
- approved synthetic user/session boundaries where needed;
- approved resource budget and retry limits;
- redaction and evidence storage approval;
- cleanup or rollback rules for sessions and staging transaction state;
- Security and QA review approval before execution.

If any gate is missing, WebView/payment reports remain `blocked` or `not_run`.
