# TASK-015B/016A - Final approval validator hardening and ADB inventory rerun/preflight

Mode: `NON_AUTONOMOUS`

Branch: `qa/task-015b-016a-final-validator-adb-preflight`

Production safety classification:

- `PROD_SAFE` for docs, validators, tests and default no-ADB CLI dry-runs.
- `PROD_CONDITIONAL` for owner-approved local TASK-016A ADB inventory allowlist.

## Goal

Close the remaining approval-validator false-pass cases from the post
TASK-015A/016 audit and harden TASK-016A inventory aliases before any future
TASK-005 runtime smoke can be considered.

## In Scope

- Approval metadata validator hardening.
- Regression tests for false-pass cases.
- ADB inventory alias-map sanitizer hardening.
- Device alias and ADB inventory policy docs.
- Source-of-truth documentation updates.
- Default no-ADB CLI dry-run.
- Owner-approved inventory-only ADB rerun when local devices are available.

## Out Of Scope

- APK install.
- App launch.
- `am start`, `monkey`, `logcat`, screenshots or videos.
- Runtime smoke.
- WebView, WebRTC, stream/media playback.
- Payment, subscription or purchase flows.
- Network/offline execution.
- Decompile, patch, resign or security bypass.

## Acceptance Criteria

- P0 TV/STB target with `adb_available: no` or `unknown` blocks.
- Heuristic or manual-review-required runtime targets block.
- Reserved alias tokens block in `device_aliases`, `device_alias` and
  `runtime_profile_alias`.
- Empty or incomplete TASK-005 runtime scope blocks.
- Raw evidence public-report policy blocks.
- APK metadata requires local ignored storage, SHA-256 requirement, private hash
  policy and strict action allow/forbid lists.
- Allowed target categories match structured device categories.
- Existing unsafe serial alias maps block public inventory.
- Generated inventory remains heuristic/manual-review-required.
- Runtime, APK install and app launch statuses remain `not_run`.

## Verification

Required checks:

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

Owner-approved conditional inventory rerun:

```text
python automation/device_inventory/generate_adb_device_inventory.py --allow-adb --raw-output .qa_local/devices/raw_adb_devices.json --alias-map .qa_local/devices/serial_alias_map.json --public-output .qa_local/devices/device_inventory.public_safe.generated.json --report .qa_local/devices/preflight_report.json
```

## Stop Conditions

Stop if requested work requires APK install, app launch, runtime smoke, logcat,
screenshots, videos, raw evidence publication, secrets, private endpoints,
production mutation, decompilation, patching, resigning or security bypass.
