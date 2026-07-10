# Evidence Schema

Task: `TASK-003 - Reporting, evidence schema and release gate generator`

This schema is public-safe and shared by blocked reports, exported component guard summaries, future redacted runtime summaries and release-gate inputs. It intentionally excludes raw logs, screenshots, videos, private endpoints, credentials, APK artifacts and executable runtime/device recipes.

## Evidence Report Envelope v2

TASK-038 adds the forward-compatible public-safe envelope
`evidence-report-envelope-v2` in
`docs/qa/schemas/evidence-report-envelope-v2.schema.json`.

The v2 envelope separates these status dimensions so a report cannot convert
unknown or blocked evidence into release confidence:

- `schema_validation_status`: schema/envelope validity; v2-valid reports use
  `pass`, while manifest records normalize source reports to `v2_valid`,
  `legacy_migration_blocked`, `unknown_schema` or `invalid`.
- `execution_status`: whether the described check passed, failed, was blocked,
  not run, partial, closed by ledger or unknown.
- `coverage_status`: whether the intended scope was covered, partial, blocked,
  not run or unknown.
- `evidence_status`: `confirmed`, `likely`, `hypothesis` or `unknown`, with the
  existing extended values used by prior public summaries.
- `release_effect`: `candidate_evidence`, `blocks_release`,
  `no_release_claim`, `deferred` or `unknown`.
- `production_safety_classification`: explicit `PROD_*` class for the report.

Required identity/provenance fields are `generated_at_utc`, `task_id`,
`build_ref`, optional public-safe build hash prefix inside `build_ref`,
`target_alias`, `run_id`, `artifacts[]`, `blocked_reasons`, `unknowns`,
`risks`, `verification`, `review` and `provenance`. `artifacts[]` entries use
public repo-relative references plus SHA-256; raw evidence paths, ignored
`.qa_local` material, absolute paths, URLs, endpoints, secrets and private
values are forbidden.

TASK-038 also adds `docs/qa/schemas/report-manifest-v1.schema.json` and the
generated manifest `docs/qa/reports/report-manifest.json`. The manifest indexes
tracked public-safe JSON summaries matching `docs/qa/reports/*.json`, validates file
existence and SHA-256, chooses at most one authoritative v2 record per
task/build/target/run and fails closed on duplicate authority, stale or missing
references, unknown schemas, invalid v2 envelopes or unsafe values. Existing
pre-v2 reports are not ignored and are not authoritative; they are recorded as
`legacy_migration_blocked` until a later task migrates them.

## Status Vocabulary

| Field | Allowed values |
|---|---|
| `overall_status` | `pass`, `fail`, `blocked`, `not_run` |
| `gate_status` | `pass`, `fail`, `blocked`, `not_run` |
| `evidence_status` | `confirmed`, `likely`, `hypothesis`, `unknown` |
| `production_safety_classification` | `PROD_SAFE`, `PROD_CONDITIONAL`, `PROD_FORBIDDEN` |
| `redaction_status` | `not_applicable`, `pending`, `redacted`, `blocked` |
| `risk_level` | `R0`, `R1`, `R2`, `R3`, `unknown` |
| `release_decision` | `pass`, `blocked`, `fail`, `not_run` |

Invalid or missing evidence values must normalize to `unknown`, not to `confirmed`.

## Required Report Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `schema_version` | string | yes | Current shared version is `1.0`. |
| `generated_at_utc` | string | yes | ISO-8601 UTC timestamp. |
| `task_id` | string | yes | Example: `TASK-003`. |
| `mode` | string | yes | Example: `BOUNDED_AUTONOMOUS`. |
| `tool_name` | string | yes | Public-safe generator name. |
| `overall_status` | enum | yes | `blocked` when required release metadata is missing. |
| `evidence_status` | enum | yes | `unknown` when no approved runtime evidence exists. |
| `production_safety_classification` | enum | yes | Local generators are `PROD_SAFE`. |
| `redaction_status` | enum | yes | `redacted` when private-looking notes or artifact refs were sanitized. |
| `prerequisites` | object | yes | Approval state for build, target, config, fixtures, redaction policy, evidence storage and cleanup/rollback. |
| `release_gates` | array | yes | Each gate includes `id`, `name`, `status`, `evidence_status`, `risk_level`, `notes`. |
| `blocked_reasons` | array | yes | Empty only when status is not blocked. |
| `risks` | array | yes | Each risk includes `id`, `level`, `status`, `summary`. |
| `unknowns` | array | yes | Each unknown includes `id`, `status`, `question`. |
| `verification` | array | yes | Local checks and outcomes. |
| `artifacts` | array | yes | References only to approved redacted artifacts. |
| `review` | object | yes | Reviewer roles and result or pending status. |
| `fixtures` | array | conditional | Public-safe fixture approval summaries; required for future fixture-dependent runtime tasks. |

