# Exported Component Guard Checklist

Task: `TASK-002 - Exported component guard checks skeleton`

Production safety classification: `PROD_SAFE` for this checklist and local report generation. It defines categories, prerequisites and report expectations only. It does not contain executable device/runtime recipes.

## Evidence Status

Use exactly one status for every observation:

| Status | Meaning |
|---|---|
| `confirmed` | Backed by approved runtime evidence, explicit team confirmation or an approved sanitized artifact. |
| `likely` | Supported by public-safe sanitized planning context but not runtime-confirmed. |
| `hypothesis` | A testable expectation or risk that still needs evidence. |
| `unknown` | Not enough approved evidence is available. |

## Required Prerequisites

Exported component guard execution is `blocked` until all prerequisites below are explicitly approved and recorded in a future task run:

| Prerequisite category | Required approval or evidence | Evidence status before approval |
|---|---|---:|
| Approved build | Build identifier, source, release channel and handling rules are known. | `unknown` |
| Approved target | Android TV device or emulator target is in scope. | `unknown` |
| Approved configuration | Environment, fixture boundaries and no-mutation policy are documented. | `unknown` |
| Approved guard scope | Product/security approves which exported surface categories are intentional and safe to check. | `unknown` |
| Redaction policy | Logs, screenshots, videos and reports have redaction rules before capture. | `unknown` |
| Synthetic fixture policy | Auth/session/payment/stream dependencies use approved synthetic fixtures only. | `unknown` |
| Cleanup and rollback | Any mutable flow has cleanup, rollback or explicit no-mutation proof. | `unknown` |

## Guard Categories

TASK-002 only creates the category-level skeleton. Runtime results stay `unknown`.

| ID | Category | Purpose | Initial result | Evidence status |
|---|---|---|---:|---:|
| ECG-001 | Intentional exposure inventory | Confirm product/security has approved the exported surface inventory at category level. | `not_run` | `unknown` |
| ECG-002 | Benign direct-start guard | Plan a benign check that protected entry points do not bypass expected guards. | `not_run` | `unknown` |
| ECG-003 | Auth/session guard | Plan a check that session-dependent entry points require approved session state. | `not_run` | `unknown` |
| ECG-004 | Input validation guard | Plan synthetic non-private input validation checks without endpoint or secret disclosure. | `not_run` | `unknown` |
| ECG-005 | No-mutation guard | Plan checks as no-op/dry-run only unless cleanup and rollback are approved. | `not_run` | `unknown` |
| ECG-006 | Redacted evidence guard | Require public-safe summaries and redacted artifact references only. | `not_run` | `unknown` |

## Blocked Criteria

Mark the guard run as `blocked` when any of these are true:

- approved build, target, configuration or guard scope is missing;
- exact component names or package/class identifiers would be published in public source;
- the task would need source code, decompiled code, smali, private endpoints, secrets or real user data;
- a flow could mutate production state without cleanup and rollback;
- evidence could expose private values and redaction is not defined;
- runtime execution has not been explicitly approved for the task.

## Public-Safe Output

Allowed public outputs:

- category-level checklist results;
- blocked or not-run guard reports;
- redacted summaries;
- risk and unknown lists;
- links to approved local evidence records without raw private content.

Forbidden public outputs:

- raw manifest/component inventories or exact private component identifiers;
- APK, AAB, DEX, native or signing artifacts;
- raw logs, screenshots, videos or endpoint inventories;
- secrets, tokens, cookies, sessions or credentials;
- executable device/runtime command recipes;
- real payment or real-user data.
