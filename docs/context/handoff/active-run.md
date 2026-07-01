# Active run

## Run metadata

Mode: `NON_AUTONOMOUS`
Thread title: `TASK-015H/017C - Final scope-version/normalization polish + TASK-005 owner approval handoff finalization`
Thread status: `completed_user_authorized_default_push`
Fresh thread verified: `current_thread_renamed_for_task`
Task ID: `TASK-015H/017C`
Task branch: `qa/task-015h-017c-scope-normalization-owner-handoff`
Default branch: `main`
Base commit: `c3bd70f`
Merge/push authority: `user explicitly authorized push to master/default; interpreted as detected default branch main`
Production safety classification: `PROD_SAFE` for docs, validators, schemas,
synthetic unit tests, hygiene checks, default no-ADB dry-runs and public-safe
owner handoff material.

## Goal

Complete final pre-runtime approval strictness polish and owner handoff
finalization:

- require exact TASK-005 `scope_version`;
- block approval-list whitespace variants and duplicates after trimming;
- restrict TASK-005 build aliases to `task-005-local-apk-NNN`;
- block malformed public-safe generated inventory metadata before owner-review
  export;
- keep TASK-005 runtime `blocked` / `not_run`.

## Allowed scope

- docs;
- validators;
- schemas;
- synthetic unit tests;
- full-tree hygiene scans;
- default no-ADB dry-runs;
- public-safe owner approval handoff docs.

## Forbidden actions

- APK/AAB/APKS/XAPK handling;
- ADB inventory refresh or any `--allow-adb` run;
- `adb install`;
- `am start`;
- `monkey`;
- `logcat`;
- screenshots, screenrecord or videos;
- APK install, app launch or runtime smoke;
- WebView, WebRTC, stream/media playback, payment, subscription or purchase
  flows;
- network/offline runtime flows;
- decompile, patch or resign APK;
- security bypass, proxy/packet capture or TLS bypass;
- production mutation;
- secrets, private endpoints, raw evidence or raw device identifiers.

## Acceptance criteria

- `scope_version=task-999-all-runtime` blocks.
- `runtime_execution.allowed_scope` containing both `install` and ` install `
  blocks.
- `runtime_execution.forbidden_scope`, APK actions and cleanup levels also
  block whitespace duplicates.
- Unsafe/generic `approved_build_apk.build_alias` values such as
  `task-qa-user-001` block.
- Owner-review export rejects raw source metadata, non-redacted device payloads,
  invalid `generated_at_utc`, missing or mismatched `public_device_count`, and
  empty device lists.
- Owner handoff docs say this is final pre-runtime polish and the next step is
  owner/QA input plus a separate TASK-005 limited runtime task.
- TASK-005 runtime remains `blocked` / `not_run`.

## Verification plan

Required commands:

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

## Current evidence status

- TASK-005 runtime execution: `blocked`
- APK install/app launch/logcat/screenshots/videos/WebView/WebRTC/payment:
  `not_run`
- Manual owner/QA target approval: `not_run`
- Owner-review inventory devices: `heuristic` / `manual_review_required`
- Diff checks: `passed`
- Full-tree hygiene auto/public-safe-tree: `passed`
- Targeted validator/inventory/hygiene tests: `285 passed`
- Full pytest: `385 passed` through both `pytest -q` and `python -m pytest -q`
- Compileall: `passed`
- Approval example/draft CLI: `blocked` / `runtime_execution_status=not_run`
- Default TASK-016 inventory CLI: `blocked` / `runtime_execution_status=not_run`, no `--allow-adb`
- Tracked APK/.qa_local scan: `no tracked files`

## Multi-agent status

- Planner: `PASS_READ_ONLY_PLAN`
- Security/Prod-safety Reviewer: `PASS_READ_ONLY_REVIEW`
- Builder: `PASS_IMPLEMENTED_SCOPE`
- QA Reviewer A: `PASS_FINAL_REVIEW`
- QA Reviewer B: `PASS_FINAL_REVIEW`
- Security/Prod-safety final review: `PASS_FINAL_REVIEW`
- Docs/Scribe: `PASS_FINAL_REVIEW_AFTER_REMEDIATION`
- Subagent closure audit: `complete`; Planner, Security pre-check,
  QA Reviewer A, QA Reviewer B, Security final and Docs/Scribe agents closed
  after outputs were recorded.

## Stop conditions

Stop and ask for user guidance if any requested change would require APK
install/launch, app runtime smoke, ADB inventory refresh, `--allow-adb`,
`am start`, `monkey`, `logcat`, screenshots, videos, WebView, WebRTC,
stream/media playback, payment, subscription, purchase, account/profile
mutation, secrets, private endpoints, raw evidence publication, production
mutation, decompilation, patching, resigning, security bypass or default branch
merge/push.
