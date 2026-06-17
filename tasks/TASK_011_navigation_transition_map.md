# TASK-011 - Navigation transition map and coverage model

## Task

Create a public-safe navigation transition map and local fail-closed report foundation for future approved Android TV navigation coverage.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-011 - Navigation transition map and coverage model
```

## Branch

```text
qa/task-011-navigation-transition-map
```

## Context

TASK-004 created manual runtime screen/focus map templates. TASK-006 through TASK-010 added fixture, network/offline, WebView/payment, compatibility and CI/nightly safety boundaries. TASK-005 runtime smoke remains blocked because approved build/APK, Android TV target, runtime configuration, fixture approvals, redaction, evidence storage and cleanup/rollback prerequisites are still `unknown`.

TASK-011 adds a transition-level coverage model that can be filled by a future approved runtime task without publishing private routes, endpoints, raw evidence, device identifiers or executable Android command recipes.

Official public Android Developers guidance is used as a design reference only:

- `https://developer.android.com/design/ui/tv/guides/foundations/navigation-on-tv`;
- `https://developer.android.com/training/tv/get-started/navigation`.

The model reflects efficient, predictable and intuitive navigation; 4-way D-pad traversal; Select, Back and Home semantics; clear paths to all focusable elements; predictable Back behavior without infinite loops; and axis-based traversal for large hierarchies. These are guideline categories, not confirmed MTC Fog Play runtime behavior.

## Production safety classification

This TASK-011 documentation and local report generation work is `PROD_SAFE`.

Future runtime navigation observation, D-pad execution, Back/Home behavior checks, WebView boundary checks, playback transitions, evidence capture or device/APK interaction are `PROD_CONDITIONAL` and remain blocked until all required prerequisites are approved with `present=true` and `evidence_status=confirmed`.

Endpoint discovery, private route publication, raw logs/screenshots/videos, APK modification, security bypasses, real user data, production mutation and real payments are `PROD_FORBIDDEN`.

## Scope

In scope:

- task specification for TASK-011;
- public-safe navigation transition map;
- public-safe navigation transition report template;
- local fail-closed JSON report generator;
- unit tests for metadata loading, fail-closed behavior, status normalization, CLI output and redaction;
- UTF-8 BOM metadata support;
- redaction of URLs, emails, secret-like values, sessions, cookies, authorization values, API keys, local paths and opaque long values.

Out of scope:

- runtime/device/APK execution;
- executable Android device or runtime command recipes;
- WebView, WebRTC, browser, redirect, backend, network or payment execution;
- endpoint discovery, extraction, publication or inventory;
- private URLs, routes, redirect chains, headers, payloads, cookies, sessions, account identifiers or payment data;
- source code, decompiled code, smali or method bodies;
- raw logs, screenshots, videos, packet captures, dumps or raw evidence;
- APK patching, resigning or modification;
- TLS, pinning, auth or security-control bypass;
- real user data, real payments, production mutation, load testing or destructive actions;

Builder-owned core deliverables do not include governance/source-of-truth docs or release-gate wiring. Those updates are in scope for TASK-011 but are owned by Orchestrator and Docs/Scribe.

## Deliverables

- `tasks/TASK_011_navigation_transition_map.md`
- `docs/qa/navigation-transition-map.md`
- `docs/qa/navigation-transition-report-template.md`
- `automation/navigation_transition_map/__init__.py`
- `automation/navigation_transition_map/generate_navigation_transition_report.py`
- `tests/test_navigation_transition_map.py`

## Required prerequisites

The navigation transition report generator requires all metadata keys below:

- `approved_build`;
- `approved_target`;
- `approved_config`;
- `navigation_scope`;
- `screen_alias_policy`;
- `input_event_policy`;
- `fixture_policy`;
- `resource_budget`;
- `redaction_policy`;
- `evidence_storage`;
- `cleanup_rollback`;
- `security_review`;
- `qa_review`.

Each prerequisite must be a JSON object with:

- `present=true`;
- `evidence_status=confirmed`;
- optional public-safe `note`.

Missing metadata, malformed JSON, non-object JSON, missing prerequisite objects, `present` not true or any non-confirmed evidence status blocks the report. Invalid evidence status normalizes to `unknown`.

## Generator behavior

- `--metadata` accepts an optional public-safe JSON file.
- `--output` writes JSON to a file; otherwise JSON is written to stdout.
- Input is read with UTF-8 BOM support.
- Missing, malformed or non-object metadata emits `overall_status=blocked`.
- Partial or non-confirmed metadata emits `overall_status=blocked`.
- Complete confirmed metadata emits `overall_status=not_run`.
- Planned transitions remain `result=not_run` and `evidence_status=unknown`.
- Optional `screen_aliases`, `transition_edges` and `artifacts` are normalized as public-safe redacted records only.
- The generator must never emit a successful runtime, navigation or device result.
- The generator performs no Android, device, APK, WebView, WebRTC, payment, backend, network or production interaction.

## Acceptance criteria

- No forbidden artifact, credential, private endpoint, route, redirect chain, cookie, token, real account, real payment value, raw evidence, APK artifact or executable runtime/device/network recipe is requested or committed.
- Navigation transition planning is public-safe and fail-closed.
- Runtime navigation execution remains blocked unless future approvals are confirmed.
- Required prerequisites are enforced exactly as fail-closed gates.
- Missing metadata, missing metadata path, malformed metadata and non-object metadata block.
- Invalid evidence status normalizes to `unknown` and blocks.
- Complete confirmed metadata produces only `not_run` planned transitions with `unknown` evidence, never a successful runtime result.
- CLI supports stdout and `--output`.
- Redaction covers URLs, emails, secret-like values, sessions, cookies, authorization values, API keys, local paths and opaque long values.
- Unit tests cover required fail-closed and redaction behavior.

## Verification

- `git status --short --branch`;
- `git diff --check`;
- inspect changed diff;
- `python -m pytest -q tests/test_navigation_transition_map.py`;
- `python -m compileall automation/navigation_transition_map tests/test_navigation_transition_map.py`;
- local dry-run with no metadata;
- local dry-run with public-safe confirmed sample metadata.

Runtime/device/APK/WebView/WebRTC/browser/redirect/payment/backend/network execution is not run for TASK-011.

## Stop conditions

Stop and ask for user or Orchestrator guidance if any requested change would require:

- runtime/device/APK execution;
- Android runtime command recipes;
- WebView, WebRTC, browser, redirect, payment, network, backend, proxy or packet interaction;
- endpoint, private URL, route, redirect chain, cookie, token or payment data discovery, extraction or publication;
- source code or decompiled code;
- private endpoints, secrets, tokens, cookies, sessions or production credentials;
- real accounts, real user data or real payment instruments;
- raw logs, screenshots, videos, packet captures, dumps or endpoint inventories;
- production mutation, load testing, security bypasses or destructive actions;
- governance/source-of-truth docs or release-gate changes outside Builder scope.
