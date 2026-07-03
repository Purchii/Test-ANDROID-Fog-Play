# TASK-025 report contract

## Schema versions

- Suite: `task025-native-regression-suite-v1`
- Summary: `task025-native-regression-summary-v1`

## No-device TASK-025A report

The committed template must remain blocked/not-run:

```text
run_status=blocked
runtime_execution_status=not_run
physical_device_available=false
physical_device_status=unavailable
apk_install_status=not_run
app_launch_status=not_run
task025b_runtime_status=deferred
```

All regression cases must be `not_run` or `blocked` with a reason while no
device is available.

## Runtime pass requirements for future TASK-025B

A future pass report must be produced only by
`execution_mode=physical_selected_lane_runtime`, with a connected physical
device, confirmed runtime execution, passing install/launch statuses, non-empty
session persistence checkpoints and confirmed boundary evidence for
boundary-sensitive cases.

The validator rejects weak pass reports, including:

- pass with empty `session_persistence_checkpoints`;
- runtime pass while `physical_device_available=false`;
- `NR-008` or `NR-009` pass without confirmed boundary evidence;
- duplicate evidence IDs inside or across case/checkpoint/boundary ledgers;
- malformed known or new anomaly entries;
- `phase_c_runtime=pass` while runtime is `not_run` or `blocked`;
- exhaustive app navigation, payment, stream, WebView or compatibility claims;
- raw local paths, URLs, phone/OTP-like values, device identifiers, logs,
  screenshots, XML paths or raw artifact references.

## Synthetic contract tests

Synthetic/fake driver checks use
`execution_mode=no_device_synthetic_contract_test`. They may validate control
flow and boundary-guard contracts locally, but they must keep
`runtime_execution_status=not_run` and are never runtime evidence.
