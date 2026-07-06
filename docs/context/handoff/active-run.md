# Active run

## Run Metadata

Mode: `NON_AUTONOMOUS`
Thread title: `TASK-027S — Visual destination screen coverage for TASK-027R rail blockers`
Thread status: `in_progress_visual_destination_coverage`
Fresh thread verified: `yes`
Task ID: `TASK-027S`
Task branch: `qa/task-027s-visual-destination-screen-coverage`
Default branch: `main`
Base commit: `ac9e78b`
Merge/push authority: `NON_AUTONOMOUS; task branch push allowed after verification; no default-branch merge/push without explicit owner command`
Production safety classification: tracked docs/source, validators, templates
and local public-safe scans are `PROD_SAFE`; physical Android TV runtime,
ADB/APK/app launch, screenshot/XML/log/video capture and local QR decode are
`PROD_CONDITIONAL` and are open only for the same selected TASK-027 lane and
the same transition-graph / visual-destination rail coverage objective.

## Goal

Visually cover, or terminally classify as still blocked, the rail destination
screens that TASK-027R did not visually reach: session journal, Steam/top-up QR
and feedback QR, plus any immediately required rail/focus state needed to prove
or reject those routes.

TASK-027R `full_graph_closed` is terminal ledger closure only. It does not count
as visual destination coverage for session journal, Steam/top-up QR or feedback
QR. Those destinations remain uncovered unless TASK-027S captures fresh
screenshot/visual inspection proof of the destination screen.

## Current Status

The fresh TASK-027S thread has been renamed and the branch was created from
`origin/qa/task-027r-full-graph-closure-final` at commit `ac9e78b`. Source-of-
truth docs and the TASK-027R public report/summary/handoff have been read.

Existing post-preflight runtime-boundary approval was reviewed by
Security/Prod-safety for TASK-027S and remains sufficient only because this run
keeps the same selected device/APK/account/evidence lane and the same
transition-graph / visual-destination rail coverage objective:

- device alias: `tv-tpv-013`;
- runtime profile alias: `tv-tpv-a12-013`;
- build family alias: `task-005-local-apk-television-full`;
- synthetic user alias: `qa-user-phone-001`;
- ignored local-only evidence storage, redaction-by-default and no public raw
  screenshots, XML, logs, QR targets, APK hashes, device identifiers or account-
  like values.

If any lane element or scope changes, TASK-027S must stop for fresh owner
approval before ADB/runtime action.

Strict real multi-agent workflow is active:

- Orchestrator: current thread;
- Planner: completed TASK-027S scope, acceptance and verification plan;
- Builder: completed tracked-doc reconnaissance for prior safe route patterns
  and confirmed no tracked rail-targeting oracle exists;
- QA Reviewer A: final review `PASS` after remediation for local-only archive
  filename redaction and 120-second timeout validator enforcement;
- QA Reviewer B: final review `PASS` after remediation for target-specific
  destination evidence IDs and verification-memory wording;
- Security/Prod-safety Reviewer: `APPROVED_WITH_CONDITIONS` for same-lane
  bounded visual-destination runtime after this TASK-027S active-run framing;
  final review `PASS` after remediation for synthetic negative-test path
  wording;
- Docs/Scribe: final review `PASS` after remediation for exact task title,
  precise blocked status and TASK-027S-specific closure wording.

TASK-027S may not repeat the same old coordinate/key/D-pad no-op attempts from
`ANOM-027R-008` unless a new focus/targeting oracle is present. The only
currently identified safer route pattern from tracked source-of-truth is the
TASK-020/TASK-023 state-dependent catalog scroll/lateral movement pattern; if
that cannot prove a destination visually within bounded attempts, TASK-027S
must classify the destination coverage as blocked.

Public-safe TASK-027 contract artifacts exist and were updated or revalidated:

- `tasks/TASK_027_full_app_transition_graph_physical_runtime.md`;
- `docs/qa/reports/task027_full_app_transition_graph_physical_runtime.summary.json`;
- `docs/qa/reports/task027_full_app_transition_graph_physical_runtime.md`;
- `automation/native_regression/validate_task027_transition_graph_report.py`;
- `tests/test_task027_transition_graph_validator.py`.

Validator hardening in this continuation now requires the session journal,
Steam/top-up QR and feedback QR rail routes to appear as directed transition
families. It also blocks premature `full_graph_closed` reports unless
`runtime_execution_status=closed_by_ledger`, unresolved areas are empty, all
guarded boundary categories are represented and evidence IDs use accepted
TASK-027 checkpoint/QR ID shapes.

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

