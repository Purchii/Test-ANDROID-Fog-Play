# TASK-025 selected-lane native regression model

## Purpose

TASK-025 prepares selected-lane native post-auth regression for the same public
lane used by TASK-005, TASK-019, TASK-020, TASK-021, TASK-022, TASK-023 and
TASK-024. TASK-025A is no-device readiness only. TASK-025B is the future
physical runtime run.

TASK-025 physical-device runtime execution is deferred because no physical
Android TV/STB device is currently available. TASK-025A is limited to no-device
automation readiness, schema/report hardening and fake/synthetic tests.
TASK-025B will execute selected-lane physical runtime only after a device is
available and owner approvals are refreshed.

## Future selected lane

```json
{
  "device_alias": "tv-tpv-013",
  "runtime_profile_alias": "tv-tpv-a12-013",
  "build_alias": "task-005-local-apk-001",
  "synthetic_user_alias": "qa-user-phone-001"
}
```

## Oracles

- post-auth root reachable and focused;
- D-pad focus movement remains valid;
- Search visible-keyboard path, no-results state and recovery;
- Back recovery from game detail, Settings, promo and boundary-adjacent
  surfaces;
- Home/foreground session persistence;
- force-stop/relaunch session persistence;
- boundary surfaces classified but not entered.

## Boundary guards

TASK-025 must classify and stop before these categories:

- payment/subscription/purchase;
- WebView/browser/external QR traversal;
- stream/WebRTC/media playback/game session start;
- Steam/account connection;
- profile/account mutation;
- network/offline manipulation.

## TASK-025A status

TASK-025A does not run ADB, install APKs, launch the app, execute UIAutomator,
collect logcat/screenshots/videos, read secrets or capture raw runtime
evidence. Fake/synthetic contract tests are not runtime evidence and cannot
make a runtime pass report valid.

## TASK-026A readiness hardening

TASK-026A adds XL+ no-device coverage for the TASK-025B report contract. The
coverage is local-only and validates that future physical pass reports require
confirmed TASK-025B preflight, non-empty runtime evidence IDs, physical runtime
execution mode/counting on passed cases, specific boundary-ledger links for
`NR-008`/`NR-009` and the full forbidden boundary guard list.

These tests do not prove physical-device availability, APK presence, app
launch, install/update, account/session state, boundary behavior or product
runtime behavior.
