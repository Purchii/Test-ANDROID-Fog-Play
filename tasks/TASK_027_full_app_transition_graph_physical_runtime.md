# TASK-027 - Full app transition graph physical runtime coverage

## Mode

`NON_AUTONOMOUS`

## Production safety classification

Tracked docs, validators, templates and public-safe scans are `PROD_SAFE`.

Physical Android TV runtime is `PROD_CONDITIONAL` and may start only after the
TASK-027-specific preflight ledger is confirmed. Runtime must stop or classify
before payment, WebView/browser/external QR traversal, stream/session start,
Steam/account connection, profile/account mutation, network/offline
manipulation, APK modification or security bypass.

## Objective

Build and execute a public-safe, evidence-first physical runtime task that
closes the full reachable approved transition graph of the app on the same
selected lane used by TASK-025B.

TASK-025B is a partial baseline, not a pass and not graph closure proof. TASK-027
must use a directed transition ledger showing every currently reachable approved
node/branch as `covered`, `blocked_by_boundary`, `blocked_by_tooling`,
`blocked_by_external_state` or `not_run_out_of_scope`, with evidence IDs when
runtime evidence exists.

## Required baseline inputs

- `docs/qa/reports/task025b_selected_lane_physical_runtime.summary.json`
- `docs/qa/reports/task025b_selected_lane_physical_runtime.md`
- `docs/qa/reports/task020_full_screen_inventory.summary.json`
- `docs/qa/reports/task023_full_data_screen_inventory.summary.json`
- TASK-026B no-device contracts as readiness checks only, not runtime evidence.

## Preflight gate

Before any ADB/APK/app action, confirm and record:

- physical Android TV/STB availability and authorization;
- selected public-safe device aliases and runtime profile alias;
- selected APK presence under ignored local TASK-005 APK storage;
- APK hash recorded local-only without printing or committing the value;
- synthetic QA env existence without printing raw values;
- evidence capture approval and ignored local evidence storage;
- cleanup/rollback policy limited to safe Back, Home, cancel, close and
  force-stop plus relaunch recovery;
- QA Reviewer A, QA Reviewer B and Security/Prod-safety approval.

If any gate is missing, runtime status is `blocked`, not partial or pass.

## Dynamic data rule

Game catalog and server-list contents can change over time. TASK-027 must not
assert fixed titles, server row counts, server aliases, prices, hardware rows,
ping values or complete row enumeration. It may assert categories, structure,
focus movement, scroll/lazy-load behavior, boundary handling and redaction.

## Known TASK-025B anomalies to recheck or carry explicitly

- `ANOM-025B-001`: ambiguous first launch after ambient recovery; cold relaunch
  recovered catalog.
- `ANOM-025B-002`: Search TV keyboard Back/Escape recovery trap.
- `ANOM-025B-003`: Settings navigation intended for Gamepad reached logout
  confirmation; cancel/no prevented mutation.

## Verification baseline

```text
git status --short --branch
git diff --check
python automation/native_regression/validate_task027_transition_graph_report.py --report docs/qa/reports/task027_full_app_transition_graph_physical_runtime.summary.json
python -m pytest -q tests/test_task027_transition_graph_validator.py
python automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py --scenarios docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json --report docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json
python -m pytest -q tests/test_task025_native_regression.py tests/test_task025_native_regression_validator.py tests/test_task026a_no_device_readiness_coverage.py tests/test_task026b_no_device_task025b_physical_runtime_tests.py tests/test_task027_transition_graph_validator.py
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

Runtime/device checks are allowed only after the preflight gate is confirmed.
