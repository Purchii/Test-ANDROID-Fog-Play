# TASK-026A - XL+ no-device TASK-025B readiness and regression coverage

## Mode

`BOUNDED_AUTONOMOUS`

## Production safety classification

`PROD_SAFE` only.

## Objective

Expand local no-device TASK-025B readiness and native-regression contract
coverage around the existing TASK-024/TASK-025 runner, validator and report
schema. This task prepares the harness for a future physical TASK-025B selected
lane run, but does not execute or validate physical runtime behavior.

## Allowed

- public-safe docs/source-of-truth updates;
- local validator and runner contract hardening;
- unit tests with synthetic/fake data;
- blocked/not-run no-device report template generation;
- public-safe hygiene and docs consistency checks.

## Forbidden

- ADB, emulator/device runtime, app launch or UIAutomator traversal;
- APK read/hash/install/update/decompile/patch/resign;
- `.qa_local` inspection;
- local secrets, raw phone/OTP values, raw QR targets, private endpoints or
  raw runtime evidence;
- logcat, screenshots, screenrecord, XML dumps or videos;
- payment, WebView/browser, stream/WebRTC/media, Steam/account connection,
  profile/account mutation, network/offline manipulation or production
  interaction.

## Deliverables

- stricter TASK-025 report/preflight/evidence/boundary validator invariants;
- broad TASK-026A no-device regression tests for positive blocked/not-run
  behavior and negative false-pass/public-safety cases;
- updated TASK-025B handoff/checklist/contract docs;
- source-of-truth updates that keep TASK-025B deferred until physical-device
  availability and refreshed owner approvals are confirmed.

## Acceptance

- default TASK-025 runner remains blocked/not-run with
  `physical_device_status=unavailable`, empty runtime evidence IDs and
  `task025b_preflight.preflight_status=deferred_no_device`;
- synthetic/fake contract execution remains
  `execution_mode=no_device_synthetic_contract_test` and
  `counts_as_runtime_evidence=false`;
- validator rejects weak/fake passes, missing confirmed preflight/evidence,
  inconsistent runtime/Phase C/TASK-025B status combinations, malformed
  anomalies, duplicate evidence IDs, unsafe coverage claims, raw public
  values/paths/artifacts and boundary overclaims;
- future physical pass fixtures remain schema-only test fixtures and require
  concrete physical-runtime/preflight/evidence fields;
- no forbidden runtime/APK/ADB/raw evidence/secrets actions are performed.

## Builder assessment summary

Builder reviewed the candidate diff as PROD_SAFE tracked-source work only and
confirmed the implementation direction is aligned with the XL+ no-device goal:
TASK-025B readiness contracts are stricter, while runtime/device/APK evidence
is neither produced nor claimed.

Builder recommendations to close before merge:

- ensure the new TASK-026A test module is tracked;
- run full pytest, compileall, hygiene, public repository safety and docs
  consistency checks;
- complete active-run and verification-memory;
- keep `public_safety.*_invoked` semantics documented as no-device/unsafe
  invocation flags rather than proof that future physical runtime actions did
  or did not occur.

## Verification plan

```text
git status --short --branch
git diff --check
python -m pytest -q tests/test_task025_native_regression.py tests/test_task025_native_regression_validator.py tests/test_task026a_no_device_readiness_coverage.py
python -m pytest -q tests/test_native_regression_probe.py tests/test_native_regression_report_validator.py
pytest -q
python -m pytest -q
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
python automation/native_regression/validate_task025_native_regression_report.py --report docs/qa/reports/task025_selected_lane_native_regression.summary.template.json
python automation/native_regression/run_task025_selected_lane_regression.py
```

All commands are local/public-safe and must not connect to devices, run APKs,
read ignored local evidence or contact production systems.
