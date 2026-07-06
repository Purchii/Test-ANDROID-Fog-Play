# TASK-027T - Continue visual destination screen coverage

## Mode

`NON_AUTONOMOUS`

## Production safety classification

Tracked task docs, public-safe reports, validators and unit tests are
`PROD_SAFE`.

Physical Android TV runtime remains `PROD_CONDITIONAL`. The existing selected
lane approval was reviewed as sufficient only if the same device/APK/account
and ignored evidence lane can be locally reconfirmed.

The fresh worktree initially did not contain the ignored local-only
selected-lane material. After the owner instructed autonomous runtime
continuation, TASK-027T restored the same lane from the same-machine owner
checkout and executed bounded runtime. Raw artifacts stayed ignored local-only.

## Objective

Continue the TASK-027S visual destination coverage attempt for the rail
destinations that TASK-027R and TASK-027S did not prove:

- session journal;
- Steam/top-up QR;
- feedback QR;
- launcher-entry/app-shell-loader recovery gates needed before those routes can
  be asserted.

TASK-027R closed the transition graph by terminal ledger classification only.
TASK-027S confirmed a launcher/recommendations entry surface and the
`app_shell_loader_after_launcher_entry` anomaly, but did not visually reach the
three target destination screens. TASK-027T produced fresh runtime evidence for
all three target destinations.

## Initial TASK-027T status

TASK-027T executed bounded runtime evidence collection. The public-safe summary
records:

- runtime execution status: `covered`;
- run status: `covered`;
- target destination coverage: `covered`;
- visual destination proof: `true` for session journal, Steam/top-up QR and
  feedback QR;
- QR decode status: `local_only_decoded` for the QR destinations;
- QR navigation followed: `false`;
- all public-safety flags set to false.

Prior TASK-027R/TASK-027S evidence explains blockers and source context, but
TASK-027T coverage is based on fresh `rt027t-*` checkpoints only.

## Required future runtime gates

TASK-027T marked destinations `covered` only after the same selected lane was
locally reconfirmed and fresh TASK-027T checkpoint evidence proved all of the
following in a public-safe way:

- a loaded, actionable app state was reached before route assertions;
- `app_shell_loader_after_launcher_entry` was not counted as catalog or
  destination coverage;
- the specific destination screen was visually reached;
- screenshot/visual inspection and UI XML capture were both recorded
  local-only;
- QR screens, if reached, were decoded local-only only, with no external
  navigation followed;
- payment, stream/session, Steam/account mutation, profile/account mutation,
  network manipulation and external browser/WebView traversal remained outside
  the executed boundary.

## Owned public-safe artifacts

- `docs/qa/reports/task027t_continue_visual_destination_screen_coverage.summary.json`
- `docs/qa/reports/task027t_continue_visual_destination_screen_coverage.md`
- `automation/native_regression/validate_task027t_visual_destination_report.py`
- `tests/test_task027t_visual_destination_report_validator.py`

## Verification baseline

```text
git status --short --branch
git diff --check
python automation/native_regression/validate_task027t_visual_destination_report.py --report docs/qa/reports/task027t_continue_visual_destination_screen_coverage.summary.json
python -m pytest -q tests/test_task027t_visual_destination_report_validator.py
python automation/native_regression/validate_task027s_visual_destination_report.py --report docs/qa/reports/task027s_visual_destination_screen_coverage.summary.json
python automation/native_regression/validate_task027_transition_graph_report.py --report docs/qa/reports/task027_full_app_transition_graph_physical_runtime.summary.json
python -m compileall -q automation tests
```
