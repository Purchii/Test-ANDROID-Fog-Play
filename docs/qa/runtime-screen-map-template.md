# Manual Runtime Screen Map Template

Task: `TASK-004 - Manual runtime screen and TV focus map templates`

Production safety classification: `PROD_SAFE` for this template and local report generation. Manual runtime observation is `PROD_CONDITIONAL` and remains blocked until approved build, target, configuration, fixture and redaction prerequisites are recorded in a future task.

This template captures category-level, public-safe screen observations. It must not include raw screenshots, raw logs, private endpoint values, credentials, real user data, package/class identifiers or executable runtime/device command recipes.

## Evidence Status

Use exactly one status for every observation:

| Status | Meaning |
|---|---|
| `confirmed` | Backed by approved runtime evidence, explicit team confirmation or an approved sanitized artifact. |
| `likely` | Supported by public-safe sanitized planning context but not runtime-confirmed. |
| `hypothesis` | A testable expectation or risk that still needs evidence. |
| `unknown` | Not enough approved evidence is available. |

## Required Prerequisites

| Prerequisite category | Required approval or evidence | Evidence status before approval |
|---|---|---:|
| Approved build | Build identifier, source, release channel and handling rules are known. | `unknown` |
| Approved target | Android TV device or emulator target is in scope. | `unknown` |
| Approved configuration | Environment, feature flags and fixture boundaries are documented. | `unknown` |
| Redaction policy | Screenshot, video, log and report redaction rules are approved before capture. | `unknown` |
| Synthetic fixture policy | Auth, stream and payment-like flows use approved synthetic or staging fixtures only. | `unknown` |
| Evidence storage | Raw local evidence path is ignored by source control and approved for temporary storage. | `unknown` |
| Cleanup and rollback | Any mutable flow has cleanup, rollback or explicit no-mutation proof. | `unknown` |

## Screen Alias Rules

Use stable public-safe aliases instead of private identifiers.

| Field | Rule | Example |
|---|---|---|
| Screen alias | Human-readable category plus sequence number. | `screen-home-001` |
| Screen type | Category-level purpose only. | `startup`, `auth_guard`, `catalog`, `stream_guard`, `settings`, `error_state` |
| Artifact reference | Redacted artifact ID or local ignored evidence ID only. | `artifact-screen-home-001` |
| Visible text | Summarize category, not private/user-specific text. | `catalog row label present` |
| Route/source | Do not record private routes, package names or class names. | `launcher_entry` |

## Screen Inventory

| Screen alias | Screen type | Entry source | Stable state criteria | Evidence status | Redacted artifact ref | Notes |
|---|---|---|---|---:|---|---|
| `screen-___-001` | `startup/auth_guard/catalog/stream_guard/settings/error_state/other` | `launcher/back/deeplink/category-only/other` | `unknown` | `unknown` | `none` |  |

## Screen State Fields

| Field | Value |
|---|---|
| Screen alias | `screen-___-001` |
| Observation timestamp UTC | `YYYY-MM-DDTHH:MM:SSZ` |
| Observer role | `QA/Orchestrator/Reviewer` |
| Build evidence status | `unknown` |
| Target evidence status | `unknown` |
| Screen evidence status | `unknown` |
| Redaction status | `pending/blocked/redacted/not_applicable` |
| Crash/ANR signal | `unknown/not_observed/observed` |
| Loading stability | `unknown/stable/unstable/blocked` |
| Private data exposure | `unknown/not_observed/observed_blocker` |

## Transition Map

Record only category-level transitions. Do not record raw command transcripts.

| From screen | Action category | To screen | Expected result | Actual result | Evidence status | Risk level | Notes |
|---|---|---|---|---|---:|---:|---|
| `screen-___-001` | `dpad_select/back/home/timeout/retry/category-only` | `screen-___-002` | `unknown` | `not_run` | `unknown` | `unknown` |  |

## Blocked Criteria

Mark screen mapping as `blocked` when any of these are true:

- approved build, target, configuration or redaction policy is missing;
- runtime execution has not been explicitly approved for the task;
- a screen could expose private/user/payment data and redaction is not approved;
- a flow could mutate production state without cleanup and rollback;
- the observation would require source code, decompiled code, smali, private endpoints, secrets or real user data;
- public output would require raw screenshots, logs, videos, endpoint inventories or executable device/runtime recipes.

## Public-Safe Output

Allowed public outputs:

- screen aliases and category-level states;
- blocked or not-run map summaries;
- redacted artifact references;
- risk and unknown lists;
- reviewer sign-off.

Forbidden public outputs:

- raw screenshots, videos, logs or dumps;
- APK, AAB, DEX, native or signing artifacts;
- private package/class names, routes, endpoints or component inventories;
- secrets, tokens, cookies, sessions or credentials;
- real user, payment or account data;
- executable Android runtime/device command recipes.