Physical app runtime is unblocked for this fresh TASK-027S thread only inside
the same selected-lane approval reviewed above. QA Reviewer A, QA Reviewer B
and Security/Prod-safety approval from the TASK-027R runtime boundary remains
usable only because the lane and objective did not change.

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

Local-only TASK-027S runtime evidence is stored under ignored evidence storage.
Public reports may reference only checkpoint IDs, not raw screenshots, XML,
logs, APK names/hashes, QR targets, device identifiers or account-like values.

Confirmed public-safe TASK-027S checkpoint families so far:

- `rt027s-cp057-launch-wait` and `rt027s-cp058-post-launch`: explicit launch
  oracle stayed on a Google TV launcher/system surface instead of restoring
  the approved in-app catalog rail.
- `rt027s-cp059-after-12-dpad-down` through
  `rt027s-cp063-after-rail-dpad-down-2`: D-pad movement acted on launcher/app
  recommendation surfaces, not on the approved in-app rail state.
- `rt027s-cp064-monkey-launch` and `rt027s-cp065-monkey-launch-wait`:
  alternate leanback/package launch oracle also stayed on a Google TV launcher
  surface.
- `rt027s-cp066-launcher-recommendations-pre-entry`: Google TV launcher /
  recommendations app entry surface was visible and is now a covered entry
  surface category for future navigation models.
- `rt027s-cp067-after-visible-app-icon-entry` and
  `rt027s-cp068-after-entry-wait`: visible launcher app entry opened an
  anomalous app shell loader state with left in-app rail visible and persistent
  main-content spinner. XML captured local-only had no focused, clickable or
  scrollable target nodes for the visible rail state. This is
  `app_shell_loader_after_launcher_entry`, not catalog, session journal,
  Steam/top-up QR or feedback QR coverage.
- `rt027s-cp069-loader-rail-start`: TV/system ambient surface appeared during
  idle continuation. It is an external/system interruption, not an app screen
  or destination coverage.
- `rt027s-cp073-after-wake-home` through
  `rt027s-cp080-after-feedback-center`: safe wake/launcher entry followed by
  bounded D-pad/center candidate attempts for journal, Steam/top-up and
  feedback stayed on the app-shell loader.
- `rt027s-cp081-loader-rail-before-icon-taps` through
  `rt027s-cp084-after-loader-feedback-icon-tap`: direct visible rail-icon taps
  from the app-shell loader also stayed on the app-shell loader and did not
  reach target destinations.
- `rt027s-cp086-loader-timeout-after-2min`: app-shell-loader timeout checkpoint
  after local-only developer diagnostics collection. TASK-027S now treats this
  state with a 120-second maximum wait: after that, record anomaly, collect
  screenshot/XML/log/dumpsys evidence local-only and move on.

Current TASK-027S target destination classification:

- session journal: `blocked_by_app_shell_loader_and_prior_rail_input_blocker`,
  `confirmed`, no fresh visual destination proof;
- Steam/top-up QR: `blocked_by_app_shell_loader_and_prior_rail_input_blocker`,
  `confirmed`, no fresh QR destination reached and no QR navigation followed;
- feedback QR: `blocked_by_app_shell_loader_and_prior_rail_input_blocker`,
  `confirmed`, no fresh QR destination reached and no QR navigation followed;
- Google TV launcher/recommendations entry: `covered_as_entry_surface`,
  `confirmed`, but resulted in `app_shell_loader_after_launcher_entry`.

Local-only archives were created for internal debugging under ignored evidence
storage. Public reports may reference only the archive category and evidence
IDs, not raw archive filenames.

TASK-027R baseline checkpoint families carried for context:

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
- `rt027r-cp052b` through `rt027r-cp056`: continuation relaunch to actionable
  catalog, followed by bounded D-pad, visual-coordinate tap and key sanity
  attempts that remained on the catalog instead of opening session journal,
  Steam/top-up or feedback rail destinations. Screenshots and XML were captured
  local-only for these checkpoints; XML did not expose the visible rail labels
  as usable target nodes.

Bounded crash evidence was captured local-only after the loader recurrence:
the app process was present and the crash buffer was captured without crash
buffer content.

## Runtime Anomalies Recorded In TASK-027S

- `ANOM-027S-001`: activating the visible app entry from the Google TV launcher
  / recommendations surface reached `app_shell_loader_after_launcher_entry`.
  Expected result was a loaded post-auth catalog or recoverable destination.
  Observed result was left app rail plus persistent main-content spinner through
  delayed captures and a 120-second timeout checkpoint. Evidence status:
  `confirmed`. Likely/hypothesis cause: launcher-entry shell hydration or
  content bootstrap stalls after the shell renders; possible unresolved
  profile/session/entitlement bootstrap without a visible error state; possible
  route-host preloader or rail focus/action registration waiting for content
  bootstrap. Test-design implication: detect this state explicitly, collect
  screenshot/XML/log/dumpsys evidence local-only, and do not count it as
  catalog or destination coverage.