## Prerequisites Object

```json
{
  "approved_build": {
    "present": false,
    "evidence_status": "unknown",
    "note": "No approved build metadata was provided."
  },
  "approved_target": {
    "present": false,
    "evidence_status": "unknown",
    "note": "No approved Android TV device or emulator target was provided."
  },
  "approved_config": {
    "present": false,
    "evidence_status": "unknown",
    "note": "No approved runtime configuration was provided."
  },
  "redaction_policy": {
    "present": false,
    "evidence_status": "unknown",
    "note": "No approved redaction policy was provided."
  },
  "synthetic_fixture_policy": {
    "present": false,
    "evidence_status": "unknown",
    "note": "No approved synthetic fixture policy was provided."
  },
  "evidence_storage": {
    "present": false,
    "evidence_status": "unknown",
    "note": "No approved ignored evidence storage policy was provided."
  },
  "cleanup_rollback": {
    "present": false,
    "evidence_status": "unknown",
    "note": "No approved cleanup and rollback policy was provided."
  }
}
```

## Release Gate Object

```json
{
  "id": "RG-001",
  "name": "Runtime startup reaches first visible state",
  "status": "not_run",
  "evidence_status": "unknown",
  "risk_level": "R0",
  "production_safety_classification": "PROD_CONDITIONAL",
  "source_task": "TASK-001",
  "notes": "Runtime execution is blocked until approved build, target and config exist."
}
```

R0/R1 gates are fail-closed:

- `pass` requires `status: pass` and `evidence_status: confirmed`;
- `blocked`, `fail`, `not_run`, missing gates or non-confirmed evidence keep the release decision `blocked` or `fail`;
- missing runtime evidence is `unknown`, not proof that risk is absent.

## Input Summary Sources

TASK-003 release reports may consume public-safe summaries from:

- TASK-001 runtime smoke blocked reports;
- TASK-002 exported component guard skeleton reports;
- TASK-004 manual runtime screen/focus map summaries;
- TASK-006 fixture approval summaries;
- TASK-007 network/offline safe runner summaries;
- TASK-008 WebView/payment safe runner summaries;
- TASK-009 compatibility/device matrix summaries;
- TASK-010 CI/nightly smoke summaries;
- TASK-011 navigation transition map summaries;
- future approved runtime summaries after redaction and review.

Only structured public-safe summary fields may be used. Do not embed raw command output, raw logs, screenshots, videos, endpoint inventories, component inventories, credentials or private identifiers.

## Manual Screen And Focus Map Summary

TASK-004 map summaries may include only public-safe category-level fields:

```json
{
  "screen_map_sections": [
    {
      "id": "SM-001",
      "name": "first_screen",
      "result": "not_run",
      "evidence_status": "unknown",
      "risk_level": "R0",
      "notes": "Runtime observation is blocked until approved prerequisites exist."
    }
  ],
  "focus_map_checks": [
    {
      "id": "FM-001",
      "name": "initial_focus",
      "result": "not_run",
      "evidence_status": "unknown",
      "risk_level": "R1",
      "notes": "First-focus behavior is unknown before approved runtime evidence."
    }
  ]
}
```

Allowed aliases include `screen-home-001` or `focus-home-primary-001` style public-safe identifiers. Do not include raw visible user data, private package/class names, private routes, raw screenshot paths, logs or executable device commands.

## Fixture Approval Summary

TASK-006 fixture summaries may include only public-safe aliases and approval metadata:

```json
{
  "fixture_id": "fixture-auth-session-001",
  "fixture_class": "synthetic_user",
  "approval_status": "pending",
  "evidence_status": "unknown",
  "production_safety_classification": "PROD_CONDITIONAL",
  "owner_role": "QA/Security/Product",
  "allowed_flows": ["category-level-only"],
  "disallowed_flows": ["real_payment", "real_user_data"],
  "redaction_status": "pending",
  "evidence_storage": "pending",
  "cleanup_rollback": "pending"
}
```

Fixture approval requires `approval_status: approved` and `evidence_status: confirmed`. Fixture approval only allows future conditional execution; it does not confirm runtime behavior.

## Network/Offline Summary

TASK-007 network/offline summaries may include only public-safe prerequisite status and category-level planned checks:

```json
{
  "planned_network_offline_checks": [
    {
      "id": "NO-001",
      "category": "offline_startup",
      "result": "not_run",
      "evidence_status": "unknown",
      "risk_level": "R1",
      "notes": "Network/offline execution is blocked until approved prerequisites exist."
    }
  ]
}
```

Allowed aliases include `offline`, `reconnect`, `high_latency`, `intermittent_connectivity`, `transport_switch` and `captive_portal_like`. Public reports must not include endpoint values, packet captures, proxy configuration, TLS bypass instructions, raw logs, traffic dumps or executable device/network command recipes.

