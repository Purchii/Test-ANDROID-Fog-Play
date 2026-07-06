# Active run

## Run Metadata

Mode: `NON_AUTONOMOUS`
Thread title: `TASK-027R — Full app transition graph physical runtime execution`
Thread status: `partial_runtime_closed_for_current_thread`
Fresh thread verified: `yes`
Task ID: `TASK-027`
Task branch: `qa/task-027-full-app-transition-graph-physical-runtime`
Default branch: `main`
Base commit: `f9f58fb`
Merge/push authority: `NON_AUTONOMOUS; owner explicitly requested safe current-thread closure, push to detected default branch, and continuation in a new thread`
Production safety classification: tracked docs/source, validators, templates
and local public-safe scans are `PROD_SAFE`; physical Android TV runtime,
ADB/APK/app launch, screenshot/XML/log/video capture and local QR decode are
`PROD_CONDITIONAL` and are open only inside the post-preflight TASK-027R
runtime boundary approval.

## Goal

Build and execute a public-safe, evidence-first physical Android TV runtime
task covering the full reachable approved transition graph on the same selected
lane used by TASK-025B.

TASK-025B is a partial baseline only. It does not count as a full graph pass or
as complete transition coverage for TASK-027. The current TASK-027R thread is
being closed as a partial runtime checkpoint by owner command; full graph
closure remains the continuation objective.

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

Physical app runtime is now unblocked for this fresh TASK-027R thread only
after post-preflight runtime-boundary review. QA Reviewer A, QA Reviewer B and
Security/Prod-safety Reviewer returned `APPROVED_WITH_CONDITIONS` in thread
`019f3678-274c-7c72-98a9-a35ffd79b9d2`.

The approval opens only the selected-lane `PROD_CONDITIONAL` runtime boundary:
APK install/update, app launch/relaunch, safe D-pad/navigation coverage,
screenshot/visual checkpoints, XML where available, bounded crash/ANR/log
evidence, optional video evidence and local-only QR decode. It is not an
acceptance result and not a full graph pass.

Before and during runtime, every checkpoint must keep raw artifacts under
ignored local evidence storage, must publish only evidence IDs/category-level
metadata, and must stop at payment, stream/session, WebView/browser/external
QR traversal, Steam/account connection, profile/account mutation, network
manipulation, captcha solving/bypass, APK modification or security bypass.

## Runtime Evidence Checkpoints

Local-only TASK-027R runtime evidence is stored under ignored evidence storage.
Public reports may reference only checkpoint IDs, not raw screenshots, XML,
logs, APK names/hashes, QR targets, device identifiers or account-like values.

Confirmed public-safe checkpoint families so far:

- `rt027-cp001c`, `rt027-cp036`: external TV ambient/screensaver recurrence,
  not an app screen.
- `rt027-cp002` through `rt027-cp006`, `rt027-cp037` through `rt027-cp043`:
  app loader and loader-after-recovery states.
- `rt027-cp006` through `rt027-cp010`: post-auth catalog, rail focus movement
  and dynamic catalog scroll sampling.
- `rt027-cp011` through `rt027-cp015`: game detail and dynamic server-list
  sampling without session/payment activation.
- `rt027-cp016` through `rt027-cp021`: Search keyboard, input/recovery trap and
  safe force-stop/relaunch recovery.
- `rt027-cp022` through `rt027-cp028`: Settings root, Gamepad safe-entry,
  Gamepad close recovery, Home and foreground persistence.
- `rt027-cp029` through `rt027-cp035`: promo-code screen recurrence with TV
  keyboard and failed intended rail-branch switching.

Bounded crash evidence was captured local-only after the loader recurrence:
the app process was present and the crash buffer was captured without crash
buffer content.

## Runtime Anomalies Recorded In TASK-027R

Record every anomaly immediately. This is a global project rule, not a
session-local preference: do not defer anomaly records until the end, even for
tooling issues or branches planned for later revisit. Current TASK-027R
anomalies:

- `ANOM-025B-001` rechecked: launch and ambient-recovery flows can remain in
  prolonged app loader states; one earlier force-stop/relaunch recovered the
  catalog, but a later ambient recovery returned to the loader and did not
  reach actionable catalog within bounded waits.
- `ANOM-025B-002` rechecked: Search keyboard accepted the route but raw ADB
  text input had no visible effect, and Back/Escape did not recover; recovery
  required force-stop/relaunch.
- `ANOM-025B-003` rechecked: precise safe Gamepad entry opened the Gamepad
  setup screen and close returned to Settings root, without logout/profile
  mutation.
- `ANOM-027R-001`: initial screenshot capture path corrupted a PNG when binary
  output was redirected through an unsafe shell path; capture was corrected via
  a binary-safe process stream.
- `ANOM-027R-002`: banner QR crop was partial/cut off; fullscreen local-only
  decode attempt did not decode, so recurring QR classification must reference
  prior local-only decode artifacts where applicable and keep this TASK-027R
  QR attempt as a tooling anomaly until revisited.
- `ANOM-027R-003`: Back from game detail/server-list sampling did not recover;
  D-pad Left recovered to the rail while retaining detail/server-list context.
- `ANOM-027R-004`: promo-code screen with TV keyboard trapped multiple intended
  rail-boundary taps; checkpoints stayed on the promo-code screen rather than
  opening feedback, Steam/top-up or journal branches.
- `ANOM-027R-005`: after force-stop/relaunch from the promo-code trap, the TV
  ambient/screensaver surface recurred, then foreground recovery entered a
  prolonged app loader that blocked further safe rail traversal in the current
  session.
- `ANOM-027R-006`: a local PowerShell helper around approved recovery commands
  reported non-zero adb command codes while a visual checkpoint was still
  captured; classify recovery from screenshot/XML evidence and local-only raw
  command artifacts, not from that wrapper status alone.
- `ANOM-027R-007`: after clean direct recovery restored the actionable catalog,
  intended rail taps for session journal, Steam/top-up and feedback remained on
  the catalog; do not count those intended branches as covered without visual
  proof of their destination states.

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

Current thread result: `partial runtime checkpoint`.

Owner stop/continuation command: `confirmed`.

Default branch push authority: `confirmed for detected default branch main`.

Runtime objective status: `not complete`.

Continuation required: `yes`.

Next thread title target: `TASK-027R — Full app transition graph physical runtime execution`.

Next thread branch/source: continue after this partial checkpoint is committed,
pushed, merged to `main` and pushed to remote default by explicit owner command.

Continuation focus:

- use `docs/qa/reports/task027_full_app_transition_graph_physical_runtime.summary.json`
  as the current public-safe closure ledger;
- do not redo broad preparation unless a concrete blocker appears;
- continue from unclosed rail-route branches: session journal, Steam/top-up QR
  and feedback QR destination coverage;
- revisit QR decode with the established local-only path only if needed;
- preserve all forbidden boundaries: no payment/session start, external QR or
  browser traversal, stream/WebRTC/media playback, Steam/account mutation,
  profile/account mutation or network/offline manipulation;
- keep recording anomalies immediately as a global project rule.

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
