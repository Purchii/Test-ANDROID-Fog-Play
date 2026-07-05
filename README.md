# MTC Fog Play Android QA

Public-safe QA automation and process repository for Android TV / hybrid /
WebView / WebRTC testing of MTC Fog Play.

## Current Safety Status

- Current selected-lane evidence includes TASK-005 startup/focus smoke,
  TASK-019 auth/session smoke, TASK-020 post-auth navigation and full screen
  inventory, TASK-021 reversible DNS offline-like network data point, TASK-022
  Xbox-like/gamepad inventory and TASK-023 full data inventory on
  `tv-tpv-013` / `tv-tpv-a12-013`.
- TASK-024 adds a native post-auth regression model, suite, fail-closed runner
  and public-safe validator derived from TASK-020/021/022/023 evidence.
- TASK-025A adds no-device selected-lane native regression readiness only:
  TASK-025 suite/report contracts, no-device runner, validator hardening,
  synthetic/fake contract tests and TASK-025B handoff. Physical runtime is
  deferred until a device is available and owner approvals are refreshed.
- TASK-026A expands XL+ no-device TASK-025B readiness coverage with stricter
  local report/preflight/boundary/evidence contract tests. It does not run ADB,
  inspect APKs or `.qa_local`, launch the app, collect runtime evidence or
  validate real device/app behavior.
- TASK-017 adds a synthetic-only redaction corpus for local validator/redactor
  tests; it does not inspect real evidence, APKs, endpoints, QR targets or
  device data.
- TASK-018 adds tracked-docs link and public-reference sanity checks only; it
  does not crawl external links or inspect ignored local evidence.
- Broader runtime lanes remain blocked or `not_run` until explicit confirmed
  approvals.
- TASK-016 allows inventory-only local ADB preflight after owner approval; raw
  ADB output and serial alias maps remain under ignored `.qa_local/devices/`.
- APK files, raw evidence, secrets, private endpoints and device identifiers are
  local-only and ignored by default.
- Reports and validators fail closed when evidence is missing or not confirmed.
- TASK-015 adds approval metadata validation only; it does not run the app.
- TASK-015A hardens approval validation with strict allowlists.
- TASK-015C/016B hardens approval/device inventory consistency without runtime
  execution.
- TASK-015D/016C uses a two-phase hard gate: Phase B inventory-only ADB is
  blocked until Phase A approval hardening passes.
- TASK-015F/017A hardens strict schema, hygiene and owner-review validation
  only; it does not approve or run TASK-005.
- TASK-015G/017B hardens residual approval strictness and adds owner approval
  input templates only; it does not approve or run TASK-005.
- TASK-016 inventory preflight does not install, launch, capture logcat,
  screenshots or videos, and always reports runtime/app statuses as `not_run`.
- Current runtime evidence is selected-lane evidence only. It is not exhaustive
  app navigation proof, not payment/WebView/stream/session-start proof, not
  broad compatibility proof and not complete dynamic game/server data
  enumeration.

## Source Of Truth

Read these before substantial work:

```text
AGENTS.md
CODEX_ANDROID_QA_PROJECT_TZ.md
docs/codex/*.md
docs/context/current-state.md
docs/context/handoff/active-run.md
docs/context/governance/decisions-log.md
docs/context/governance/risk-register.md
docs/context/engineering/quality-gates.md
docs/context/engineering/verification-memory.md
docs/tasks/backlog.md
docs/qa/approval-dependency-map.md
docs/qa/evidence-schema.md
docs/qa/synthetic-redaction-policy-test-corpus.md
docs/approvals/*.md
```

## Safe Commands

```bash
pytest -q
python -m pytest -q
python -m compileall automation tests
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.example.json
python automation/device_inventory/generate_adb_device_inventory.py
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/docs_consistency_link_sanity.py
python automation/quality/public_repo_safety_scan.py
python automation/quality/synthetic_redaction_corpus.py --json
python automation/native_regression/validate_task025_native_regression_report.py --report docs/qa/reports/task025_selected_lane_native_regression.summary.template.json
python automation/native_regression/run_task025_selected_lane_regression.py
```

These commands are local and public-safe. They must not connect to devices, run
APK files, capture raw evidence or contact production systems.

Owner-approved local inventory command for TASK-016 only:

```bash
python automation/device_inventory/generate_adb_device_inventory.py \
  --allow-adb \
  --raw-output .qa_local/devices/raw_adb_devices.json \
  --alias-map .qa_local/devices/serial_alias_map.json \
  --public-output .qa_local/devices/device_inventory.public_safe.generated.json \
  --report .qa_local/devices/preflight_report.json
```

This command may run only the approved ADB inventory allowlist and must not
install, launch, smoke test, use logcat, capture screenshots/videos or mutate
device/account/application state.

For TASK-015D/016C, this command is Phase B only. It may not run until the
Phase A approval-hardening gate passes, and generated inventory remains
heuristic/manual-review-required until separate owner/QA manual review.

## Local-Only Artifacts

Use ignored `.qa_local/` storage for APKs, device inventory, evidence and
secrets. Do not commit raw APKs, logs, screenshots, videos, phone numbers, OTPs,
tokens, cookies, sessions, device serials, IMEI, MAC, Android ID, private
routes, deeplinks or endpoint details.
