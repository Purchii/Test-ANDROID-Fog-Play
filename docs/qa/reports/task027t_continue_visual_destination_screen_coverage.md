# TASK-027T continue visual destination screen coverage

Mode: `NON_AUTONOMOUS`

Public-safe machine-readable report:
`docs/qa/reports/task027t_continue_visual_destination_screen_coverage.summary.json`

## Result

TASK-027T reviewed the existing selected-lane approval, restored the same local
selected-lane material from the same-machine owner checkout, and executed
bounded physical Android TV runtime coverage. Raw APK, screenshot, XML, log,
QR target and account-like values remain local-only under ignored evidence
storage.

The report records `covered` for the three TASK-027T target destinations:
session journal, Steam/top-up QR and feedback QR. Coverage is visual
destination-screen coverage only; it does not mean populated session history,
external QR traversal, payment, stream/session start or account mutation.

TASK-027R remains terminal ledger context only. TASK-027S remains launcher entry
and app-shell-loader context only. Neither predecessor report is TASK-027T
visual destination proof.

## Destination Ledger

| Destination | TASK-027T status | Evidence status | Visual proof |
|---|---|---|---|
| Session journal | `covered` | `confirmed` | `true` |
| Steam/top-up QR | `covered` | `confirmed` | `true` |
| Feedback QR | `covered` | `confirmed` | `true` |

Key public-safe checkpoint IDs:

- session journal: `rt027t-cp011-after-grid-dpad-left`;
- Steam/top-up QR: `rt027t-cp013-steam-topup-qr-after-center`;
- feedback QR: `rt027t-cp015-feedback-qr-after-center`.

Both QR destinations were decoded local-only as HTTPS-category targets and were
not followed or opened externally.

## Fail-Closed Rules

The TASK-027T validator rejects destination overclaims unless a future update
adds fresh TASK-027T evidence and keeps the public-safety boundary intact.

Required future invariants:

- `covered` destination rows must have `visual_destination_proof=true`,
  `runtime_evidence_collected=true`, `evidence_status=confirmed` and at least
  one `rt027t-cp...` evidence ID;
- QR destination rows must keep `qr_navigation_followed=false`;
- `app_shell_loader_after_launcher_entry` must not be counted as catalog or
  destination coverage;
- prior TASK-027R or TASK-027S evidence must not count as TASK-027T visual
  proof;
- public reports must not expose raw screenshots, XML, logs, QR targets,
  device identifiers, APK details, private runtime metadata or local paths.

The validator also requires a `missing_local_selected_lane_material` preflight
blocker when this report uses the blocked status, and it rejects runtime
executed claims while `runtime_execution_status` is `blocked`.

After QA review, the validator also rejects top-level `covered` or mismatched
runtime statuses unless every required destination row has fresh `rt027t-*`
visual evidence and matching coverage claims.

## Boundaries

No payment, paid session, stream/WebRTC/media playback, external QR/browser
traversal, Steam/account connection mutation, profile/account mutation,
network/offline manipulation, captcha solving/bypass, APK modification or
security bypass was performed.

## Anomalies

- `ANOM-027T-001`: first launch checkpoint hit external Android TV ambient /
  screensaver surface and was recovered by explicit app launch.
- `ANOM-027T-002`: unsafe screenshot redirection/helper naming caused local
  capture tooling issues; binary-safe recapture was used before evidence was
  counted.
- `ANOM-027T-003`: direct D-pad rail attempts from loaded catalog stayed on the
  catalog and were not counted as destination coverage.
- `ANOM-027T-004`: XML exposed rail label bounds, but direct tap remained on
  catalog; the successful oracle was grid focus plus lateral rail recovery.

## Unverified Areas

- recovery from `app_shell_loader_after_launcher_entry`;
- root cause of rail no-op before grid-focus oracle;
- complete dynamic game/server value inventory.
