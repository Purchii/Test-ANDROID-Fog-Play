# Runtime Discovery Checklist

Task: `TASK-001 - Runtime discovery and smoke bootstrap`

Production safety classification: `PROD_SAFE` for this checklist. It defines categories, prerequisites and evidence expectations only. It does not contain executable device/runtime recipes.

## Evidence Status

Use exactly one status for every observation:

| Status | Meaning |
|---|---|
| `confirmed` | Backed by approved runtime evidence, explicit team confirmation or an approved sanitized artifact. |
| `likely` | Supported by public-safe sanitized planning context but not runtime-confirmed. |
| `hypothesis` | A testable expectation or risk that still needs evidence. |
| `unknown` | Not enough approved evidence is available. |

## Required Prerequisites

Runtime discovery is `blocked` until all prerequisites below are explicitly approved and recorded in a task run:

| Prerequisite category | Required approval or evidence | Evidence status before approval |
|---|---|---|
| Approved build | Build identifier, source, release channel and handling rules are known. | `unknown` |
| Approved device or emulator target | Device class, OS level and display/input profile are in scope. | `unknown` |
| Approved configuration | Environment, feature flags and account/fixture boundaries are documented. | `unknown` |
| Redaction policy | Screenshots, logs, videos and reports have redaction rules before capture. | `unknown` |
| Data policy | Synthetic users and non-real-payment fixtures are defined if needed. | `unknown` |
| Cleanup and rollback | Any mutable flow has cleanup, rollback or explicit no-mutation proof. | `unknown` |
| Audit trail | Operator, task branch, timestamp and report output path are recorded. | `unknown` |

## Discovery Categories

Record each category at category level first. Promote details only after approved runtime evidence exists and is redacted.

| Category | Purpose | Initial evidence status | Completion evidence |
|---|---|---:|---|
| Launch entry | Confirm the app can start from an approved launcher path. | `unknown` | Redacted report with launch result, timing bucket and crash/ANR status. |
| First screen | Identify the first stable visible state after startup. | `unknown` | Redacted screenshot reference or structured observation. |
| Initial focus | Confirm a visible and usable TV focus target exists. | `unknown` | Focus target description with no private text or identifiers. |
| D-pad movement | Confirm directional navigation does not trap focus on first screen. | `unknown` | Structured movement notes and blocked zones if any. |
| Back/Home behavior | Classify safe exit, background and return behavior. | `unknown` | Observation summary; no device command transcript. |
| Auth/session guard | Confirm protected paths require valid approved state. | `unknown` | Guard outcome summary with synthetic-only account boundary. |
| Stream entry guard | Confirm stream entry is blocked or allowed according to approved fixture state. | `unknown` | Outcome and fixture classification; no private media identifiers. |
| WebView/payment-safe boundary | Confirm payment-like flows remain staging-only before execution. | `unknown` | Explicit fixture approval or `blocked`. |
| Error and offline states | Confirm graceful blocking or retry UI for unavailable dependencies. | `unknown` | Redacted state summary and recovery outcome. |
| Logging/privacy | Confirm collected evidence is redacted before storage. | `unknown` | Redaction checklist result and reviewer approval. |

## Blocked Criteria

Mark the discovery run as `blocked` when any of these are true:

- approved build, device target or configuration is missing;
- the task would need source code, decompiled code, private endpoints, secrets or real user data;
- a flow could mutate production state without documented cleanup and rollback;
- evidence could expose private values and redaction is not defined;
- runtime execution has not been explicitly approved for the task.

## Public-Safe Output

Allowed public outputs:

- category-level checklist results;
- blocked reports;
- redacted summaries;
- risk and unknown lists;
- links to approved local evidence records without raw private content.

Forbidden public outputs:

- APK, AAB, DEX, native or signing artifacts;
- raw logs, screenshots, videos or endpoint inventories;
- secrets, tokens, cookies, sessions or credentials;
- executable device/runtime command recipes;
- real payment or real-user data.
