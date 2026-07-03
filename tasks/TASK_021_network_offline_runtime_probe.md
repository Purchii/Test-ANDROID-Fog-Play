# TASK-021 - Network/offline runtime probe

## Mode

`NON_AUTONOMOUS`

## Branch

```text
qa/task-021-network-offline-runtime-check
```

## Runtime Lane

- `device_alias`: `tv-tpv-013`
- `runtime_profile_alias`: `tv-tpv-a12-013`
- `build_alias`: `task-005-local-apk-001`
- `synthetic_user_alias`: `qa-user-phone-001`

## Production Safety

- `PROD_SAFE`: docs, public-safe JSON validation and report review.
- `PROD_CONDITIONAL`: bounded selected-lane offline-like runtime checks with
  cleanup/recovery and local-only raw evidence.
- `PROD_FORBIDDEN`: packet capture, proxying, TLS/security bypass, private
  endpoint extraction, payment/WebView/stream/account mutation, APK
  modification and raw evidence publication.

## Result

TASK-021 confirmed a reversible DNS offline-like app data point on the approved
lane:

- offline error screen under reversible DNS offline-like condition:
  `confirmed`;
- focused `DPAD_CENTER` on the refresh action after network restoration:
  `confirmed`;
- internet-check loader before recovery route:
  `confirmed`;
- unauthenticated recovery to phone input:
  `confirmed`;
- authenticated/onboarding-incomplete recovery to first onboarding screen:
  `confirmed`;
- authenticated/onboarding-complete recovery to games catalog:
  `confirmed`;
- true Wi-Fi-off product verdict:
  `unknown` because the Wi-Fi-off probe hit an external TV ambient/screensaver
  surface while ADB connectivity was interrupted.

Public summary:

```text
docs/qa/reports/task021_network_offline_probe.summary.json
```

Raw network/auth/device values, screenshots and videos remain local-only under
ignored TASK-021 evidence storage.

## Not Run

TASK-021 did not perform packet capture, proxying, TLS bypass, private endpoint
extraction, payment, WebView/browser traversal, stream/WebRTC/media playback,
account/profile mutation or compatibility coverage.

## Verification

Recorded verification included JSON sanity, hygiene scan, `git diff --check`,
runtime checkpoint review, network cleanup/recovery review and multi-agent
review. The durable automation lesson is that focused `DPAD_CENTER` on Refresh
is the confirmed activation path; touch-tap refresh was ambiguous, and the
loader may require screenshot/video evidence rather than delayed XML only.
