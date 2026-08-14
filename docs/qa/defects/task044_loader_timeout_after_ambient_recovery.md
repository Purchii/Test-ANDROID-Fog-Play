# TASK-044 defect — loader timeout after ambient recovery

## Public-safe identity

- Defect alias: `TASK044-DEFECT-LOADER-001`
- Scenarios: `QA-044-002`, `QA-044-004`
- Final scenario status: `confirmed_defect`
- Lane: `tv-tpv-013` / `tv-tpv-a12-013`
- APK family: `television-full`
- Evidence status: `confirmed`
- Safety classification: `PROD_CONDITIONAL`

## Trigger

Launch the approved Television Full entry after waking the physical TV from an
ambient/screensaver interruption.

## Expected result

The application reaches a visually and structurally actionable catalog within
the bounded `120 s` loader oracle.

## Observed result

The application remained on a non-actionable loader for the complete bounded
interval. D-pad input did not establish actionable focus. The loader was not
counted as catalog success.

## Recovery and recurrence

A target-app-only `force-stop` followed by the approved launcher entry restored
the actionable catalog. The first timeout evidence is retained separately from
the successful recovery; recovery does not convert the original attempt to a
clean pass.

## Impact

- cold/warm startup reliability is not cleanly closed;
- downstream catalog, Search, Settings and detail scenarios must retain the
  startup anomaly in their evidence lineage;
- release evidence remains conditional until the startup path is rechecked in
  a fresh run.

## Evidence boundaries

Raw screenshots, UI trees, logs, device/build identifiers and dynamic account
or catalog values remain only in ignored local TASK-044 evidence storage.
Tracked reports use category-level aliases and do not expose QR targets or any
on-screen account value.

## Test-design implication

Every reference-lane startup check must distinguish ambient/system state,
loader/non-actionable state and actionable catalog, enforce the `120 s` cap,
retain the first failure, and record any force-stop/relaunch as a separate
recovery attempt.
