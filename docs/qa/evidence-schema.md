# Evidence Schema

Task: `TASK-003 - Reporting, evidence schema and release gate generator`

This schema is public-safe and shared by blocked reports, exported component guard summaries, future redacted runtime summaries and release-gate inputs. It intentionally excludes raw logs, screenshots, videos, private endpoints, credentials, APK artifacts and executable runtime/device recipes.

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
- TASK-009 compatibility/device matrix summaries;
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
