# TASK-025B runtime preflight checklist

Do not start TASK-025B until every item is confirmed:

| Check | Required value | Status before TASK-025B |
|---|---|---|
| Physical device available | `true` | deferred |
| Selected device connected and authorized | `yes` | deferred |
| Runtime lane aliases | refreshed/confirmed | deferred |
| APK local presence | target-specific APK under `.qa_local/apks/task-005/` | deferred |
| APK hash evidence | local-only SHA-256 recorded | deferred |
| Synthetic QA user env | `.qa_local/secrets/qa_user.env` exists | deferred |
| Raw phone/OTP printing | forbidden | deferred |
| Evidence capture approval | explicit | deferred |
| Evidence storage | ignored local storage | deferred |
| Cleanup policy | explicit | deferred |
| Payment/WebView/stream/profile/network boundaries | forbidden | deferred |

TASK-025B remains blocked until this checklist is refreshed in a fresh task
thread with current owner approval.

TASK-026A no-device tests require the corresponding report preflight object to
remain `preflight_status=deferred_no_device` with all runtime-enabling booleans
set to `false`. A future TASK-025B runtime pass must flip those booleans only
from fresh physical-device and owner-approval evidence, not from synthetic
contract tests.

TASK-026B adds ready-to-run future physical scenario contracts while preserving
the same no-device gate. Before any future TASK-025B runtime action, validate:

```text
python automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py --scenarios docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json --report docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json
```

Passing this command proves only that the scenario/report contract is internally
consistent. It is not physical-device evidence and does not approve runtime
execution.
