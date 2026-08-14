# TASK-044 observed-failure record — Settings Gamepad selection routes to logout

## Public-safe identity

- Finding alias: `TASK044-FINDING-SETTINGS-001`
- Scenario: `QA-044-018`
- Final scenario status: `observed_fail` (not `confirmed_defect`)
- Lane: `tv-tpv-013` / `tv-tpv-a12-013`
- APK family: `television-full`
- Evidence status: `confirmed`
- Cause evidence status: `hypothesis`
- Safety classification: `PROD_CONDITIONAL`

## Trigger

Navigate to Settings, visually place focus on the Gamepad item, and activate the
focused destination with the approved D-pad action.

## Expected result

The Gamepad destination opens and can be inventoried without account mutation.

## Observed result

Logout confirmation opened instead. This is classified as a visual-semantic
focus/routing mismatch, not successful Gamepad coverage.

## Safe boundary and impact

Only Cancel was selected. Logout, account/profile mutation and session changes
were not performed. The Gamepad route oracle remains unresolved and blocks a
clean reference-lane result.
The observation is confirmed, but the visual-semantic cause remains a
hypothesis and is not asserted as a confirmed product defect.

## Evidence boundaries and test implication

Raw screenshots, UI trees, logs and account-like values remain local-only.
Future automation must verify the destination immediately after activation,
hold logout confirmation at a Cancel-only boundary and preserve the accidental
route as first-failure evidence.
