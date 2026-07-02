# TASK-005 APK Bundle Contract

Status: `owner_confirmed_input_contract`

Evidence status: `confirmed` from owner message on 2026-07-01 for expected
bundle shape and device mapping. APK file arrival is still `pending`.

Production safety classification: `PROD_SAFE_DOCUMENTATION_ONLY`.

This document records the expected local-only APK package for future test runs.
It does not approve APK install, app launch, runtime smoke, ADB refresh,
logcat, screenshots, videos, WebView, WebRTC, payment, network/offline flows or
production interaction.

## Local Bundle Directory

The owner-confirmed local bundle directory is:

```text
.qa_local/apks/task-005/
```

The repository must not commit APK files, raw hashes or machine-specific
absolute paths. The local Windows path provided by the owner maps to this
repo-relative ignored directory.

## Expected APK Files Per Test Run

Each test run is expected to receive the same package shape for now:

| APK file | Intended targets | Evidence status |
|---|---|---|
| `fogplay-tv-television-steam-production-release.apk` | YandexTV | confirmed_owner_mapping |
| `fogplay-tv-television-sber-production-release.apk` | SberBox 1, SberBox 2, SberTV | confirmed_owner_mapping |
| `fogplay-tv-phone-full-production-release.apk` | phones | confirmed_owner_mapping |
| `fogplay-tv-aosp-full-production-release.apk` | FogPlay Stick; future Fog Play Box is out of current audit | confirmed_owner_mapping |
| `fogplay-tv-television-full-production-release.apk` | Philips old, Philips new | confirmed_owner_mapping |

## Approval Boundary

- APK files are local-only and ignored by default.
- APK arrival, local hash recording and target-specific build selection remain
  future owner/QA inputs.
- TASK-005 remains blocked until real approval metadata validates and a separate
  limited runtime smoke task is opened.
- Current approval metadata validation still fails closed and does not run or
  inspect APKs.
