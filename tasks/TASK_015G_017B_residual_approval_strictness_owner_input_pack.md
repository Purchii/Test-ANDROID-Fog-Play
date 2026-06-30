# TASK-015G/017B - Residual approval strictness polish + TASK-005 owner approval input pack

Mode: `NON_AUTONOMOUS`

Production safety classification: `PROD_SAFE` for docs, validators, schemas,
synthetic unit tests, hygiene checks, default no-ADB dry-runs and public-safe
owner approval input templates.

## Goal

Close the residual post-TASK-015F/017A approval false-pass gaps and create the
public-safe owner input pack needed before a future separate TASK-005 limited
runtime smoke can be considered.

## Scope

- approval metadata validator strictness;
- owner-review inventory export strictness;
- regression tests for residual audit findings;
- public-safe owner approval input template and checklist;
- source-of-truth docs updates.

## Out Of Scope

- TASK-005 runtime smoke;
- APK install, app launch or app modification;
- `adb install`, `am start`, `monkey`, `logcat`, screenshots or videos;
- WebView, WebRTC, stream/media playback, payment, subscription or purchase;
- secrets, raw device identifiers, private endpoints or raw evidence;
- production mutation, security bypass, decompile, patch or resign.

## Acceptance Criteria

- `approved_build_apk.forbidden_actions` rejects unsupported extras and accepts only the exact required policy set.
- `approved_targets.forbidden_identifiers` is required and rejects missing, unsupported or duplicate values.
- `expires_at` is valid, non-expired and no more than 30 days after validation time.
- TASK-005 APK, synthetic secret and evidence paths use exact approved local path patterns.
- Optional synthetic auth policy fields are validated even when auth is out of scope.
- Owner-review export rejects malformed redaction guarantees and malformed public enum values.
- Owner input template and checklist remain public-safe and do not approve runtime.
- TASK-005 remains `blocked` / `not_run`.

## Verification

Required gate:

```text
git status --short --branch
git diff --check
git diff --cached --check
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python -m pytest -q tests/test_approval_metadata_validator.py tests/test_adb_device_inventory.py tests/test_full_tree_hygiene_scan.py
pytest -q
python -m pytest -q
python -m compileall -q automation tests
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.example.json
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.task005.draft.json
python automation/device_inventory/generate_adb_device_inventory.py
```
