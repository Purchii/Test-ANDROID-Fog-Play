# TASK-025B physical runtime handoff

TASK-025B is deferred until a physical Android TV/STB target is available and
owner approvals are refreshed. This file is a handoff stub, not approval to run
runtime now.

## Required owner/QA confirmations

- `physical_device_available=true`;
- selected device is connected and authorized;
- selected aliases are `tv-tpv-013` / `tv-tpv-a12-013` or a refreshed
  manual-confirmed replacement;
- APK is present locally under `.qa_local/apks/task-005/app-under-test.apk`;
- build alias is `task-005-local-apk-001` or a refreshed
  `task-005-local-apk-NNN`;
- local SHA-256 is recorded without publishing the value;
- `.qa_local/secrets/qa_user.env` exists and raw phone/OTP values are not
  printed;
- evidence capture approval is explicit;
- cleanup policy is explicit;
- payment, WebView, stream, profile/account mutation and network/offline
  boundaries remain forbidden unless a later task separately approves them.

## Required execution cases

TASK-025B should execute `NR-001` through `NR-010` from the TASK-025 suite and
publish only public-safe aliases, statuses, categories and evidence IDs.
