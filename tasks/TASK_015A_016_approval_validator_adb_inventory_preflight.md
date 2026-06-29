# TASK-015A/016 - Approval validator hardening and ADB device/build inventory preflight

Mode: `NON_AUTONOMOUS`.

Production safety classification:

- `PROD_SAFE` for validator, docs and mocked tests.
- `PROD_CONDITIONAL` for owner-approved local ADB inventory allowlist only.

## Goal

Harden approval metadata validation so invalid TASK-005 runtime approvals fail
closed, then collect only safe local ADB device/build inventory for TASK-016.

## In Scope

- Regression tests for the TASK-015 audit false-pass matrix.
- Strict validator allowlists for approver role, fixtures, evidence capture,
  runtime scope, cleanup levels, structured target aliases and synthetic user
  approval.
- TASK-016 ADB inventory preflight CLI with default no-ADB behavior.
- Mocked unit tests for ADB command allowlist, aliasing, redaction and report
  statuses.
- Local-only raw ADB inventory under `.qa_local/devices/`.
- Public-safe generated inventory with aliases only and no forbidden raw
  identifiers.

## Out Of Scope

- APK install or launch.
- App runtime smoke.
- `am start`, `monkey`, `logcat`, screenshots, screenrecord or videos.
- WebView, WebRTC, stream/media playback, payment, purchase or subscription.
- Account/profile mutation.
- Security bypass, decompilation, patching or resigning.
- Committing raw ADB serials, IP addresses, APKs, logs, screenshots, videos,
  phone numbers, OTPs, tokens, endpoints or private identifiers.

## Acceptance Criteria

- Each audit false-pass mutation blocks validation.
- Happy approval metadata can only return `approved_for_limited_runtime`, with
  runtime execution still `not_run`.
- TASK-016 default CLI performs no ADB calls and returns blocked/not-run.
- TASK-016 `--allow-adb` uses only the approved inventory command allowlist.
- Generated public-safe inventory excludes ADB serial, IP address, MAC, IMEI,
  Android ID, Google account, full build fingerprint, phone number, OTP, owner
  name and room/location labels.
- TASK-016 reports `runtime_execution_status`, `apk_install_status` and
  `app_launch_status` as `not_run`.
- Tests, compileall and diff checks pass.
- Multi-agent Planner, Builder, QA, Security and Docs review complete.

## Verification

Required:

```bash
git status --short --branch
git diff --check
python -m pytest -q tests/test_approval_metadata_validator.py
python -m pytest -q tests/test_adb_device_inventory.py
pytest -q
python -m pytest -q
python -m compileall -q automation tests
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.example.json
python automation/device_inventory/generate_adb_device_inventory.py
```

Owner-approved local inventory:

```bash
python automation/device_inventory/generate_adb_device_inventory.py --allow-adb --raw-output .qa_local/devices/raw_adb_devices.json --alias-map .qa_local/devices/serial_alias_map.json --public-output .qa_local/devices/device_inventory.public_safe.generated.json --report .qa_local/devices/preflight_report.json
```
