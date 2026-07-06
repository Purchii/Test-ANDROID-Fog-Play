# TASK-025B selected-lane physical runtime report

Date: 2026-07-06

Mode: `NON_AUTONOMOUS`

Status: `partial`

This run executed a selected-lane physical Android TV runtime on the approved
public-safe lane aliases `tv-tpv-013` / `tv-tpv-a12-013` using the previously
installed/approved Television Full APK family. Raw APK paths, hashes, phone or
OTP values, device identifiers, screenshots, XML, logs and QR targets remain
local-only under ignored `.qa_local/` evidence storage.

## Result

TASK-025B was run, but it is not a full pass. The correct closure status is
`partial`.

Confirmed:

- physical device available and authorized;
- selected APK present and installed;
- local APK hash recorded local-only;
- synthetic QA env present without printing values;
- app launch after force-stop relaunch reached the post-auth catalog;
- catalog/rail focus, QR boundary classification, settings root category and
  Home/foreground persistence were sampled;
- external QR/browser targets were not opened;
- payment, stream/session start, Steam/account mutation, profile mutation,
  network/offline manipulation and APK modification were not performed.

Not fully confirmed:

- complete transition graph;
- complete data-source coverage;
- game detail server-list path for `NR-008`;
- Search typed no-results and Back recovery without trap;
- Settings Gamepad safe entry.

## Case Summary

| Case | Status | Public-safe note |
|---|---|---|
| `NR-001` | `pass` | Authorized post-auth catalog restored after cold relaunch. |
| `NR-002` | `pass` | Catalog root and side-rail focus sampled. |
| `NR-003` | `pass` | Catalog rail/grid focus sampled. |
| `NR-004` | `known_anomaly` | Search opened and TV keyboard was reachable, but Back/Escape recovery trapped until app relaunch. |
| `NR-005` | `blocked_by_boundary` | Attempted safe detail path reached a catalog banner QR boundary instead of game detail. |
| `NR-006` | `pass` | Settings root/promo-code category observed; recovery returned to catalog. |
| `NR-007` | `blocked_by_boundary` | Intended Gamepad path reached logout confirmation boundary; cancel/no was selected. |
| `NR-008` | `not_run` | Game detail server-list path was not reached before owner stop. |
| `NR-009` | `pass` | QR/account-mutation boundaries classified; no target/action followed. |
| `NR-010` | `pass` | Force-stop/relaunch and Home/foreground preserved catalog session state. |

## Anomalies

- `ANOM-025B-001`: first launch after ambient recovery stayed in an ambiguous
  loading state; force-stop cold relaunch restored normal catalog behavior.
- `ANOM-025B-002`: Search TV keyboard recovery trapped after Back/Escape until
  app recovery.
- `ANOM-025B-003`: Settings navigation intended for Gamepad reached logout
  confirmation boundary; cancel/no prevented account mutation.

## Boundary Ledger

- `BND-025B-001`: Steam/account-related QR boundary classified, not opened.
- `BND-025B-002`: support/external QR boundary classified, not opened.
- `BND-025B-003`: catalog banner QR boundary classified, not opened.
- `BND-025B-004`: logout/profile mutation boundary classified and cancelled.

## Artifacts

Public-safe summary JSON:
`docs/qa/reports/task025b_selected_lane_physical_runtime.summary.json`

Local-only raw evidence:
ignored `.qa_local/evidence/task-025b/`

The TASK-026B no-device scenario contract remains implementation readiness
input only and does not count as runtime evidence.