## Compatibility/Device Matrix Summary

TASK-009 compatibility summaries may include only public-safe aliases and category-level planned checks:

```json
{
  "device_profiles": [
    {
      "alias": "device-template-001",
      "target_category": "unknown",
      "os_api_band": "unknown",
      "form_factor": "unknown",
      "display_class": "unknown",
      "input_class": "unknown",
      "network_class": "unknown",
      "locale_class": "unknown",
      "evidence_status": "unknown",
      "notes": "Template only; no device inventory was collected by TASK-009."
    }
  ],
  "planned_compatibility_checks": [
    {
      "id": "CDM-001",
      "category": "os_api_band",
      "result": "not_run",
      "evidence_status": "unknown",
      "risk_level": "R1",
      "artifact_refs": []
    }
  ]
}
```

Allowed fields include device aliases, target category, OS/API buckets, form factor, display/input/network/locale category buckets, planned compatibility check categories, result, evidence status, risk level, redacted artifact aliases and blocked reasons.

Public reports must not include real device serials, private lab identifiers, raw screenshots, raw logs, raw videos, APK paths, endpoint data, credentials, account identifiers or executable Android/device/runtime command recipes. Emulator/preflight rows do not replace confirmed Android TV release evidence.

## WebView/Payment Safe Summary

TASK-008 WebView/payment summaries may include only public-safe prerequisite status, fixture aliases and category-level planned checks:

```json
{
  "flow_aliases": [
    {
      "alias": "webview-payment-template-001",
      "surface_category": "webview_payment",
      "fixture_category": "payment_success_return",
      "allowed_scope": "plan_only",
      "evidence_status": "unknown",
      "notes": "Public-safe alias only."
    }
  ],
  "planned_webview_payment_checks": [
    {
      "id": "WPS-001",
      "category": "webview_render_guard",
      "result": "not_run",
      "evidence_status": "unknown",
      "risk_level": "R1",
      "artifact_refs": []
    }
  ]
}
```

Allowed aliases include `web-legal-001`, `web-auth-boundary-001`, `payment-cancel-001`, `payment-failure-001`, `payment-pending-001`, `payment-duplicate-return-001` and `payment-success-return-001`.

Public reports must not include private URLs, redirect chains, endpoints, headers, payloads, cookies, tokens, sessions, raw WebView logs, payment instruments, billing tokens, receipts, raw screenshots, APK paths, account identifiers or executable Android/device/runtime/network recipes.

## CI/Nightly Smoke Summary

TASK-010 CI/nightly smoke summaries may include only public-safe prerequisite status, CI job aliases and category-level planned checks:

```json
{
  "ci_jobs": [
    {
      "alias": "ci-nightly-template-001",
      "job_category": "python_unit_tests",
      "trigger_category": "manual_or_future_schedule",
      "runner_category": "public_safe_runner",
      "evidence_status": "unknown",
      "notes": "Template only; no live CI schedule was created by TASK-010."
    }
  ],
  "planned_ci_nightly_checks": [
    {
      "id": "CNS-001",
      "category": "repository_hygiene",
      "result": "not_run",
      "evidence_status": "unknown",
      "risk_level": "R1",
      "artifact_refs": []
    }
  ]
}
```

Allowed fields include CI job aliases, category-level triggers, runner categories, planned check categories, result, evidence status, risk level, redacted artifact aliases and blocked reasons.

Public reports must not include CI secrets, private runner credentials, deploy keys, private endpoints, raw logs, raw screenshots, APK paths, account identifiers, payment values or executable Android/device/runtime/network recipes.

## Navigation Transition Summary

TASK-011 navigation transition summaries may include only public-safe aliases and category-level planned checks:

```json
{
  "transition_edges": [
    {
      "alias": "transition-startup-catalog-001",
      "from_screen_category": "startup",
      "to_screen_category": "catalog",
      "action_category": "dpad_select",
      "guard_category": "none_or_unknown",
      "fixture_dependency": "none_or_unknown",
      "evidence_status": "unknown",
      "notes": "Template only; no runtime navigation was executed by TASK-011."
    }
  ],
  "planned_transitions": [
    {
      "id": "NTM-001",
      "category": "startup_to_catalog",
      "result": "not_run",
      "evidence_status": "unknown",
      "risk_level": "R1",
      "artifact_refs": []
    }
  ]
}
```

Allowed fields include transition aliases, screen categories, action categories, guard categories, fixture dependency categories, planned transition check categories, result, evidence status, risk level, redacted artifact aliases and blocked reasons.

Public reports must not include private route values, deeplink values, package or class names, endpoint data, redirect chains, raw screenshots, raw logs, raw videos, APK paths, account identifiers, payment values or executable Android/device/runtime command recipes.

## Approval Metadata Validation Summary

