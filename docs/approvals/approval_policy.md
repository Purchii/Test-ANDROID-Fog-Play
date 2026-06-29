# Approval Metadata Policy

Task: `TASK-015 - Approval Metadata Schema Validator`

Production safety classification: `PROD_SAFE` for schema, docs, local unit tests
and fail-closed validation only. This policy does not approve Android runtime,
APK handling, device execution, WebView, WebRTC, payment, network or live CI
actions.

## Purpose

Approval metadata is a public-safe bridge between planning tasks and a future
limited TASK-005 runtime smoke. It records only category-level approvals,
aliases, expiration, scope, storage policy, cleanup boundaries and reviewer
status.

The validator can return only:

```text
approval_decision: blocked | approved_for_limited_runtime
runtime_execution_status: not_run
```

It must never return runtime `pass` or claim app behavior.

## Required Top-Level Fields

```text
schema_version
task_id
scope_version
approval_status
approval_evidence_status
expires_at
approved_by_role
approved_build_apk
approved_targets
runtime_execution
synthetic_qa_user
fixtures
evidence_capture
cleanup_rollback
required_reviews
```

## Required Enums

```text
approval_status: approved/pending/blocked/revoked
approval_evidence_status: confirmed/likely/hypothesis/unknown
execution_status: pass/fail/blocked/not_run
runtime_evidence_status: confirmed/likely/hypothesis/unknown
fixture status: approved/out_of_scope/pending/blocked
review status: approved/confirmed/pending/blocked/rejected
```

## Hard Blockers

- Approval status is not `approved`.
- Approval evidence status is not `confirmed`.
- Expiration is missing, invalid or expired.
- TASK-005 has no approved build alias and local ignored APK storage policy.
- APK path pattern is outside `.qa_local/` or uses a user-specific absolute path.
- Approved targets are not approved or do not include public-safe aliases.
- Device metadata includes serials, IMEI, MAC, Android ID, Google account or personal identifiers.
- Runtime scope includes payment, subscription, purchase, stream, WebRTC, media playback, WebView, redirect, production mutation, security bypass, decompilation, patching or resigning.
- Stream, WebView or payment fixtures are `out_of_scope` while runtime scope includes those flows.
- Synthetic QA user metadata includes raw phone or OTP values.
- Evidence capture policy remains pending.
- Raw evidence storage is not local ignored storage.
- Cleanup levels are missing or include C5 without separate approval.
- Any required reviewer is not `approved` or `confirmed`.

## Reviewer Gate

The required reviewers are:

```text
qa_reviewer_a
qa_reviewer_b
security_prod_safety_reviewer
docs_scribe
```

Each must be `approved` or `confirmed` before metadata can be
`approved_for_limited_runtime`.

## Public-Safe Values

Allowed:

- Build alias such as `task-005-local-apk-001`.
- Device aliases such as `tv-001`, `stb-001`, `phone-001`.
- Synthetic user alias `qa-user-phone-001`.
- Local ignored path patterns under `.qa_local/`.
- Redacted summary references and category-level scope labels.

Forbidden:

- APK/AAB/APKS/XAPK binaries in source control.
- Raw phone, OTP, token, cookie, session or credential values.
- Raw screenshots, logs, videos, packet captures or dumps.
- Device serial, IMEI, MAC, Android ID, Google account or private device label.
- Private endpoint, route, deeplink, redirect chain, header or payload details.
- Runtime/device command recipes and security bypass instructions.

