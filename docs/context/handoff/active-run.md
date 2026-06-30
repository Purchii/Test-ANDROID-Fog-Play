# Active run

## Run metadata

Mode: `NON_AUTONOMOUS`
Thread title: `TASK-015G/017B - Residual approval strictness polish + TASK-005 owner approval input pack`
Thread status: `completed_user_authorized_default_push`
Fresh thread verified: `current_thread_renamed_for_task`
Task ID: `TASK-015G/017B`
Task branch: `qa/task-015g-017b-approval-strictness-owner-input-pack`
Default branch: `main`
Base commit: `d308ef0`
Merge/push authority: `user explicitly authorized push to master/default; interpreted as detected default branch main`
Production safety classification: `PROD_SAFE` for docs, validators, schemas,
synthetic unit tests, full-tree hygiene checks, default no-ADB dry-runs and
public-safe owner approval input templates.

Allowed files:

```text
.gitignore
README.md
automation/approvals/validate_approval_metadata.py
automation/device_inventory/generate_adb_device_inventory.py
docs/approvals/*.md
docs/approvals/task005_owner_approval_inputs.template.json
docs/context/current-state.md
docs/context/engineering/quality-gates.md
docs/context/engineering/verification-memory.md
docs/context/governance/decisions-log.md
docs/context/governance/risk-register.md
docs/context/handoff/active-run.md
docs/tasks/backlog.md
tasks/TASK_015G_017B_residual_approval_strictness_owner_input_pack.md
tests/test_approval_metadata_validator.py
tests/test_adb_device_inventory.py
```

## Goal

Complete TASK-015G/017B residual approval strictness polish and TASK-005 owner
approval input pack:

- close residual approval validator false-pass cases from the post-TASK-015F/017A audit;
- harden public-safe owner-review inventory export validation;
- create owner-facing public-safe TASK-005 approval input materials;
- keep TASK-005 runtime smoke `blocked` / `not_run`.

## Allowed scope

- docs;
- validators;
- schemas;
- synthetic unit tests;
- full-tree hygiene scans;
- default no-ADB dry-runs;
- public-safe owner approval templates and checklist.

## Forbidden actions

- APK/AAB/APKS/XAPK handling;
- `adb install`;
- `am start`;
- `monkey`;
- `logcat`;
- screenshots, screenrecord or videos;
- APK install, app launch or runtime smoke;
- WebView, WebRTC, stream/media playback, payment, subscription or purchase flows;
- decompile, patch, resign or security bypass;
- production mutation;
- secrets, private endpoints, raw evidence or raw device identifiers.

## Acceptance criteria

- `approved_build_apk.forbidden_actions` rejects unsupported extras and accepts only the exact required policy set;
- `approved_targets.forbidden_identifiers` is required and rejects missing, unsupported or duplicate values;
- `expires_at` is valid, non-expired and no more than 30 days after validation time;
- TASK-005 APK, synthetic QA user secret and evidence paths use exact approved local path patterns;
- optional synthetic auth policy fields are validated even when auth is out of scope;
- owner-review inventory export rejects malformed redaction guarantees and malformed public enum values;
- owner input template and checklist remain public-safe and do not approve runtime;
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
- APK install/app launch/logcat/screenshots/videos/WebView/WebRTC/payment: `not_run`
- Manual owner/QA target approval: `not_run`
- Owner-review inventory devices: `heuristic` / `manual_review_required`
- Verification: `passed_after_phase_b_docs_remediation`
- Targeted validator/inventory/hygiene tests: `267 passed`
- Full pytest: `367 passed` through both `pytest -q` and `python -m pytest -q`
- Compileall: `passed`
- Approval example/draft CLI: `blocked` / `runtime_execution_status=not_run`
- Default TASK-016 inventory CLI: `blocked` / `runtime_execution_status=not_run`, no `--allow-adb`
- Untracked local archive risk: `mitigated_by_safe_archives_gitignore`; `safe_archives/` remains unstaged and ignored

## Multi-agent status

- Planner: `PASS_READ_ONLY_PLAN`
- Security/Prod-safety Reviewer: `PASS_READ_ONLY_REVIEW`
- Builder: `PASS_IMPLEMENTED_SCOPE`
- Builder implementation auditor: `PASS_FINAL_REVIEW`
- QA Reviewer A: `PASS_FINAL_REVIEW`
- QA Reviewer B: `PASS_FINAL_REVIEW`
- Security/Prod-safety final review: `PASS_FINAL_REVIEW`
- Docs/Scribe: `PASS_FINAL_REVIEW`
- Subagent closure audit: `complete`; Planner, Security, Builder auditor, QA Reviewer A, QA Reviewer B and Docs/Scribe agents closed after outputs were recorded.

## Stop conditions

Stop and ask for user guidance if any requested change would require APK
install/launch, app runtime smoke, `am start`, `monkey`, `logcat`,
screenshots, videos, WebView, WebRTC, stream/media playback, payment,
subscription, purchase, account/profile mutation, secrets, private endpoints,
raw evidence publication, production mutation, decompilation, patching,
resigning, security bypass or default branch merge/push.
