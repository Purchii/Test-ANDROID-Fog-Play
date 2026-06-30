# Approval Metadata Policy

Task: `TASK-015F/017A - Final strict-schema polish + owner target review handoff`

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
- APK path pattern is not under `.qa_local/apks/task-005/` or does not end
  with `.apk`.
- TASK-005 APK metadata omits `sha256_required: true`, allows the public SHA-256
  value, uses a build alias containing reserved identifier/security tokens or
  identifier-like values, permits actions outside `install`, `launch` and
  `observe`, or omits critical forbidden actions such as `decompile` or
  `extract_secrets`.
- APK action lists contain duplicate values.
- Approved runtime metadata contains fields outside the documented strict
  top-level and section-level allowlists.
- Build aliases contain compound reserved token forms such as `api-key`,
  `apikey`, `api_key`, `extract-secrets`, `extract_secrets`,
  `extractsecrets`, `private-endpoints`, `private_endpoints` or
  `privateendpoints`.
- `approved_by_role` is empty or not one of `project_owner`, `qa_lead` or
  `security_prod_safety_reviewer`.
- Approved targets are not approved or do not include structured public-safe
  device targets with `device_alias` and `runtime_profile_alias`.
- Approved targets omit `allowed_categories`.
- Approved targets omit `device_aliases_required: true`.
- Approved target aliases do not match the TASK-016 grammar, contain reserved
  identifier/security/account tokens, contain IP/fingerprint-like values, or
  contain owner/location labels such as `oleg`, `home`, `livingroom`,
  `bedroom`, `office`, `kitchen`, `personal` or `private`.
- Stable `device_alias` values contain Android-version tokens such as `a9`,
  `a10`, `a11`, `a12`, `a13`, `a14`, `a15` or `a16`. Android major belongs
  only in `runtime_profile_alias`.
- `approved_targets.device_aliases` and structured
  `approved_targets.devices[*].device_alias` disagree.
- TASK-005 approval metadata has no actionable P0 Android TV/STB D-pad target
  with `adb_available: yes`, `classification_confidence: manual_confirmed`,
  `manual_review_required: false` and `forbidden_identifiers_excluded: true`.
- Runtime target aliases are inconsistent: `runtime_profile_alias` must preserve
  the `device_alias` prefix and index and its `a<android_major>` segment must
  match `android_major`.
- Android major and API level do not match the project-local sanity map:
  Android 9 -> API 28, 10 -> 29, 11 -> 30, 12 -> 31 or 32, 13 -> 33,
  14 -> 34, 15 -> 35, 16 -> 36. This is a sanity guard, not a universal Android
  authority; unknown future majors block until the map is updated.
- Manual-confirmed TV/STB approval targets use an alias first segment that does
  not match the structured `form_factor`.
- Structured target categories are inconsistent with
  `approved_targets.allowed_categories`.
- Device metadata includes serials, IMEI, MAC, Android ID, Google account or personal identifiers.
- Structured `approved_targets.devices[*]` includes fields outside the
  documented public-safe allowlist.
- Approval metadata contains IP-like values in any JSON field.
- Runtime scope includes anything outside the exact TASK-005 allowlist:
  `install`, `launch`, `first_visible_state`, `synthetic_login_if_required`,
  `initial_focus`, `minimal_dpad_navigation`, `back_home`,
  `background_foreground`, `force_stop_relaunch`,
  `clear_cache_if_preapproved`, `clear_app_data_before_after_clean_state`,
  `crash_anr_logcat_observation`, `redacted_evidence_summary`.
- Runtime scope is empty or misses the TASK-005 core subset: `install`,
  `launch`, `first_visible_state`, `initial_focus`,
  `minimal_dpad_navigation`, `back_home`, `background_foreground`,
  `force_stop_relaunch`, `crash_anr_logcat_observation` and
  `redacted_evidence_summary`.
- Runtime scope includes payment, subscription, purchase, billing, checkout,
  card, wallet, bank, transaction, invoice, receipt, stream, WebRTC, media,
  video, playback, player, cloud/game stream, WebView, browser, custom tab,
  URL load, redirect, profile/account mutation, real-user data changes,
  production mutation, security bypass, decompilation, patching or resigning.
- `runtime_execution.forbidden_scope` is missing, empty, duplicated, contains
  unsupported values or omits required forbidden areas: payment, subscription,
  purchase, stream, WebRTC, media playback, WebView, redirect flow, production
  mutation, security bypass, decompilation, patching and resigning.
- Stream, WebView or payment fixtures are `out_of_scope` while runtime scope includes those flows.
- Fixture statuses use anything outside `approved`, `out_of_scope`, `pending`
  or `blocked`.
- For current TASK-005 scope, stream, WebView and payment fixtures are not
  `out_of_scope`.
- `synthetic_login_if_required` is in scope but `synthetic_qa_user.approved`
  is not true.
