# TV Focus Map Template

Task: `TASK-004 - Manual runtime screen and TV focus map templates`

Production safety classification: `PROD_SAFE` for this template and local report generation. Runtime focus observation is `PROD_CONDITIONAL` and remains blocked until approved runtime prerequisites are recorded in a future task.

This template captures Android TV D-pad focus behavior using public-safe aliases. It must not include raw screenshots, raw logs, private endpoint values, credentials, real user data, package/class identifiers or executable runtime/device command recipes.

## Focus Alias Rules

| Field | Rule | Example |
|---|---|---|
| Focus target alias | Public-safe alias scoped to a screen. | `focus-home-primary-001` |
| Target type | Category-level UI role. | `button`, `card`, `tab`, `row_item`, `menu_item`, `webview_boundary`, `unknown` |
| Label handling | Summarize category only. | `primary action`, `catalog item`, `settings tab` |
| Position | Use relative area, not pixel coordinates unless redacted and approved. | `top_left`, `center`, `bottom_row` |
| Evidence | Redacted artifact ID only. | `artifact-focus-home-001` |

## Initial Focus

| Screen alias | Initial focus alias | Visible focus indicator | Usable with TV remote | Evidence status | Risk level | Notes |
|---|---|---:|---:|---:|---:|---|
| `screen-___-001` | `focus-___-001` | `unknown` | `unknown` | `unknown` | `R1` |  |

## D-Pad Movement Matrix

Use `not_run` before approved runtime observation exists.

| Screen alias | From focus alias | Direction | Expected target alias | Actual target alias | Result | Evidence status | Notes |
|---|---|---|---|---|---:|---:|---|
| `screen-___-001` | `focus-___-001` | `up/down/left/right` | `focus-___-002` | `not_run` | `not_run` | `unknown` |  |

## Focus Trap Checks

| Screen alias | Trap scenario | Trigger category | Escape path | Result | Evidence status | Risk level | Notes |
|---|---|---|---|---:|---:|---:|---|
| `screen-___-001` | `initial_focus_trap/list_boundary/modal/webview_boundary/other` | `dpad/back/home/category-only` | `unknown` | `not_run` | `unknown` | `R1` |  |

## Back/Home Behavior

| Screen alias | Action category | Expected behavior | Actual behavior | Crash/ANR signal | Evidence status | Notes |
|---|---|---|---|---:|---:|---|
| `screen-___-001` | `back/home/reopen/category-only` | `unknown` | `not_run` | `unknown` | `unknown` |  |

## Accessibility And Localization Focus Notes

| Screen alias | Scenario | Check | Result | Evidence status | Notes |
|---|---|---|---:|---:|---|
| `screen-___-001` | `long_text/localization/accessibility_scaling/rtl_or_locale/other` | `focus remains visible and navigation order is understandable` | `not_run` | `unknown` |  |

## Severity Guidance

| Signal | Suggested risk level | Evidence status rule |
|---|---:|---|
| No visible focus target after startup. | R1 | `confirmed` only with approved runtime evidence. |
| Focus trap blocks primary startup navigation. | R1 | `confirmed` only with approved runtime evidence. |
| Back/Home causes crash, ANR or unrecoverable state. | R0/R1 | `confirmed` only with approved runtime evidence. |
| Focus enters a payment-like or account-mutating flow without approved fixture boundary. | R0/R1 | `confirmed` only with approved runtime evidence and product/security review. |
| Raw evidence exposes private data. | R0/R1 | `confirmed` when private data is observed in a public/reportable path. |

## Blocked Criteria

Mark focus mapping as `blocked` when any of these are true:

- approved build, target, configuration or redaction policy is missing;
- runtime focus observation has not been explicitly approved for the task;
- a flow could mutate production state without cleanup and rollback;
- private/user/payment data may be captured without redaction approval;
- the task would require source code, decompiled code, smali, private endpoints, secrets or real user data;
- public output would require raw screenshots, videos, logs, endpoint inventories or executable device/runtime recipes.

## Release Gate Signals

| Signal | Source gate | Default result before approved runtime evidence |
|---|---|---:|
| First focus visible and usable | `first_focus` | `not_run` / `unknown` |
| D-pad navigation has no startup-blocking trap | `first_focus` | `not_run` / `unknown` |
| Back/Home behavior avoids crash/ANR | `runtime_startup` | `not_run` / `unknown` |
| Redacted evidence is available | `redacted_evidence` | `blocked` / `unknown` |
