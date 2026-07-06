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
runtime_evidence_ids=[]
task025b_preflight.preflight_status=deferred_no_device
```

All regression cases must be `not_run` or `blocked` with a reason while no
device is available. No-device reports must not contain runtime evidence IDs,
confirmed TASK-025B preflight fields or any claim that physical runtime is ready.

## Runtime pass requirements for future TASK-025B

A future pass report must be produced only by
`execution_mode=physical_selected_lane_runtime`, with a connected physical
device, confirmed runtime execution, passing install/launch statuses, non-empty
session persistence checkpoints and confirmed boundary evidence for
boundary-sensitive cases.

Future TASK-025B pass reports must also include:

- `task025b_runtime_status=ready_after_refreshed_approval`;
- `task025b_preflight.preflight_status=confirmed_for_task025b`;
- all TASK-025B preflight booleans confirmed as `true`;
- non-empty top-level `runtime_evidence_ids`;
- every passed regression case marked
  `execution_mode=physical_selected_lane_runtime` and
  `counts_as_runtime_evidence=true`;
- `NR-008` and `NR-009` linked to specific `boundary_ledger.boundary_id`
  entries;
- `boundary_guard_categories` matching the TASK-025 forbidden boundary
  category allowlist.

The validator rejects weak pass reports, including:

- pass with empty `session_persistence_checkpoints`;
- runtime pass while `physical_device_available=false`;
- `NR-008` or `NR-009` pass without confirmed boundary evidence;
- duplicate evidence IDs inside or across case/checkpoint/boundary ledgers;
- malformed known or new anomaly entries;
- `phase_c_runtime=pass` while runtime is `not_run` or `blocked`;
- runtime pass while TASK-025B preflight is missing, deferred, blocked or not
  fully confirmed;
- runtime pass with no top-level runtime evidence IDs;
- passed cases without physical runtime execution mode or runtime-evidence
  counting;
- boundary-sensitive cases linked only to unrelated boundary entries;
- boundary ledgers with unknown categories, followed navigation or performed
  external actions;
- exhaustive app navigation, payment, stream, WebView or compatibility claims;
- raw local paths, URLs, phone/OTP-like values, device identifiers, logs,
  screenshots, XML paths or raw artifact references.

## Synthetic contract tests

Synthetic/fake driver checks use
`execution_mode=no_device_synthetic_contract_test`. They may validate control
flow and boundary-guard contracts locally, but they must keep
`runtime_execution_status=not_run` and are never runtime evidence.

## TASK-026B runtime scenario contract

TASK-026B implements the future TASK-025B physical runtime tests as no-device
scenario contracts:

- `docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json`
  defines `NR-001` through `NR-010` with
  `future_runtime_gate=requires_confirmed_task025b_preflight`;
- `automation/native_regression/run_task026b_no_device_task025b_runtime_tests.py`
  emits a blocked/not-run/deferred report by default;
- `--synthetic-sequencing-test` uses an in-memory fake driver only and keeps
  `runtime_evidence_ids=[]`;
- `automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py`
  validates both the scenario contract and TASK-026B report section.

The `task025b_runtime_scenarios` report section must keep
`counts_as_runtime_evidence=false`, empty `runtime_evidence_ids`, case statuses
limited to `not_run` / `blocked` / `deferred`, case `evidence_status=unknown`
and the exact boundary guard allowlist. Synthetic executions may be `pass` only
as contract checks; they remain non-runtime evidence.

Scenario validation must enforce the ordered minimum action contract for each
`NR-001` through `NR-010` case, not only the presence of any allowed action.
Boundary-sensitive scenarios must declare public-safe
`expected_boundary_categories` and `expected_screen_state_categories`, and
`NR-008` / `NR-009` must include an explicit `classify_boundary` action rather
than only a public-safe evidence-reference placeholder.
Synthetic guarded-boundary coverage may confirm only fake driver handling of
the boundary category allowlist; it does not prove real payment, WebView,
stream, Steam/account, profile/account or network/offline behavior.
When synthetic sequencing status is `pass`, the synthetic execution ledger must
contain exactly one recognized execution for every required case ID with no
duplicates, and boundary-sensitive executions must record non-empty guarded
boundary categories.

## Public safety flags

The `public_safety.*_public` and `public_safety.*_invoked` booleans are
fail-closed leak/unsafe-action flags for the no-device/public report contract.
They must remain `false` in public reports. They are not a detailed future
physical-runtime action ledger. A future TASK-025B run that installs or launches
under refreshed approvals still needs separate approved runtime evidence,
preflight confirmation and evidence IDs; it must not flip these public-safety
flags to justify runtime behavior.
