# TASK-025B physical runtime handoff

TASK-025B is deferred until a physical Android TV/STB target is available and
owner approvals are refreshed. This file is a handoff stub, not approval to run
runtime now.

## Required owner/QA confirmations

- `physical_device_available=true`;
- selected device is connected and authorized;
- selected aliases are `tv-tpv-013` / `tv-tpv-a12-013` or a refreshed
  manual-confirmed replacement;
- APK is present locally as the owner-selected target-specific APK under
  `.qa_local/apks/task-005/`;
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

TASK-026B adds the no-device implementation contract for those physical
runtime tests:

- scenario source:
  `docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json`;
- no-device runner:
  `automation/native_regression/run_task026b_no_device_task025b_runtime_tests.py`;
- contract validator:
  `automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py`;
- blocked/not-run template:
  `docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json`.

These artifacts implement sequencing and report contracts only. They do not
confirm device availability, APK presence, app launch, installation, account
state, boundary behavior or runtime product behavior.

## TASK-026A no-device readiness note

TASK-026A strengthens local no-device contract coverage for this handoff. Those
tests confirm only public-safe runner/validator/schema behavior. They do not
confirm device availability, APK presence, app launch, installation, account
state, real boundary behavior or runtime product behavior.

## TASK-026B no-device implementation note

TASK-026B implements the future TASK-025B physical runtime scenarios behind
explicit gates. Default execution remains blocked/not-run/deferred, and
synthetic sequencing uses only an in-memory fake driver with empty runtime
evidence IDs. A future physical TASK-025B task must rerun the validator and then
execute scenarios only after refreshed owner approvals and physical device
preflight are confirmed.
