# Navigation Transition Map

Task: `TASK-011 - Navigation transition map and coverage model`

Production safety classification: `PROD_SAFE` for this map and local report generation. Any future runtime navigation observation, D-pad execution, Back/Home behavior check, playback transition, WebView boundary check, evidence capture, device/emulator use or APK handling is `PROD_CONDITIONAL` and remains blocked until approved build, target, config, navigation scope, screen alias policy, input event policy, fixture policy, resource budget, redaction, evidence storage, cleanup/rollback, Security review and QA review prerequisites are recorded with `evidence_status=confirmed`.

This document is public-safe. It must not contain private endpoints, raw evidence, credentials, tokens, cookies, sessions, real user data, payment data, APK artifacts, raw device identifiers, packet captures, proxy configuration, TLS bypass details or executable Android runtime/device/network recipes.

## Core Rule

No confirmed navigation scope and approved runtime prerequisites, no transition execution.

TASK-011 tooling creates a local JSON transition map plan only. It does not interact with Android, a device, APK, WebView, WebRTC session, payment surface, backend, network service or production environment.

## Official Design Guidance References

TASK-011 uses the following public Android Developers guidance as design categories only, not as confirmed behavior of MTC Fog Play:

| Source | Public-safe guidance reflected in this model |
|---|---|
| [Navigation on TV](https://developer.android.com/design/ui/tv/guides/foundations/navigation-on-tv) | Navigation should be efficient, predictable and intuitive; TV remotes use limited controls including 4-way D-pad, Select, Back and Home. |
| [TV navigation](https://developer.android.com/training/tv/get-started/navigation) | D-pad navigation should reach visible controls predictably; Back should progress toward the start/root without loops; large hierarchies should use clear horizontal and vertical traversal roles. |

## Evidence Status

Use exactly one evidence status for every prerequisite, transition, risk and report field:

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
| `approved_build` | Approved build/APK category for future runtime observation. |
| `approved_target` | Approved Android TV target class without raw serials or private lab identifiers. |
| `approved_config` | Approved runtime configuration category. |
| `navigation_scope` | Approved screen and transition categories to observe. |
| `screen_alias_policy` | Public-safe alias rules for screen, control and state names. |
| `input_event_policy` | Approved D-pad, Select, Back/Home and media key categories. |
| `fixture_policy` | Synthetic-only account/session/stream fixture boundary where needed. |
| `resource_budget` | Bounded duration, retry, account/session, stream and Back/Home traversal limits. |
| `redaction_policy` | Log, screenshot, report and artifact redaction rules. |
| `evidence_storage` | Raw evidence, if approved later, stays in ignored local or approved restricted storage. |
| `cleanup_rollback` | Cleanup and rollback plan for sessions, playback state and mutable fixtures. |
| `security_review` | Security/Prod-safety Reviewer approves the boundary. |
| `qa_review` | QA Reviewer approves coverage and blocked/not-run expectations. |

Missing, malformed, non-object, `present` not true or non-confirmed prerequisite metadata keeps the report `blocked`.

## Transition Coverage Model

Planned transition categories:

| Category | From alias | To alias | Trigger category | Default result |
|---|---|---|---|---:|
| `startup_to_first_screen` | `app_launch` | `first_screen_alias` | `future_approved_launch_observation` | `not_run` |
| `home_to_catalog` | `home_alias` | `catalog_alias` | `d_pad_select` | `not_run` |
| `catalog_to_detail` | `catalog_alias` | `detail_alias` | `d_pad_select` | `not_run` |
| `detail_to_playback` | `detail_alias` | `playback_alias` | `start_playback_action` | `not_run` |
| `playback_controls` | `playback_alias` | `playback_controls_alias` | `d_pad_or_media_key` | `not_run` |
| `back_navigation` | `current_screen_alias` | `previous_or_safe_exit_alias` | `back` | `not_run` |
| `home_resume` | `foreground_screen_alias` | `resume_or_first_screen_alias` | `home_and_resume` | `not_run` |
| `auth_required_boundary` | `protected_surface_alias` | `auth_or_entitlement_alias` | `access_protected_action` | `not_run` |
| `search_navigation` | `search_entry_alias` | `search_results_alias` | `search_submit` | `not_run` |
| `webview_or_hybrid_boundary` | `native_screen_alias` | `hybrid_surface_alias` | `open_hybrid_action` | `not_run` |
| `error_empty_state` | `requested_surface_alias` | `error_or_empty_state_alias` | `future_approved_negative_condition` | `not_run` |
| `redacted_transition_evidence` | `evidence_source_alias` | `report_alias` | `redacted_artifact_reference` | `not_run` |

All planned transitions have `evidence_status=unknown` until future approved runtime evidence exists.

## Design Guideline Coverage Categories

The report model tags planned transitions with public guideline categories so future reviewers can judge coverage without claiming runtime behavior:

| Category | Meaning |
|---|---|
| `efficient_intuitive_entry` | Entry paths should minimize unnecessary screens and feel easy to learn. |
| `four_way_dpad_select` | Coverage should account for up/down/left/right movement and Select activation. |
| `select_semantics` | Select-triggered transitions should be explicit and expected. |
| `home_semantics` | Home behavior is treated as a system-level exit/resume boundary. |
| `predictable_back_no_infinite_loop` | Back should move toward the previous destination or root and avoid loops. |
| `clear_focus_path` | Every planned focusable target should have an understandable directional path. |
| `axis_based_traversal` | Large hierarchies should separate horizontal and vertical traversal roles where practical. |
| `predictable_navigation_boundary` | Auth, entitlement and hybrid boundaries should not surprise users. |
| `intuitive_recovery` | Error and empty states should offer understandable recovery paths. |
| `public_safe_evidence` | Evidence references must stay sanitized and category-level. |

## Forbidden Content

The following remain forbidden in public docs and TASK-011 tooling:

- live Android device or emulator commands;
- APK, AAB, DEX, native, signing or decompiled artifacts;
- private endpoints, URLs, routes, redirect chains, headers, payloads, cookies, sessions or authorization values;
- raw screenshots, videos, logs, packet captures, dumps or endpoint inventories;
- raw device serials, IMEI/IMSI, Android IDs, MAC addresses or owner labels;
- WebView redirect data, WebRTC internals or payment data;
- proxy setup, interception or traffic mutation recipes;
- TLS, certificate, pinning, authentication or security-control bypass;
- production load, fuzzing or unbounded retry behavior;
- real user data, real payment data, real payment instruments or production mutation.

## Future Execution Gate

Future navigation transition execution may start only after a separate approved task records:

- confirmed approved build, target and runtime configuration;
- confirmed public-safe navigation scope, screen aliases and input event policy;
- confirmed synthetic fixture, resource budget, redaction, evidence storage and cleanup/rollback approvals;
- Security and QA review approval before runtime observation;
- confirmed storage boundaries for any raw evidence, which must remain outside public source control.

If any gate is missing, navigation transition reports remain `blocked` or `not_run`.
