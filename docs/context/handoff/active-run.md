# Active run

## Run Metadata

Mode: `NON_AUTONOMOUS`
Thread title: `TASK-027 — Full app transition graph physical runtime coverage`
Thread status: `inactive_preparation_completed_runtime_handoff_created`
Fresh thread verified: `yes`
Task ID: `TASK-027`
Task branch: `qa/task-027-full-app-transition-graph-physical-runtime`
Default branch: `main`
Base commit: `f9f58fb`
Merge/push authority: `NON_AUTONOMOUS; do not merge or push default branch without explicit owner command`
Production safety classification: tracked docs/source, validators, templates
and local public-safe scans are `PROD_SAFE`; physical Android TV runtime,
ADB/APK/app launch, screenshot/XML/log/video capture and local QR decode are
`PROD_CONDITIONAL` and remain blocked until the TASK-027-specific preflight
ledger is confirmed.

## Goal

Build and execute a public-safe, evidence-first physical Android TV runtime
task covering the full reachable approved transition graph on the same selected
lane used by TASK-025B.

TASK-025B is a partial baseline only. It does not count as a full graph pass or
as complete transition coverage for TASK-027.

## Current Status

The fresh TASK-027 thread has been renamed and the task branch has been created
from the detected default branch `main`. Source-of-truth docs and TASK-025B,
TASK-020 and TASK-023 public reports have been read.

Strict real multi-agent workflow is active:

- Orchestrator: current thread;
- Planner: completed TASK-027 scope, ledger and verification plan;
- Builder: completed public-safe report/validator recommendations;
- QA Reviewer A: blocked acceptance until a real TASK-027 acceptance artifact
  and graph closure ledger exist;
- QA Reviewer B: blocked full graph closure until fresh runtime closure ledger,
  screenshot+XML checkpoints and guarded boundaries exist;
- Security/Prod-safety Reviewer: `APPROVED_WITH_CONDITIONS` for bounded
  static/preflight work and conditional physical runtime after gates;
- Docs/Scribe: proposed TASK-027 source-of-truth/report updates.

Public-safe TASK-027 contract artifacts now exist:

- `tasks/TASK_027_full_app_transition_graph_physical_runtime.md`;
- `docs/qa/reports/task027_full_app_transition_graph_physical_runtime.summary.json`;
- `docs/qa/reports/task027_full_app_transition_graph_physical_runtime.md`;
- `automation/native_regression/validate_task027_transition_graph_report.py`;
- `tests/test_task027_transition_graph_validator.py`.

## Preflight Gate

Redaction-safe physical preflight is confirmed in this TASK-027 run:

- physical Android TV/STB target connected and authorized: `confirmed`;
- selected public-safe device aliases and runtime profile alias refreshed:
  `confirmed`;
- selected APK present under ignored local TASK-005 APK storage: `confirmed`;
- APK SHA-256 recorded local-only without printing or committing the value:
  `confirmed`;
- synthetic QA user env exists without printing raw values: `confirmed`;
- ignored local evidence storage and redaction policy approved: `confirmed`;
- cleanup/recovery policy limited to Back, Home, cancel, close and force-stop or
  explicit relaunch: `confirmed`;
- QA Reviewer A, QA Reviewer B and Security/Prod-safety approval for
  preflight-only: `confirmed`.

No APK install, app launch, logcat, screenshot/XML/video capture, QR decode,
navigation, WebView, payment, stream, account/profile mutation or
network/offline action was performed in preflight.

Physical app runtime remains `blocked` in this preparation thread. The owner
requested direct graph coverage in a separate thread after preparation, so a
fresh runtime execution thread was created:
`019f3678-274c-7c72-98a9-a35ffd79b9d2`
(`TASK-027R — Full app transition graph physical runtime execution`).

That runtime thread must request and record QA Reviewer A, QA Reviewer B and
Security/Prod-safety approval for the post-preflight runtime boundary before
APK install, app launch, navigation, screenshot/XML/log/video capture or QR
decode.

## Runtime Closure Requirements

Full graph closure requires a directed transition ledger where every currently
reachable approved node/branch is terminally classified as:

- `covered`;
- `blocked_by_boundary`;
- `blocked_by_tooling`;
- `blocked_by_external_state`;
- `not_run_out_of_scope`.

Every runtime checkpoint must include screenshot/visual inspection and XML when
available. XML-vs-visual mismatches are first-class tooling gaps. Recurrent
screens and anomalies must be recorded immediately.

## Dynamic Data Rule

Game catalog and server-list contents may change over time. TASK-027 must
assert screen categories, field models, focus/scroll behavior, transition
outcomes, redaction and boundaries. It must not assert fixed game titles,
server counts, server aliases, prices, hardware rows, ping values or complete
row enumeration.

## Boundaries

Forbidden unless a later separate task approves:

- real payment completion or paid session start;
- external QR/WebView/browser traversal;
- stream/WebRTC/media playback/game session start;
- Steam/account connection mutation;
- profile/account mutation, including logout confirmation acceptance;
- network/offline manipulation;
- APK patch/decompile/resign or security bypass;
- printing or committing raw APK hashes, phone/OTP values, device identifiers,
  QR targets, endpoints, screenshots, XML, logs, videos or private values.

## Known TASK-025B Anomalies

TASK-027 must recheck or explicitly carry with reasons:

- `ANOM-025B-001`: ambiguous first launch after ambient recovery; cold relaunch
  restored catalog.
- `ANOM-025B-002`: Search TV keyboard Back/Escape recovery trap.
- `ANOM-025B-003`: Settings navigation intended for Gamepad reached logout
  confirmation and was cancelled.

## Verification Plan

Minimum tracked checks:

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

Runtime/device checks are allowed only after the preflight gate above is
confirmed and after the fresh runtime execution thread records post-preflight
runtime-boundary approval.

## Thread Handoff

Preparation result: `complete`.

Next thread created: `yes`.

Next thread ID: `019f3678-274c-7c72-98a9-a35ffd79b9d2`.

Next thread title: `TASK-027R — Full app transition graph physical runtime execution`.

Next thread branch: continue from `qa/task-027-full-app-transition-graph-physical-runtime`.

Next thread starting commit: `df7b97c` plus this handoff update.

## Stop Conditions

Stop and report a precise blocker if:

- physical device, APK, auth env, evidence storage, cleanup or reviewer
  approval is missing;
- runtime navigation reaches a forbidden boundary that cannot be safely
  classified/recovered;
- screenshot/XML capture cannot support checkpoint evidence;
- Search/Settings/focus trap prevents safe continuation and approved recovery
  does not restore an actionable app state;
- public-safe scans detect raw values or local-only artifacts.
