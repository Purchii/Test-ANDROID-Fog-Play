# TASK-025B - Selected-lane physical native regression runtime

## Mode

`NON_AUTONOMOUS`

## Production safety classification

`PROD_SAFE` for tracked docs/source, no-device contract validation and public
report/schema checks.

Physical runtime is `PROD_CONDITIONAL`. In this run it was executed only after
refreshed owner approval and preflight, and stopped before forbidden payment,
WebView/browser, external QR traversal, stream/session, Steam/account,
profile/account and network/offline actions.

## Objective

Execute selected-lane physical native regression cases `NR-001` through
`NR-010` only after the TASK-025B preflight checklist is confirmed.

Use TASK-026B artifacts as implementation readiness input only:

- `docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json`;
- `automation/native_regression/run_task026b_no_device_task025b_runtime_tests.py`;
- `automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py`;
- `docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json`.

These artifacts do not count as runtime evidence.

## Current status

Closed as `partial` in the fresh 2026-07-06 TASK-025B thread after the owner
requested finishing the current task and stopping.

The selected-lane physical runtime did execute. Refreshed preflight confirmed
device availability/authorization, selected lane aliases, the Television Full
APK family under ignored `.qa_local/apks/task-005/`, local-only APK hash
recording, synthetic QA env existence, ignored evidence storage and
cleanup/recovery policy. The APK installed and the app launched.

This is not a full pass. `NR-001`, `NR-002`, `NR-003`, `NR-006`, `NR-009` and
`NR-010` passed within the selected-lane boundary; `NR-004` is a known anomaly;
`NR-005` and `NR-007` are boundary-blocked; `NR-008` is not run. Public-safe
report:
`docs/qa/reports/task025b_selected_lane_physical_runtime.summary.json`.

Complete transition coverage, complete data-source coverage, the game-detail
server-list path, Search typed no-results recovery and Settings Gamepad safe
entry remain unverified.

## Runtime gates

Before any ADB/APK/app action, confirm all of:

- physical Android TV/STB connected and authorized;
- selected device aliases and runtime profile alias refreshed/confirmed;
- owner-selected APK present only under ignored `.qa_local/apks/task-005/`;
- APK SHA-256 recorded local-only without printing or committing the value;
- synthetic QA user env present under ignored `.qa_local/secrets/qa_user.env`;
- evidence capture/storage/redaction approval explicit;
- cleanup/rollback policy explicit;
- QA and Security/Prod-safety approve the runtime boundary.

## Forbidden without a separate later approval

- real payment completion or paid session start;
- opening/following external QR/WebView/browser targets;
- stream/WebRTC/media playback/game session start;
- Steam/account connection mutation;
- profile/account mutation beyond explicitly approved safe checks;
- network/offline manipulation;
- APK patch/decompile/resign or security bypass;
- printing or committing raw APK hashes, phone/OTP, device identifiers, QR
  targets, endpoints, screenshots, logs, XML, video or private values.

## Verification baseline

```text
git status --short --branch
git diff --check
python automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py --scenarios docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json --report docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json
python automation/native_regression/run_task026b_no_device_task025b_runtime_tests.py
python automation/native_regression/run_task026b_no_device_task025b_runtime_tests.py --synthetic-sequencing-test
python automation/native_regression/validate_task025_native_regression_report.py --report docs/qa/reports/task025_selected_lane_native_regression.summary.template.json
python automation/native_regression/run_task025_selected_lane_regression.py
python -m pytest -q tests/test_task025_native_regression.py tests/test_task025_native_regression_validator.py tests/test_task026a_no_device_readiness_coverage.py tests/test_task026b_no_device_task025b_physical_runtime_tests.py
python -m compileall -q automation tests
python automation/quality/public_repo_safety_scan.py
```

Runtime/device checks are allowed only after the gates above are confirmed.
