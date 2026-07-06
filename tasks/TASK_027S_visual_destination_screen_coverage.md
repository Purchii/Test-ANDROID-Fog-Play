# TASK-027S — Visual destination screen coverage for TASK-027R rail blockers

## Mode

`NON_AUTONOMOUS`

## Production safety classification

Tracked docs, validators, tests and public-safe scans are `PROD_SAFE`.

Physical Android TV runtime was `PROD_CONDITIONAL` and was allowed only because
TASK-027S kept the same selected TASK-027 lane:

- device alias: `tv-tpv-013`;
- runtime profile alias: `tv-tpv-a12-013`;
- build family alias: `task-005-local-apk-television-full`;
- synthetic user alias: `qa-user-phone-001`;
- ignored local-only evidence storage and redaction-by-default.

If any lane or scope changes, fresh owner approval is required before further
ADB/runtime action.

## Objective

Visually cover, or terminally classify as blocked, the TASK-027R rail
destinations that were not visually reached:

- session journal;
- Steam/top-up QR;
- feedback QR;
- immediately required rail/focus states proving those routes.

TASK-027R `full_graph_closed` is only terminal ledger closure. It does not
prove destination-screen coverage for these three route families.

## TASK-027S runtime result

TASK-027S found and recorded an additional app entry surface through Google TV
launcher/app recommendations. This entry surface must be covered in future
navigation models because it is a real user-visible way to start the app.

However, activating the visible launcher app entry did not reach the expected
post-auth catalog. It reached an anomalous app shell loader state:

- left in-app rail was visible;
- the main content area stayed on a spinner/loader;
- XML had no focused, clickable or scrollable target nodes in the visible rail
  state;
- delayed capture and a 120-second timeout checkpoint still showed the same
  loader state;
- no session journal, Steam/top-up QR or feedback QR destination was visually
  reached.

The public-safe state alias is:

```text
app_shell_loader_after_launcher_entry
```

This is a first-class TASK-027S anomaly and must not be classified as catalog,
session journal, Steam/top-up QR, feedback QR or successful app entry.

Runtime handling rule for this condition: wait no longer than 120 seconds in
the preloader/app-shell-loader state, then record the anomaly, capture
local-only screenshot/XML/log/dumpsys diagnostics for developers and continue
with the next bounded route or safe recovery.

## Public-safe evidence IDs

- `rt027s-cp057-launch-wait` and `rt027s-cp058-post-launch`: explicit launch
  stayed on a Google TV system launcher surface.
- `rt027s-cp059-after-12-dpad-down` through `rt027s-cp063-after-rail-dpad-down-2`:
  D-pad movement acted on launcher/app recommendation surfaces rather than the
  approved in-app rail state.
- `rt027s-cp064-monkey-launch` and `rt027s-cp065-monkey-launch-wait`:
  alternate package launch oracle still stayed on the Google TV launcher
  surface.
- `rt027s-cp066-launcher-recommendations-pre-entry`: launcher recommendations
  / app entry surface visible before app entry.
- `rt027s-cp067-after-visible-app-icon-entry` and
  `rt027s-cp068-after-entry-wait`: app shell loader after visible launcher app
  icon entry, with no destination-screen coverage.
- `rt027s-cp074-after-entry-short-wait` through
  `rt027s-cp080-after-feedback-center`: bounded D-pad/center route attempts
  from the loader remained on the loader and did not reach journal, Steam/top-up
  QR or feedback destinations.
- `rt027s-cp081-loader-rail-before-icon-taps` through
  `rt027s-cp084-after-loader-feedback-icon-tap`: direct visible rail-icon taps
  from the loader also remained on the loader.
- `rt027s-cp086-loader-timeout-after-2min`: preloader timeout checkpoint after
  local-only diagnostics collection.

Raw screenshots, XML and local zip archive remain ignored local-only. Public
reports may reference only evidence IDs and category-level findings.

## Destination status

| Target | TASK-027S status | Evidence | Notes |
|---|---|---|---|
| Session journal | `blocked_by_app_shell_loader_and_prior_rail_input_blocker` | `rt027s-cp076`, `rt027s-cp082`, `rt027s-cp086`, prior `rt027r-cp052b`-`rt027r-cp056` | No fresh visual destination proof. |
| Steam/top-up QR | `blocked_by_app_shell_loader_and_prior_rail_input_blocker` | `rt027s-cp078`, `rt027s-cp083`, `rt027s-cp086`, prior `rt027r-cp052b`-`rt027r-cp056` | No QR destination reached; no QR target followed. |
| Feedback QR | `blocked_by_app_shell_loader_and_prior_rail_input_blocker` | `rt027s-cp080`, `rt027s-cp084`, `rt027s-cp086`, prior `rt027r-cp052b`-`rt027r-cp056` | No QR destination reached; no QR target followed. |
| Google TV launcher app entry | `covered_as_entry_surface` | `rt027s-cp066`, `rt027s-cp067`, `rt027s-cp086` | Entry surface discovered and must be modeled separately. |

## New anomaly

`ANOM-027S-001`:

- trigger/action: activate the visible MTC Fog Play app entry from Google TV
  launcher/recommendations surface;
- expected result: post-auth catalog or another recoverable app destination
  screen loads;
- observed result: app shell rail appears, but main content remains on a
  spinner/loader through delayed capture and the 120-second timeout checkpoint;
- evidence status: `confirmed`;
- likely/hypothesis cause: launcher-entry or app-shell hydration/content
  bootstrap stall where the navigation shell renders but the catalog/content
  route does not complete; possible unresolved profile/session/entitlement
  bootstrap without a visible error state; possible route-host preloader or
  rail focus/action registration waiting for content bootstrap;
- test-design implication: future automation must detect
  `app_shell_loader_after_launcher_entry` as a blocker and must not count it as
  catalog or destination coverage.

`ANOM-027S-003` records an external TV ambient/screensaver interruption during
idle runtime and keeps it out of app coverage. `ANOM-027S-004` records that
bounded D-pad/center and direct visible rail-icon attempts from the loader did
not reach the target destination screens.

## Boundaries

TASK-027S did not perform:

- real payment or paid session start;
- stream/WebRTC/media playback/game session start;
- external QR/WebView/browser traversal;
- Steam/account connection mutation;
- profile/account mutation or logout confirmation;
- network/offline manipulation;
- captcha solving/bypass;
- APK patch/decompile/resign/security bypass.

## Verification baseline

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
