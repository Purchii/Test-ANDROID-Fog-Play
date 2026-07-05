# TASK-025B Codex prompt stub

Use this stub only after a physical device is available and approvals are
refreshed. Do not use it to run TASK-025A.

```text
Task: TASK-025B - Selected-lane physical native regression runtime
Mode: NON_AUTONOMOUS unless owner explicitly authorizes bounded runtime.

Read source-of-truth docs first. Confirm physical_device_available=true,
selected device authorized, selected APK present locally, local SHA-256
recorded, synthetic QA user env present, evidence capture approval explicit and
cleanup policy explicit.

Before any runtime action, confirm TASK-026A no-device readiness artifacts still
validate and that the TASK-025B report preflight can be supported by fresh
physical-device evidence and refreshed owner approvals. Do not treat synthetic
contract tests or no-device pytest results as runtime evidence.

Run only the TASK-025 selected-lane native regression cases NR-001 through
NR-010. Stop before payment, WebView/browser/external QR traversal,
stream/WebRTC/media playback/game session start, Steam/account connection,
profile/account mutation and network/offline manipulation. Public reports must
omit raw phone/OTP, raw device identifiers, raw APK hashes, raw screenshots,
raw logs, raw XML, QR targets, URLs and private route/endpoint values.
```
