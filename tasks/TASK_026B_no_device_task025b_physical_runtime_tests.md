# TASK-026B - No-device implementation of TASK-025B physical runtime tests

## Mode

`BOUNDED_AUTONOMOUS`

## Production safety classification

`PROD_SAFE` only for tracked source, docs, schemas, validators and
synthetic/fake tests.

## Objective

Implement the TASK-025B physical runtime test scenarios now, but keep all
runtime execution deferred until a later physical-device task confirms device
availability and refreshed owner approvals.

TASK-026B is implementation readiness only. It does not execute Android TV
runtime, ADB, APK, app launch, logcat, screenshots, XML/video capture, payment,
WebView, stream, profile/account or network/offline flows.

## Deliverables

- `docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json`
  defines future TASK-025B scenarios `NR-001` through `NR-010`.
- `automation/native_regression/run_task026b_no_device_task025b_runtime_tests.py`
  generates blocked/not-run reports by default and can run only in-memory
  synthetic sequencing.
- `automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py`
  validates the scenario/report contract.
- `docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json`
  is the public-safe blocked/not-run template report.
- `tests/test_task026b_no_device_task025b_physical_runtime_tests.py` proves the
  default no-device behavior, fake-driver sequencing, boundary guards, report
  validation and absence of process/shell imports.

## Acceptance

- Default execution returns `run_status=blocked`,
  `runtime_execution_status=not_run`, `physical_device_status=unavailable`,
  `apk_install_status=not_run`, `app_launch_status=not_run`,
  `task025b_runtime_status=deferred`, empty `runtime_evidence_ids` and
  `task025b_preflight.preflight_status=deferred_no_device`.
- Every future scenario remains `not_run`, `blocked` or `deferred` without a
  physical TASK-025B run.
- Synthetic sequencing uses `execution_mode=no_device_synthetic_contract_test`,
  keeps `counts_as_runtime_evidence=false` and keeps runtime evidence IDs empty.
- Boundary-sensitive cases classify payment/WebView/stream/profile/network
  boundaries only; they must not open, follow, enter, pay, stream, mutate
  profile/account state or manipulate network state.
- Public reports reject raw values, local evidence paths, QR targets, phone/OTP
  values, device identifiers, artifact references and overbroad coverage
  claims.

## Verification plan

```text
git status --short --branch
git diff --check
python -m pytest -q tests/test_task025_native_regression.py tests/test_task025_native_regression_validator.py tests/test_task026a_no_device_readiness_coverage.py tests/test_task026b_no_device_task025b_physical_runtime_tests.py
python automation/native_regression/run_task026b_no_device_task025b_runtime_tests.py
python automation/native_regression/run_task026b_no_device_task025b_runtime_tests.py --synthetic-sequencing-test
python automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py --scenarios docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json --report docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json
pytest -q
python -m pytest -q
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

All commands are local/public-safe and must not connect to devices, run APKs,
inspect ignored local evidence or contact production systems.
