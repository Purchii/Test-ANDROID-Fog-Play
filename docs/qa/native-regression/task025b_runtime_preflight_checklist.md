# TASK-025B runtime preflight checklist

Status note: this checklist preserves the historical pre-runtime gate for
TASK-025B. It is superseded by the 2026-07-06 TASK-025B partial runtime report:
`docs/qa/reports/task025b_selected_lane_physical_runtime.summary.json`.
TASK-025B is no longer merely blocked-before-runtime; it ran and closed
`partial`, not pass.

Do not start TASK-025B until every item is confirmed:

| Check | Required value | Fresh 2026-07-06 TASK-025B status |
|---|---|---|
| Physical device available | `true` | confirmed: one authorized ADB target |
| Selected device connected and authorized | `yes` | confirmed: one authorized ADB target |
| Runtime lane aliases | refreshed/confirmed | confirmed from valid local approval metadata: `tv-tpv-013` / `tv-tpv-a12-013` |
| APK local presence | target-specific APK under `.qa_local/apks/task-005/` | blocked: directory has five APK candidates, but selected metadata path is missing |
| APK hash evidence | local-only SHA-256 recorded | blocked until selected APK is identified; value must not be printed |
| Synthetic QA user env | `.qa_local/secrets/qa_user.env` exists | confirmed existence-only; raw values not printed |
| Raw phone/OTP printing | forbidden | confirmed as forbidden for this TASK-025B scope |
| Evidence capture approval | explicit | owner authorized refreshed preflight/runtime in this thread; runtime still blocked by selected APK |
| Evidence storage | ignored local storage | `.qa_local/` ignored; task evidence path not used because runtime did not start |
| Cleanup policy | explicit | force-stop/relaunch cleanup remains planned but not used because runtime did not start |
| Payment/WebView/stream/profile/network boundaries | forbidden | confirmed as forbidden for this TASK-025B scope |

Historical checkpoint: TASK-025B was blocked at this moment until the ledger
above was confirmed in the fresh TASK-025B thread with current owner approval.

Fresh 2026-07-06 checkpoint: after explicit owner authorization, redaction-safe
preflight confirmed ADB availability, one authorized target, approval aliases,
ignored APK directory existence and synthetic QA env existence. Runtime remains
blocked because the selected APK path from valid approval metadata is missing
while five APK candidates exist under `.qa_local/apks/task-005/`. No APK hash,
install, app launch, screenshots, XML, logcat, secrets or raw runtime evidence
were produced.

An ignored local-only APK candidate index was generated under
`.qa_local/evidence/task-025b/preflight/` so the owner can select the approved
candidate without publishing filenames, paths or hashes.

TASK-026A no-device tests require the corresponding report preflight object to
remain `preflight_status=deferred_no_device` with all runtime-enabling booleans
set to `false`. A future TASK-025B runtime pass must flip those booleans only
from fresh physical-device and owner-approval evidence, not from synthetic
contract tests.

TASK-026B adds ready-to-run future physical scenario contracts while preserving
the same no-device gate. Before any future TASK-025B-like runtime action,
validate:

```text
python automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py --scenarios docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json --report docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json
```

Passing this command proves only that the scenario/report contract is internally
consistent. It is not physical-device evidence and does not approve runtime
execution. TASK-027 direct graph coverage must use its own preflight and
runtime-boundary approvals.
