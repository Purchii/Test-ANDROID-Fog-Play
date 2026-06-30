# TASK-015C/016B - Approval/device-inventory consistency polish and local ADB inventory readiness

Mode: `NON_AUTONOMOUS`
Branch: `qa/task-015c-016b-approval-inventory-consistency`
Base commit: `0832867`
Production safety: `PROD_SAFE` for docs, validators, unit tests and default
dry-runs; `PROD_CONDITIONAL` for owner-approved TASK-016B inventory-only ADB
preflight when local `adb` and authorized devices are available.

## Goal

Close the post TASK-015B/016A consistency gaps before any future TASK-005
runtime smoke. This task does not install, launch or run the app.

## Scope

- Fix whitespace quality gate regressions.
- Allow `phone-*` device/runtime aliases only for structured phone targets and
  block `phone` in later alias segments.
- Validate runtime profile alias prefix/index and Android major consistency.
- Block manual-confirmed TV/STB approval targets whose alias prefix disagrees
  with structured form factor.
- Add semantic reserved-token checks for build aliases.
- Require evidence capture modes that match TASK-005 runtime scope.
- Require explicit `runtime_execution.auth_mode`.
- Restore public-safe phone inventory examples.

## Out of scope

- APK install or launch.
- `am start`, `monkey`, `logcat`, screenshots, videos or screenrecord.
- WebView, WebRTC, media playback, payment, network/offline runtime flows.
- Decompile, patch, resign, endpoint extraction, secrets or raw identifiers.

## Verification

Required local verification:

```text
git status --short --branch
git diff --check
python -m pytest -q tests/test_approval_metadata_validator.py tests/test_adb_device_inventory.py
pytest -q
python -m pytest -q
python -m compileall -q automation tests
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.example.json
python automation/device_inventory/generate_adb_device_inventory.py
```

Optional TASK-016B local ADB inventory may run only when `adb` is available and
local authorized devices are visible. Raw outputs must remain ignored under
`.qa_local/devices/`.

## Result

The validator and inventory tooling now block the requested consistency cases
and keep app runtime status `not_run`. In this task environment `adb` was not
available in PATH, so the explicit TASK-016B ADB inventory command was not run.
