# TASK-015H/017C - Final scope-version/normalization polish + TASK-005 owner approval handoff finalization

Mode: `NON_AUTONOMOUS`

Branch: `qa/task-015h-017c-scope-normalization-owner-handoff`

Production safety classification: `PROD_SAFE` for docs, validators, schemas,
synthetic unit tests, hygiene checks, default no-ADB dry-runs and public-safe
owner handoff material.

## Goal

Close the final concrete pre-runtime false-pass cases found after
TASK-015G/017B and finalize the TASK-005 owner approval handoff boundary.

This is not TASK-005 runtime smoke. TASK-005 remains `blocked`/`not_run`.

## Scope

- Require exact TASK-005 `scope_version`.
- Reject approval-list values with leading/trailing whitespace and duplicates
  after trimming.
- Restrict TASK-005 build aliases to `task-005-local-apk-NNN`.
- Harden public-safe generated inventory metadata before owner-review export.
- Update owner handoff docs to direct the next step toward owner/QA approval
  input and a separate TASK-005 limited runtime task.

## Out Of Scope

- APK/AAB/APKS/XAPK handling.
- ADB inventory refresh or any `--allow-adb` run.
- `adb install`, `am start`, `monkey`, `logcat`, screenshots, screenrecord or
  videos.
- App launch, APK runtime smoke, WebView, WebRTC, stream/media playback,
  payment, subscription, purchase, network/offline runtime flows or production
  mutation.
- Decompilation, patching, resigning, security bypass or private endpoint
  discovery.

## Acceptance Criteria

- `scope_version=task-999-all-runtime` blocks.
- Whitespace duplicates such as `install` plus ` install ` block.
- Generic or unsafe build aliases such as `task-qa-user-001` block.
- Owner-review export rejects malformed public-safe generated inventory metadata
  such as raw source, non-redacted devices, invalid timestamp, missing or
  mismatched `public_device_count`, and empty device lists.
- TASK-005 owner input materials remain public-safe templates only.
- TASK-005 runtime remains `blocked`/`not_run`.

## Verification

Required local checks:

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

The final command must run without `--allow-adb` and must not call ADB.
