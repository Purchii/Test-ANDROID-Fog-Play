# TASK-015D/016C - Approval hardening and gated ADB inventory

Mode: `NON_AUTONOMOUS`
Branch: `qa/task-015d-016c-approval-hardening-adb-inventory`
Production safety: `PROD_SAFE` for docs, validator hardening, tests and default
dry-runs; `PROD_CONDITIONAL` for owner-approved Phase B inventory-only ADB
after the Phase A hard gate passes.

## Goal

Harden the TASK-005 approval boundary before any further local ADB inventory
work. This task is split into two phases with a hard gate between them.

## Phase A - Approval Hardening Gate

Phase A must pass before Phase B is eligible.

Required Phase A state:

- approval validator and docs enforce the latest TASK-005 runtime approval
  blockers;
- generated inventory targets remain heuristic and manual-review-required;
- TASK-005 remains blocked until approved build/APK, Android TV/STB target,
  runtime config, fixtures, redaction, storage, cleanup and reviewer approvals
  are confirmed;
- all relevant local docs/tests/checks pass or are recorded as blocked.

## Phase B - Inventory-Only ADB

Phase B may run only after Phase A passes and owner approval is present.

Allowed Phase B scope:

- inventory-only ADB collection through the approved TASK-016C allowlist;
- local raw output under ignored `.qa_local/devices/`;
- generated public-safe inventory that remains
  `classification_confidence: heuristic` and
  `manual_review_required: true`;
- no promotion of generated inventory into TASK-005 approval metadata until
  separate owner/QA manual review marks selected targets `manual_confirmed` and
  `manual_review_required: false`.

## Out Of Scope

- APK install or app launch.
- `am start`, `monkey`, `logcat`, screenshots, videos or screenrecord.
- WebView, WebRTC, stream/media playback, payment, subscription or purchase.
- Account/profile mutation.
- Private endpoint, route, deeplink, token, cookie, credential or raw device
  identifier collection for public docs.
- Decompile, patch, resign, TLS/pinning bypass or other security bypass.

## Acceptance Criteria

- Source-of-truth docs describe the two-phase hard gate.
- Phase B is documented as blocked until Phase A passes.
- Approval validator blocks missing/unsafe synthetic QA user local secret and
  repository template paths.
- Approval validator blocks IP-like values anywhere in approval metadata.
- Approval validator blocks unknown fields in `approved_targets.devices[*]`.
- Approval validator blocks unsafe compound build alias tokens and duplicate
  public approval list values.
- TASK-016C validates output paths under `.qa_local/devices/` before any ADB
  invocation.
- Generated inventory is documented as heuristic/manual-review-required.
- TASK-005 remains blocked and is not converted to runtime-ready status.
- Public docs contain no raw identifiers, private endpoints, secrets, APK paths
  outside ignored local patterns or executable runtime recipes beyond the
  approved inventory allowlist.

## Verification

Required docs-slice verification:

```text
git status --short --branch
git diff --check
Markdown/source-of-truth diff review
No ADB/runtime commands
```

Runtime/device verification is explicitly not run in this docs slice.

## Stop Conditions

Stop if requested work requires APK install, app launch, app runtime smoke,
`am start`, `monkey`, `logcat`, screenshots, videos, WebView, WebRTC, stream
playback, payment, account mutation, secrets, private endpoints, raw evidence
publication, production mutation, decompilation, patching, resigning or
security bypass.
