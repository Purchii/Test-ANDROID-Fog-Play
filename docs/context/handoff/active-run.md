# Active run

## Run metadata

Mode: `NON_AUTONOMOUS`
Thread title: `TASK-015F/017A - Final strict-schema polish + owner target review handoff`
Thread status: `inactive_completed_default_push_authorized`
Fresh thread verified: `current_thread_renamed_for_task`
Task ID: `TASK-015F/017A`
Task branch: `qa/task-015f-017a-final-strict-schema-owner-target-handoff`
Default branch: `main`
Base commit: `e4eae81`
Task branch pushed: `yes`
Default branch merge/push: `user_authorized_push_to_master_interpreted_as_main`
Production safety classification: `PROD_SAFE` for docs, validators, schemas,
synthetic unit tests, full-tree hygiene scan, public-safe review export
validation and owner handoff.
Multi-agent status: `complete_passed_after_remediation`

## Goal

Complete TASK-015F/017A final strict-schema polish and owner target review
handoff:

- close remaining approval metadata validator false-pass cases;
- make full-tree hygiene scanner portable for both git checkouts and extracted
  public-safe archive trees;
- harden public-safe device inventory review export validation;
- add owner-facing TASK-005 P0 TV/STB target review handoff;
- keep TASK-005 runtime smoke `blocked` / `not_run`.

## Allowed scope

- docs;
- validators;
- schemas;
- synthetic unit tests;
- full-tree hygiene scans;
- default no-ADB dry-runs;
- public-safe owner-review inventory validation.

## Forbidden actions

- APK/AAB/APKS/XAPK handling;
- `adb install`;
- `am start`;
- `monkey`;
- `logcat`;
- screenshots, screenrecord or videos;
- APK install, app launch or runtime smoke;
- WebView, WebRTC, stream/media playback, payment, subscription or purchase
  flows;
- decompile, patch, resign or security bypass;
- production mutation;
- secrets, private endpoints, raw evidence or raw device identifiers.

## Acceptance criteria

- approval validator blocks strict schema/key drift, broad path variants,
  stable aliases with Android-version tokens, Android major/API mismatch,
  duplicate auxiliary approval lists and invalid `runtime_execution.forbidden_scope`;
- hygiene scanner supports `--mode auto`, `--mode tracked` and
  `--mode public-safe-tree`;
- owner-review export blocks malformed aliases, alias/form-factor/API drift,
  duplicate aliases, count mismatch, unknown public fields and auto-promotion;
- `docs/approvals/task005_owner_device_review.md` lists the 6 P0 TV/STB
  candidates and states that owner/QA manual confirmation is required;
- example and draft approval metadata remain `blocked` / `not_run`;
- TASK-005 remains `blocked` / `not_run`.

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
- Manual owner/QA review of generated inventory: `not_run`
- Owner-review P0 candidates: `6`, from
  `docs/approvals/device_inventory.public_safe.review.json`
- Verification: `passed_after_qa_a_remediation`

## Multi-agent result

- Orchestrator: `PASS`
- Planner: `PASS_READ_ONLY_PLAN`
- Builder: `PASS_HYGIENE_SCANNER_SCOPE`
- QA Reviewer A: `PASS_AFTER_TOP_LEVEL_OWNER_REVIEW_FIELD_ALLOWLIST_REMEDIATION`
- QA Reviewer B: `PASS_READ_ONLY_FINAL_REVIEW`
- Security/Prod-safety Reviewer: `PASS_FINAL_REVIEW`
- Docs/Scribe: `PASS_AFTER_STATE_RECONCILIATION`

## Stop conditions

Stop and ask for user guidance if any requested change would require APK
install/launch, app runtime smoke, `am start`, `monkey`, `logcat`,
screenshots, videos, WebView, WebRTC, stream/media playback, payment,
subscription, purchase, account/profile mutation, secrets, private endpoints,
raw evidence publication, production mutation, decompilation, patching,
resigning, security bypass or default branch merge/push.
