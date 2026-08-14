# TASK-044 observed-failure record — Search Back keyboard trap

## Public-safe identity

- Finding alias: `TASK044-FINDING-SEARCH-001`
- Scenario: `QA-044-014`
- Final scenario status: `observed_fail` (not `confirmed_defect`)
- Lane: `tv-tpv-013` / `tv-tpv-a12-013`
- APK family: `television-full`
- Evidence status: `confirmed`
- Cause evidence status: `hypothesis`
- Safety classification: `PROD_CONDITIONAL`

## Trigger

Open Search, establish the on-screen keyboard state, then use the approved
single `Back` recovery action.

## Expected result

The keyboard closes and focus returns to an actionable Search or parent state.

## Observed result

The keyboard remained open. The input was not treated as successful navigation
and the state was recorded independently from UI-tree assertions.

## Recovery and impact

A target-app-only force-stop restored a safe restart state. The first failure is
retained and is not converted to PASS by recovery. Search keyboard/back routing
therefore remains a release-blocking reference-lane observed failure.
This record confirms the observation, not a product root cause or confirmed
product-defect classification.

## Evidence boundaries and test implication

Raw screenshots, UI trees, logs, device/build data and entered text remain in
ignored local evidence only. Future checks must visually confirm keyboard
closure and focus return, keep the first no-op/trap evidence, and use force-stop
only as a separately recorded fallback.