- `synthetic_qa_user.approved` is true but the public alias is not
  `qa-user-phone-001`, `local_secret_file_pattern` is missing or outside
  `.qa_local/secrets/`, does not end with `.env`, or `repo_allowed_file` is
  missing, under `.qa_local/` or not a repository placeholder/template path such as
  `docs/approvals/qa_user.env.example`.
- Synthetic auth scope contains anything except `login`, `logout` or
  `session_persistence`, or TASK-005 synthetic login omits `login` or
  `session_persistence`.
- Synthetic forbidden account actions are missing `payment`, `purchase`,
  `profile_mutation` or `destructive_account_action`, or contain unsupported
  typo values.
- `runtime_execution.auth_mode` is missing, outside
  `synthetic_login_if_required`, `auth_out_of_scope` or `no_auth_required`, or
  inconsistent with the presence/absence of `synthetic_login_if_required` in
  `runtime_execution.allowed_scope`.
- `synthetic_qa_user.approved` is false without explicit
  `auth_out_of_scope` or `no_auth_required` auth mode.
- Synthetic QA user metadata includes raw phone or OTP values.
- `raw_phone_allowed_in_public_docs` or `raw_otp_allowed_in_public_docs` is
  true, even in no-auth metadata variants.
- Evidence capture values are missing, pending, blocked or outside the exact
  allowed enum values.
- `crash_anr_logcat_observation` is in runtime scope while
  `evidence_capture.logs_logcat` is not `yes_local_only_redacted_summary`.
- Visual runtime scope such as `first_visible_state`, `initial_focus` or
  `minimal_dpad_navigation` is present while both screenshots and videos are
  disabled for local redacted summaries.
- Public report policy is anything other than `redacted_summaries_only`.
- Raw evidence storage is not local ignored storage.
- Raw evidence storage path is not under `.qa_local/evidence/task-005/`.
- Evidence capture is approved for local redacted summaries but
  `retention_days` is missing, not an integer or outside `1..30`.
- Cleanup levels are missing, outside C1-C4, or include C5 in allowed runtime
  cleanup.
- `cleanup_rollback.requires_separate_approval` is missing, empty, omits
  `C5_uninstall_reinstall` or contains unsupported values.
- `cleanup_rollback.authorized_zone_scopes` contains anything outside
  `force_stop_relaunch_with_auth_state_preserved` and
  `background_foreground_without_force_stop`.
- `cleanup_rollback.clean_state_scope` is not
  `clear_app_data_before_scenario_and_record_precondition`.
- Runtime scope, cleanup levels, build actions or allowed target categories
  contain duplicate values.
- Synthetic auth scope, synthetic forbidden account actions, cleanup separate
  approvals or cleanup authorized zone scopes contain duplicate values.
- Any required reviewer is not `approved` or `confirmed`.

## TASK-015D/016C Two-Phase Gate

TASK-015D/016C has two phases:

- Phase A: approval hardening and documentation/tests.
- Phase B: owner-approved inventory-only ADB preflight.

Phase B is blocked until Phase A passes. Even after Phase A passes, Phase B
does not approve TASK-005 runtime execution.

## TASK-016 Inventory Preflight

TASK-016C may run only owner-approved inventory commands, only with
`--allow-adb`, and only after the TASK-015D Phase A hard gate passes. The
default command must not call ADB and must return a blocked/not-run report.

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

Generated TASK-016 inventory is heuristic by default:

```text
classification_confidence: heuristic
manual_review_required: true
```

Owner/QA review must copy selected targets into approval metadata as
`manual_confirmed` with `manual_review_required: false` before TASK-005 can be
approved for limited runtime.

## TASK-015E/017 And TASK-015F/017A Owner-Review Export

TASK-015E/017 and TASK-015F/017A may create or validate
`docs/approvals/device_inventory.public_safe.review.json` only from an existing
sanitized generated inventory with:

- `public_safety_findings: []`;
- no raw local paths or raw identifiers;
- `runtime_execution_status: not_run`;
- `apk_install_status: not_run`;
- `app_launch_status: not_run`;
- every device still `classification_confidence: heuristic`;
- every device still `manual_review_required: true`.

The review export must explicitly state that it is not approved for TASK-005
until owner/QA manual review. It must not automatically create
`manual_confirmed` targets.

TASK-015F/017A adds final export validation. The export must fail closed if:

- alias grammar or semantic reserved-token checks fail;
- stable aliases contain Android-version tokens;
- runtime aliases do not preserve stable alias prefix/index and Android major;
- alias prefix does not match form factor;
- Android major/API level sanity fails;
- duplicate device or runtime aliases are present;
- optional `public_device_count` does not match actual device count;
- a device contains public fields outside the allowlist;
- any device is not heuristic/manual-review-required/not-run.

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

See also:

- `docs/approvals/device_alias_policy.md`
- `docs/approvals/adb_inventory_policy.md`
