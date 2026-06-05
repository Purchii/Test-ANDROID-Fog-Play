# TASK-007 - Network/offline policy and safe runner

## Task

Create the public-safe network/offline test policy and local fail-closed safe runner for future approved Android TV network/offline QA work.

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

```text
TASK-007 - Network/offline policy and safe runner
```

## Branch

```text
qa/task-007-network-offline-policy
```

## Context

TASK-006 defined the fixture contract needed before runtime-dependent QA can use synthetic users, sessions, streams, WebView, payment, network/offline profiles, redaction, evidence storage and cleanup rules.

TASK-007 adds a public-safe network/offline policy and a local report generator that can prepare a blocked or not-run JSON report without any Android, device, APK, backend, proxy, packet, network or production interaction.

## Production safety classification

This TASK-007 documentation and local report generation work is `PROD_SAFE`.

Future network/offline runtime execution is `PROD_CONDITIONAL` and remains blocked until all required prerequisites are approved with `present=true` and `evidence_status=confirmed`.

## Scope

In scope:

- task specification for TASK-007;
- public-safe network/offline policy;
- public-safe runner report template;
- local fail-closed JSON report generator;
- unit tests for metadata loading, fail-closed behavior, status normalization, CLI output and redaction;
- UTF-8 BOM metadata support;
- redaction of URLs, emails, secret-like pairs, sessions, cookies, authorization values, API keys, local paths and opaque long values.

Out of scope:

- runtime/device/APK execution;
- Android device command recipes;
- network, backend, proxy, packet capture or traffic interaction;
- endpoint discovery, extraction, publication or inventory;
- source code, decompiled code, smali or method bodies;
- secrets, tokens, cookies, sessions, production credentials or private endpoints;
- raw logs, screenshots, videos, packet captures, dumps or raw evidence;
- APK patching, resigning or modification;
- TLS, pinning, auth or security-control bypass;
- real user data, real payments, production mutation, load testing or destructive actions;
- updates to governance or source-of-truth docs by Builder.

## Deliverables

- `tasks/TASK_007_network_offline_policy_safe_runner.md`
- `docs/qa/network-offline-policy.md`
- `docs/qa/network-offline-runner-report-template.md`
- `automation/network_offline_safe_runner/__init__.py`
- `automation/network_offline_safe_runner/generate_network_offline_report.py`
- `tests/test_network_offline_safe_runner.py`

## Required prerequisites

The safe runner requires all metadata keys below:

- `approved_build`;
- `approved_target`;
- `approved_config`;
- `network_profile_policy`;
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

## Runner behavior

- `--metadata` accepts an optional public-safe JSON file.
- `--output` writes JSON to a file; otherwise JSON is written to stdout.
- Input is read with UTF-8 BOM support.
- Missing, malformed or non-object metadata emits `overall_status=blocked`.
- Partial or non-confirmed metadata emits `overall_status=blocked`.
- Complete confirmed metadata emits `overall_status=not_run`.
- Planned network/offline checks remain `result=not_run` and `evidence_status=unknown`.
- The runner must never emit a successful runtime result.
- The runner performs no Android, device, APK, backend, proxy, packet, network or production interaction.

## Acceptance criteria

- Only the approved TASK-007 deliverable files are created or updated by Builder.
- Markdown docs are public-safe and ASCII-only.
- No executable Android/device/network recipes, private endpoints, packet/proxy details, TLS bypass instructions, secrets, raw evidence or production-impacting actions are introduced.
- Required prerequisites are enforced exactly as fail-closed gates.
- Missing metadata, malformed metadata and non-object metadata block.
- Invalid evidence status normalizes to `unknown` and blocks.
- Complete confirmed metadata produces only `not_run` planned checks with `unknown` evidence, never a successful runtime result.
- CLI supports stdout and `--output`.
- Redaction covers URLs, emails, secret-like values, sessions, cookies, authorization values, API keys, local paths and opaque long values.
- Unit tests cover required fail-closed and redaction behavior.

## Verification

- `git status --short --branch`;
- `git diff --check`;
- inspect changed diff;
- verify ASCII-only content for TASK-007 docs;
- `python -m pytest -q tests/test_network_offline_safe_runner.py`;
- `python -m pytest -q`;
- `python -m compileall automation tests`;
- local dry-run with no metadata;
- local dry-run with public-safe confirmed sample metadata;
- scan changed files for forbidden content classes such as secrets, private endpoints, packet/proxy recipes, TLS bypass instructions, APK artifacts, raw evidence and executable Android/device/network recipes.

Runtime/device/APK/WebView/WebRTC/network/backend/proxy/packet/payment execution is not run for TASK-007.

## Stop conditions

Stop and ask for user or Orchestrator guidance if any requested change would require:

- runtime/device/APK execution;
- Android runtime command recipes;
- network, backend, proxy or packet interaction;
- endpoint discovery, extraction or publication;
- source code or decompiled code;
- private endpoints, secrets, tokens, cookies, sessions or production credentials;
- real accounts, real user data or real payment instruments;
- raw logs, screenshots, videos, packet captures, dumps or endpoint inventories;
- production mutation, load testing, security bypasses or destructive actions;
- edits outside the approved Builder write scope;
- default branch merge/push.
