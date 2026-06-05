# Evidence Schema

Task: `TASK-001 - Runtime discovery and smoke bootstrap`

This schema is public-safe and suitable for blocked reports, future redacted runtime summaries and release-gate inputs. It intentionally excludes raw logs, screenshots, private endpoints, credentials and executable runtime recipes.

## Status Vocabulary

| Field | Allowed values |
|---|---|
| `overall_status` | `pass`, `fail`, `blocked`, `not_run` |
| `evidence_status` | `confirmed`, `likely`, `hypothesis`, `unknown` |
| `production_safety_classification` | `PROD_SAFE`, `PROD_CONDITIONAL`, `PROD_FORBIDDEN` |
| `redaction_status` | `not_applicable`, `pending`, `redacted`, `blocked` |
| `risk_level` | `R0`, `R1`, `R2`, `R3`, `unknown` |

## Required Report Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `schema_version` | string | yes | Start with `1.0`. |
| `generated_at_utc` | string | yes | ISO-8601 UTC timestamp. |
| `task_id` | string | yes | Example: `TASK-001`. |
| `mode` | string | yes | Example: `BOUNDED_AUTONOMOUS`. |
| `tool_name` | string | yes | Public-safe generator name. |
| `overall_status` | enum | yes | `blocked` when prerequisites are missing. |
| `evidence_status` | enum | yes | `unknown` when no runtime evidence exists. |
| `production_safety_classification` | enum | yes | Local generator dry-run is `PROD_SAFE`. |
| `redaction_status` | enum | yes | `not_applicable` for reports with no raw evidence. |
| `prerequisites` | object | yes | Approval state for build, target and config. |
| `blocked_reasons` | array | yes | Empty only when status is not `blocked`. |
| `risks` | array | yes | Each risk includes `id`, `level`, `status`, `summary`. |
| `unknowns` | array | yes | Each unknown includes `id`, `status`, `question`. |
| `verification` | array | yes | Local commands/checks and outcomes. |
| `artifacts` | array | yes | References only to approved redacted artifacts. |
| `review` | object | yes | Reviewer names/roles or pending status. |

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
    "note": "No approved device or emulator target was provided."
  },
  "approved_config": {
    "present": false,
    "evidence_status": "unknown",
    "note": "No approved runtime configuration was provided."
  }
}
```

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
- real user data;
- APK, AAB, DEX, native or signing artifacts.

## Confirmation Rule

No runtime behavior may use `evidence_status: confirmed` unless approved runtime evidence, explicit team confirmation or an approved sanitized artifact is recorded. Missing evidence is `unknown`, not proof that risk is absent.
