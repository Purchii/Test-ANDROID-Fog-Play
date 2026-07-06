# TASK-025A - No-device selected-lane native regression harness and report hardening

## Mode

`BOUNDED_AUTONOMOUS`

## Objective

Prepare selected-lane native post-auth regression automation for future
TASK-025B while no physical Android TV/STB device was available in that
historical TASK-025A thread.

TASK-025 physical-device runtime execution was deferred in TASK-025A because no
physical Android TV/STB device was available then. TASK-025A is limited to
no-device automation readiness, schema/report hardening and fake/synthetic
tests. TASK-025B will execute selected-lane physical runtime only after a device
is confirmed connected/authorized and owner approvals are refreshed.

## No-device constraints

```text
physical_device_available=false
adb_available_for_this_run=false
runtime_execution_allowed=false
apk_install_allowed=false
app_launch_allowed=false
physical_debugging_allowed=false
raw_runtime_evidence_capture_allowed=false
```

## Allowed

- public-safe docs;
- schemas and validators;
- unit tests with synthetic/fake data;
- dry-run no-device runner;
- fake-driver contract tests;
- public-safe report templates;
- public-safety scans;
- future TASK-025B handoff templates.

## Forbidden

- ADB commands or subprocess-for-ADB;
- APK install/update/read/decompile/patch/resign;
- app launch or UIAutomator real traversal;
- physical-device debugging;
- logcat, screenshots, screenrecord or raw runtime evidence capture;
- reading or printing local secret values;
- private endpoint/deeplink extraction;
- payment, WebView, stream, profile/account mutation or network/offline
  execution.

## Deliverables

- TASK-025 suite/report/model/contract artifacts with
  `task025-native-regression-suite-v1` and
  `task025-native-regression-summary-v1`;
- TASK-025 no-device runner and validator;
- weak-pass validator regression tests;
- synthetic/fake driver contract tests that remain non-runtime evidence;
- TASK-025B physical runtime handoff/checklist/prompt stub;
- source-of-truth updates for no-device status and autonomous audit
  continuation.

## Acceptance

- default runner returns blocked/not-run with physical device unavailable;
- validator accepts the blocked TASK-025A template and rejects weak pass reports;
- fake/synthetic tests are clearly marked and never validate as runtime pass;
- no ADB/runtime/APK/app/debug/evidence-capture action is performed;
- TASK-025B remains deferred until a physical device and refreshed approvals
  exist.
