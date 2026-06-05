# TASK-009 - Compatibility/device matrix and report format

## Task

Create a public-safe compatibility/device matrix policy and local fail-closed report generator for future approved Android TV compatibility QA work.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-009 - Compatibility/device matrix and report format
```

## Branch

```text
qa/task-009-device-matrix
```

## Context

TASK-001 through TASK-004 created blocked runtime discovery, reporting and screen/focus map foundations. TASK-006 defined fixture approval boundaries. TASK-007 added a local fail-closed network/offline runner. TASK-009 adds the public-safe matrix layer needed to plan compatibility coverage across Android TV target categories without executing device, APK, runtime, network, WebView, WebRTC or payment flows.

## Production safety classification

This TASK-009 documentation and local report generation work is `PROD_SAFE`.

Future compatibility execution on Android TV devices, emulators or production-like builds is `PROD_CONDITIONAL` and remains blocked until all required prerequisites are approved with `present=true` and `evidence_status=confirmed`.

## Scope

In scope:

- task specification for TASK-009;
- public-safe compatibility/device matrix policy;
- public-safe compatibility report template;
- local fail-closed JSON report generator;
- unit tests for metadata loading, fail-closed behavior, status normalization, CLI output and redaction;
- UTF-8 BOM metadata support;
- redaction of URLs, emails, secret-like values, sessions, cookies, authorization values, API keys, local paths, device identifiers and opaque long values.

Out of scope:

- runtime/device/APK execution;
- executable Android device command recipes;
- device inventory extraction or publication;
- serial numbers, IMEI/IMSI, Android IDs, MAC addresses or other private device identifiers;
- WebView, WebRTC, payment, backend, proxy, packet, network or production interaction;
- source code, decompiled code, smali or method bodies;
- secrets, tokens, cookies, sessions, production credentials or private endpoints;
- raw logs, screenshots, videos, packet captures, dumps or raw evidence;
- APK patching, resigning or modification;
- TLS, pinning, auth or security-control bypass;
- real user data, real payments, production mutation, load testing or destructive actions;
- governance/source-of-truth updates outside the Builder-owned core TASK-009 deliverables.

## Deliverables

- `tasks/TASK_009_compatibility_device_matrix_report_format.md`
- `docs/qa/compatibility-device-matrix.md`
- `docs/qa/compatibility-device-matrix-report-template.md`
- `automation/compatibility_device_matrix/__init__.py`
- `automation/compatibility_device_matrix/generate_compatibility_device_matrix_report.py`
- `tests/test_compatibility_device_matrix.py`

## Required prerequisites

The compatibility matrix generator requires all metadata keys below:

- `approved_build`;
- `approved_target`;
- `approved_config`;
- `device_inventory_policy`;
- `matrix_scope`;
- `compatibility_criteria`;
- `redaction_policy`;
- `evidence_storage`;
- `fixture_policy`;
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
- Planned compatibility checks remain `result=not_run` and `evidence_status=unknown`.
- Optional `device_profiles` are normalized as public-safe aliases only.
- Optional `artifacts` are normalized as public-safe redacted references only.
- The generator must never emit a successful runtime result.
- The generator performs no Android, device, APK, WebView, WebRTC, payment, backend, proxy, packet, network or production interaction.

## Acceptance criteria

- Only the approved TASK-009 core deliverable files are created or updated by Builder.
- Markdown docs are public-safe and ASCII-only.
- No executable Android/device/network recipes, private endpoints, device identifiers, packet/proxy details, TLS bypass instructions, secrets, raw evidence or production-impacting actions are introduced.
- Required prerequisites are enforced exactly as fail-closed gates.
- Missing metadata, malformed metadata and non-object metadata block.
- Invalid evidence status normalizes to `unknown` and blocks.
- Complete confirmed metadata produces only `not_run` planned checks with `unknown` evidence, never a successful runtime result.
- CLI supports stdout and `--output`.
- Redaction covers URLs, emails, secret-like values, sessions, cookies, authorization values, API keys, local paths, device identifiers and opaque long values.
- Unit tests cover required fail-closed and redaction behavior.

## Verification

- `git status --short --branch`;
- `git diff --check`;
- inspect changed diff;
- verify ASCII-only content for TASK-009 markdown deliverables;
- `python -m pytest -q tests/test_compatibility_device_matrix.py`;
- `python -m pytest -q`;
- `python -m compileall automation tests`;
- local dry-run with no metadata;
- local dry-run with public-safe confirmed sample metadata;
- scan changed files for forbidden content classes such as secrets, private endpoints, device identifiers, APK artifacts, raw evidence and executable Android/device/runtime/network recipes.

Runtime/device/APK/WebView/WebRTC/network/backend/proxy/packet/payment execution is not run for TASK-009.

## Stop conditions

Stop and ask for user or Orchestrator guidance if any requested change would require:

- runtime/device/APK execution;
- Android runtime command recipes;
- device inventory extraction or raw device identifier publication;
- WebView, WebRTC, payment, network, backend, proxy or packet interaction;
- endpoint discovery, extraction or publication;
- source code or decompiled code;
- private endpoints, secrets, tokens, cookies, sessions or production credentials;
- real accounts, real user data or real payment instruments;
- raw logs, screenshots, videos, packet captures, dumps or endpoint inventories;
- production mutation, load testing, security bypasses or destructive actions;
- edits outside the approved Builder write scope;
- default branch merge/push.
