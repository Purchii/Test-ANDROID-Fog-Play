# Approval Metadata Policy

Task: `TASK-015A/016 - Approval validator hardening and ADB device/build inventory preflight`

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
- `approved_by_role` is empty or not one of `project_owner`, `qa_lead` or
  `security_prod_safety_reviewer`.
- Approved targets are not approved or do not include structured public-safe
  device targets with `device_alias` and `runtime_profile_alias`.
- Approved targets omit `allowed_categories`.
- Approved target aliases do not match the TASK-016 grammar or contain obvious
  owner/location labels such as `oleg`, `home`, `livingroom`, `bedroom`,
  `office`, `kitchen`, `personal` or `private`.
- TASK-005 approval metadata has only phone secondary targets and no P0
  Android TV/STB D-pad target.
- Device metadata includes serials, IMEI, MAC, Android ID, Google account or personal identifiers.
- Runtime scope includes anything outside the exact TASK-005 allowlist:
  `install`, `launch`, `first_visible_state`, `synthetic_login_if_required`,
  `initial_focus`, `minimal_dpad_navigation`, `back_home`,
  `background_foreground`, `force_stop_relaunch`,
  `clear_cache_if_preapproved`, `clear_app_data_before_after_clean_state`,
  `crash_anr_logcat_observation`, `redacted_evidence_summary`.
- Runtime scope includes payment, subscription, purchase, billing, checkout,
  card, wallet, bank, transaction, invoice, receipt, stream, WebRTC, media,
  video, playback, player, cloud/game stream, WebView, browser, custom tab,
  URL load, redirect, profile/account mutation, real-user data changes,
  production mutation, security bypass, decompilation, patching or resigning.
- Stream, WebView or payment fixtures are `out_of_scope` while runtime scope includes those flows.
- Fixture statuses use anything outside `approved`, `out_of_scope`, `pending`
  or `blocked`.
- For current TASK-005 scope, stream, WebView and payment fixtures are not
  `out_of_scope`.
- `synthetic_login_if_required` is in scope but `synthetic_qa_user.approved`
  is not true.
- Synthetic QA user metadata includes raw phone or OTP values.
- Evidence capture values are missing, pending, blocked or outside the exact
  allowed enum values.
- Raw evidence storage is not local ignored storage.
- Cleanup levels are missing, outside C1-C4, or include C5 without separate
  approval.
- Any required reviewer is not `approved` or `confirmed`.

## TASK-016 Inventory Preflight

TASK-016 may run only owner-approved inventory commands and only with
`--allow-adb`. The default command must not call ADB and must return a
blocked/not-run report.

This is the only approved device-command exception in this policy: the exact
TASK-016 inventory allowlist below is permitted for local preflight after owner
approval. Runtime/app/device command recipes outside this allowlist remain
forbidden in public docs, reports and automation.

Allowed ADB commands:

```text
adb devices -l
adb -s <serial> shell getprop ro.product.manufacturer
adb -s <serial> shell getprop ro.product.model
adb -s <serial> shell getprop ro.build.version.release
adb -s <serial> shell getprop ro.build.version.sdk
adb -s <serial> shell getprop ro.build.version.security_patch
adb -s <serial> shell wm size
adb -s <serial> shell wm density
adb -s <serial> shell pm list features
```

TASK-016 remains inventory-only and must always report:

```text
runtime_execution_status: not_run
apk_install_status: not_run
app_launch_status: not_run
```

Raw ADB output, serials and alias maps remain local-only under
`.qa_local/devices/`. Generated public-safe inventory must not include ADB
serial, IP address, MAC, IMEI, Android ID, Google account, full build
fingerprint, phone number, OTP, owner name or room/location labels.

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
- Device aliases such as `tv-tcl-001`, `stb-xiaomi-001` or
  `phone-samsung-001`.
- Runtime profile aliases such as `tv-tcl-a11-001`.
- Synthetic user alias `qa-user-phone-001`.
- Local ignored path patterns under `.qa_local/`.
- Redacted summary references and category-level scope labels.

Forbidden:

- APK/AAB/APKS/XAPK binaries in source control.
- Raw phone, OTP, token, cookie, session or credential values.
- Raw screenshots, logs, videos, packet captures or dumps.
- Device serial, IMEI, MAC, Android ID, Google account or private device label.
- Private endpoint, route, deeplink, redirect chain, header or payload details.
- Runtime/device command recipes outside the exact owner-approved TASK-016 ADB
  inventory allowlist and any security bypass instructions.
