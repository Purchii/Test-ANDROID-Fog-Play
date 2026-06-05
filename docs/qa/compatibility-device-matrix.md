# Compatibility Device Matrix

Task: `TASK-009 - Compatibility/device matrix and report format`

Production safety classification: `PROD_SAFE` for this matrix policy and local report generation. Any future Android TV compatibility execution is `PROD_CONDITIONAL` and remains blocked until approved build, target, configuration, inventory policy, matrix scope, criteria, redaction, evidence storage, fixture, Security review and QA review prerequisites are recorded with `evidence_status=confirmed`.

This document is public-safe. It must not contain private endpoints, raw evidence, credentials, tokens, cookies, sessions, real user data, payment data, APK artifacts, raw device identifiers, packet captures, proxy configuration, TLS bypass details or executable Android runtime/device/network recipes.

## Core Rule

No approved compatibility prerequisites, no compatibility execution.

TASK-009 tooling creates a local JSON plan only. It does not interact with Android, a device, APK, WebView, WebRTC session, payment surface, backend, proxy, packet capture, network service or production environment.

## Evidence Status

Use exactly one evidence status for every prerequisite, planned check, risk and report field:

| Status | Meaning |
|---|---|
| `confirmed` | Backed by explicit approved metadata, team approval or approved sanitized artifact. |
| `likely` | Supported by planning context but not approved for execution. |
| `hypothesis` | A testable expectation that still needs approval or evidence. |
| `unknown` | No sufficient approved information is available. |

Only `evidence_status=confirmed` with `present=true` satisfies a prerequisite.

## Required Prerequisites

| Prerequisite | Required public-safe approval |
|---|---|
| `approved_build` | Approved build identifier and handling rules exist outside this report. |
| `approved_target` | Approved Android TV target category is in scope. |
| `approved_config` | Approved configuration and environment class are known without endpoint values. |
| `device_inventory_policy` | Device profile aliases and private identifier handling are approved. |
| `matrix_scope` | OS, form factor, input, display, locale, network and feature axes are bounded. |
| `compatibility_criteria` | Entry, exit, severity and blocked/not-run rules are approved. |
| `redaction_policy` | Evidence and device metadata redaction rules are approved before capture. |
| `evidence_storage` | Raw evidence, if approved later, stays in ignored local storage. |
| `fixture_policy` | Synthetic or staging-only fixture boundaries are approved where needed. |
| `security_review` | Security/Prod-safety Reviewer approves the boundary. |
| `qa_review` | QA Reviewer approves coverage and blocked/not-run expectations. |

Missing, malformed, non-object, `present` not true or non-confirmed prerequisite metadata keeps the report `blocked`.

## Public-Safe Device Profile Rules

Use aliases and categories. Never publish unique device identifiers.

| Field | Rule | Example |
|---|---|---|
| Device alias | Stable public-safe alias, not model serial or owner label. | `device-tv-low-001` |
| Target category | Category-level platform class. | `android_tv`, `stb`, `tv_emulator` |
| OS/API band | Coarse supported band only. | `api_28_30`, `api_31_33`, `api_34_plus` |
| Form factor | Category only. | `tv_panel`, `set_top_box`, `emulator` |
| Display class | Category-level output. | `hd`, `full_hd`, `uhd`, `unknown` |
| Input class | Remote/focus category. | `dpad_remote`, `keyboard_optional`, `unknown` |
| Network class | Approved profile category only. | `standard`, `offline_plan`, `constrained_plan` |
| Locale class | Category-level locale coverage. | `primary_locale`, `secondary_locale`, `unknown` |
| Evidence | Redacted artifact ID only. | `artifact-device-alias-001` |

Forbidden public profile fields include serial number, IMEI/IMSI, Android ID, MAC address, account owner, private lab location, raw model dump, raw logs, raw screenshots and endpoint values.

## Matrix Axes

TASK-009 report output may include these axes only as `not_run` with `evidence_status=unknown`:

| Axis | Purpose |
|---|---|
| `os_api_band` | Future category-level coverage across supported Android TV OS/API bands. |
| `form_factor` | Future coverage across TV panel, set-top box and emulator categories. |
| `performance_class` | Future coverage of startup, navigation and stream guard behavior across device classes. |
| `display_output` | Future coverage of HD/FHD/UHD and overscan-safe layouts. |
| `input_focus` | Future D-pad, Back/Home and focus behavior compatibility coverage. |
| `network_class` | Future category-level compatibility against approved network profiles. |
| `locale_accessibility` | Future localization, text length and accessibility scaling coverage. |
| `webview_webrtc_surface` | Future coverage of hybrid/WebView/WebRTC capability categories without execution in TASK-009. |
| `install_update_path` | Future install, upgrade and data-retention category coverage. |
| `redacted_evidence` | Future validation that evidence references remain public-safe and redacted. |

The generator must never emit a successful runtime result. Complete confirmed metadata means prerequisites are ready for a future task, not that compatibility is verified.

## Report Status Rules

| Input state | Matrix status |
|---|---:|
| Required approval metadata missing or malformed | `blocked` |
| Required approval evidence not confirmed | `blocked` |
| Device profile contains only alias/category data | `not_run` plan entry |
| Approved future execution records redacted evidence | Future task only |
| Runtime behavior is not observed | `unknown` |

Compatibility rows cannot be marked `confirmed` or successful without approved future runtime evidence and reviewer sign-off.

## Redaction Rules

Before any public report is written, redact:

- URLs and endpoint-like values;
- email addresses and user identifiers;
- secrets, tokens, cookies, sessions, authorization values and API keys;
- local paths;
- serial numbers, IMEI/IMSI, Android IDs, device IDs and MAC addresses;
- opaque long values.

Allowed public output is limited to aliases, blocked/not-run status, category-level matrix axes, redacted artifact references, risk summaries, unknowns and reviewer status.

## Forbidden Categories

The following remain forbidden in public docs and TASK-009 tooling:

- raw device inventory extraction or publication;
- device serials, IMEI/IMSI, Android IDs, MAC addresses or owner labels;
- endpoint discovery, extraction or publication;
- packet capture instructions or packet dumps;
- proxy setup, interception or traffic mutation recipes;
- TLS, certificate, pinning, authentication or security-control bypass;
- production load, fuzzing or unbounded retry behavior;
- private headers, payloads, cookies, sessions or authorization values;
- raw logs, screenshots, videos, dumps or endpoint inventories;
- APK modification, resigning, patching or source/decompiled analysis.

## Future Execution Gate

Future compatibility execution may start only after a separate approved task records:

- confirmed approved build, target, configuration and fixture boundaries;
- approved public-safe device profile aliases;
- approved matrix scope and criteria;
- redaction and evidence storage approval;
- cleanup or rollback rules for mutable flows;
- Security and QA review approval before execution.

If any gate is missing, compatibility reports remain `blocked` or `not_run`.
