# TASK-015E/017 - Final metadata hardening and inventory review package

Mode: `BOUNDED_AUTONOMOUS`
Branch: `qa/task-015e-017-final-metadata-inventory-review`
Production safety: `PROD_SAFE` for docs, validators, tests, hygiene scans and
default no-ADB dry-runs; `PROD_CONDITIONAL` for optional inventory-only ADB
refresh after Phase A passes.

## Goal

Close the remaining pre-runtime approval metadata and policy gaps, then prepare
a public-safe device inventory owner-review package from existing sanitized
TASK-016C output when available.

TASK-005 runtime smoke remains blocked and `not_run`.

## Phase A - Final Hardening Gate

Phase A must pass before Phase B is eligible.

Required Phase A state:

- approval metadata validator uses typed local path families for APK, synthetic
  secret and evidence paths;
- synthetic QA user auth scope, forbidden account actions and raw-public flags
  are validated fail-closed;
- evidence retention is explicit and bounded when local redacted summaries are
  approved;
- cleanup/rollback policy validates separate approval, authorized-zone scopes
  and clean-state scope;
- `.gitignore` covers pytest/cache/coverage artifacts;
- full-tree hygiene scan catches trailing whitespace, blank EOF and missing
  final newline in tracked text files.

## Phase B - Public-Safe Owner Review Package

Phase B may run only after Phase A checks pass.

Allowed Phase B scope:

- read existing `.qa_local/devices/device_inventory.public_safe.generated.json`
  when present;
- optionally refresh inventory through the approved TASK-016 allowlist only if
  Phase A passes and a refresh is needed;
- export `docs/approvals/device_inventory.public_safe.review.json` only when
  the generated inventory has no public-safety findings and all runtime/app/APK
  statuses remain `not_run`;
- create `docs/approvals/task005_selected_target.template.json` with only
  allowed selected-target fields;
- create `docs/approvals/approval_metadata.task005.draft.json` as blocked draft
  metadata only.

Generated devices remain `classification_confidence: heuristic` and
`manual_review_required: true` until separate owner/QA manual review. The
review export is not approval for TASK-005.

## Out Of Scope

- APK install or app launch.
- `am start`, `monkey`, `logcat`, screenshots, videos or screenrecord.
- APK runtime smoke, WebView, WebRTC, stream/media playback, payment,
  subscription or purchase.
- Account/profile mutation.
- Raw ADB serial, IP, MAC, IMEI, Android ID, Google account, full fingerprint,
  raw phone, OTP, secrets, private endpoints or raw evidence in committed
  files.
- Decompile, patch, resign, TLS/pinning bypass or other security bypass.

## Acceptance Criteria

- All new residual false-pass cases from the TASK-015E/017 audit block.
- Targeted validator/inventory/hygiene tests pass.
- Full pytest, compileall, diff checks and full-tree hygiene scan pass.
- Approval metadata example remains `blocked` with
  `runtime_execution_status=not_run`.
- Default TASK-016 command remains `blocked`/`not_run` and does not call ADB.
- Phase B export, if executed, contains no raw local paths or raw identifiers.
- Exported devices remain heuristic/manual-review-required and not-run.
- TASK-005 remains blocked/not_run.

## Stop Conditions

Stop if requested work requires APK install, app launch, app runtime smoke,
`am start`, `monkey`, `logcat`, screenshots, videos, WebView, WebRTC, stream
playback, payment, account mutation, secrets, private endpoints, raw evidence
publication, production mutation, decompilation, patching, resigning, security
bypass, failing Phase A gate or R0/R1 reviewer concern.