- `ANOM-027S-002`: explicit and leanback launch oracles stayed on Google TV
  launcher/system surfaces instead of restoring the in-app catalog. Evidence
  status: `confirmed`. Test-design implication: entry-surface coverage and
  in-app destination coverage must be tracked separately.
- `ANOM-027S-003`: TV/system ambient surface appeared during idle continuation.
  Evidence status: `confirmed`. It is an external/system interruption, not an
  app screen or destination coverage.
- `ANOM-027S-004`: bounded D-pad/center and direct visible rail-icon attempts
  from the app-shell loader remained on the loader and did not reach session
  journal, Steam/top-up QR or feedback QR destinations. Evidence status:
  `confirmed`. Test-design implication: do not repeat further coordinate/key
  attempts from this loader state without a new state/focus oracle.

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
- `ANOM-027R-008`: in this continuation, relaunch restored actionable catalog,
  but D-pad, visual-coordinate tap and bounded key sanity sampling still left
  the view on catalog; UIAutomator did not expose visible rail labels as target
  nodes. Force-stop cleanup was executed, and the rail destinations remain
  blocked by tooling rather than covered.

## TASK-027S Destination-Screen Closure Requirements

TASK-027S closure requires a visual destination ledger where each target
destination screen and immediately required entry/focus state is classified as:

- `covered`;
- `blocked_by_boundary`;
- `blocked_by_tooling`;
- `blocked_by_app_shell_loader_and_prior_rail_input_blocker`;
- `blocked_by_external_state`;
- `not_run_out_of_scope`.

Every runtime checkpoint must include screenshot/visual inspection and XML when
available. XML-vs-visual mismatches are first-class tooling gaps. Recurrent
screens and anomalies must be recorded immediately.

## Dynamic Data Rule

Game catalog and server-list contents may change over time. TASK-027S must
assert screen categories, focus/scroll behavior, transition outcomes,
redaction and boundaries. It must not assert fixed game titles, server counts,
server aliases, prices, hardware rows, ping values or complete row enumeration.

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

TASK-027S must recheck or explicitly carry with reasons:

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
python automation/native_regression/validate_task027s_visual_destination_report.py --report docs/qa/reports/task027s_visual_destination_screen_coverage.summary.json
python -m pytest -q tests/test_task027_transition_graph_validator.py tests/test_task027s_visual_destination_report_validator.py
python automation/native_regression/validate_task026b_no_device_task025b_runtime_tests.py --scenarios docs/qa/native-regression/task025b_physical_runtime_test_scenarios.json --report docs/qa/reports/task026b_task025b_physical_runtime_tests.summary.template.json
python -m pytest -q tests/test_task025_native_regression.py tests/test_task025_native_regression_validator.py tests/test_task026a_no_device_readiness_coverage.py tests/test_task026b_no_device_task025b_physical_runtime_tests.py tests/test_task027_transition_graph_validator.py tests/test_task027s_visual_destination_report_validator.py
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

Current thread result:
`verified_destination_coverage_blocked_by_app_shell_loader_and_prior_rail_input_blocker`.

Owner clarification: the app-shell-loader state is an important frequent bug
to hand off to developers, not by itself the TASK-027S final blocker. TASK-027S
must continue to pursue visual destination coverage or terminally classify each
destination screen with evidence.

Default branch push authority: `not granted`.

Runtime objective status:
`destination_coverage_not_visually_proven_blocked_by_app_shell_loader_and_prior_rail_input_blocker`.

Continuation required: `commit and push task branch; no default-branch merge or
push without explicit owner command`.

Next thread title target: `none yet`.

Next thread creation status: `not_created`.

Next thread branch/source: no automatic continuation thread should be created
until TASK-027S is fully verified and the owner selects follow-up work. Because
this run is `NON_AUTONOMOUS`, default branch merge/push requires explicit owner
command after the task branch is pushed.

Future task focus if owner approves a new independent task after TASK-027S:

- add/implement a reliable app-shell-loader state detector and 120-second
  timeout handling in runtime automation;
- investigate the launcher-entry content bootstrap / route-host / focus
  registration failure using the local-only developer handoff archive;
- solve the confirmed rail focus/input blocker with a new reliable focus or
  targeting oracle before retrying session journal, Steam/top-up QR and
  feedback QR destination coverage;
- revisit QR decode with the established local-only path only after QR
  destinations are visually reached;
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