TASK-015 approval validation summaries may include only public-safe approval
metadata and normalized gate outcomes:

```json
{
  "approval_decision": "blocked",
  "runtime_execution_status": "not_run",
  "runtime_evidence_status": "unknown",
  "blocked_reasons": [
    "approval_status must be approved."
  ],
  "normalized_summary": {
    "task_id": "TASK-005",
    "approved_build_alias": "task-005-local-apk-001",
    "approved_device_aliases": ["tv-001"]
  }
}
```

Allowed fields include build aliases, device aliases, synthetic user alias,
fixture status, review status and local ignored path patterns under `.qa_local/`.

Public reports must not include raw APKs, absolute user paths, raw phone/OTP,
tokens, cookies, sessions, private endpoints, raw evidence, device serials,
IMEI, MAC, Android ID, Google account identifiers or executable runtime/device
recipes.

Approval validation is not runtime evidence. It must not produce runtime `pass`.

## TASK-005 Limited Runtime Smoke Summary

TASK-005 runtime summaries may include only public-safe aliases, status values
and category-level observations:

```json
{
  "task_id": "TASK-005",
  "mode": "NON_AUTONOMOUS",
  "production_safety_classification": "PROD_CONDITIONAL",
  "public_device_alias": "tv-tpv-013",
  "public_runtime_profile_alias": "tv-tpv-a12-013",
  "build_alias": "task-005-local-apk-001",
  "runtime_execution_status": "pass",
  "evidence_status": "confirmed",
  "checks": [
    {
      "id": "SF-001",
      "name": "first_visible_state",
      "status": "pass",
      "evidence_status": "confirmed",
      "public_screen_alias": "screen-auth-guard-001"
    }
  ],
  "forbidden_scope_not_run": [
    "payment",
    "stream",
    "webrtc",
    "media_playback",
    "webview"
  ],
  "artifact_refs": [
    {
      "id": "artifact-task005-runtime-summary-001",
      "type": "redacted_summary",
      "storage": ".qa_local/evidence/task-005/"
    }
  ]
}
```

Allowed fields include public-safe target aliases, build aliases, check names,
status, evidence status, redacted artifact IDs, local ignored storage family
and category-level first-state/focus observations.

Public TASK-005 summaries must not include raw APK files, APK hashes, package
or activity names, raw screenshots, raw logs, raw UI text, phone/OTP/account
values, device serials, IPs, MAC/IMEI/Android IDs, private endpoints,
executable command transcripts or absolute local machine paths.

## TASK-019 Auth/Session Smoke Summary

TASK-019 auth/session summaries may include only public-safe aliases, status
values and category-level observations:

```json
{
  "task_id": "TASK-019",
  "mode": "NON_AUTONOMOUS",
  "production_safety_classification": "PROD_CONDITIONAL",
  "public_device_alias": "tv-tpv-013",
  "public_runtime_profile_alias": "tv-tpv-a12-013",
  "build_alias": "task-005-local-apk-001",
  "phase_b_status": "pass",
  "auth_result": "pass",
  "post_auth_screen_alias": "post_auth_home_unknown",
  "home_foreground_session_status": "pass",
  "force_stop_relaunch_session_status": "pass",
  "crash_anr_status": "not_observed",
  "logout_status": "not_run",
  "forbidden_scope_not_run": [
    "webview",
    "redirect",
    "webrtc",
    "stream",
    "media_playback",
    "payment",
    "network_offline"
  ]
}
```

Allowed fields include public-safe target aliases, build aliases, auth/session
status values, screen aliases, focus/session summaries, crash/ANR status,
redacted artifact IDs and ignored evidence storage family.

Public TASK-019 summaries must not include raw phone/OTP values, tokens,
cookies, sessions, package or activity names, raw UI text, raw screenshots, raw
logs, APK hashes, device serials, IPs, MAC/IMEI/Android IDs, private endpoints,
executable command transcripts or absolute local machine paths. A successful
TASK-019 summary confirms only bounded auth/session shell behavior; it does not
confirm broad post-auth navigation, logout, WebView, WebRTC, stream/media
playback, payment, network/offline or compatibility coverage.

## Redaction Rules

Reports may reference only:

- redacted artifact IDs;
- approved local evidence paths excluded from public source control;
- category-level observations;
- reviewer notes that contain no private values.

Reports must not include:

- secrets, tokens, cookies, sessions or credentials;
- raw logs, screenshots, videos or dumps;
- private endpoint inventories;
- raw APK/AAB/DEX/native/signing artifacts;
- real user data;
- executable Android runtime/device command recipes.

## Confirmation Rule

No runtime behavior may use `evidence_status: confirmed` unless approved runtime evidence, explicit team confirmation or an approved sanitized artifact is recorded. Static planning context can be at most `likely`; unexecuted expectations are `hypothesis`; missing information is `unknown`.
