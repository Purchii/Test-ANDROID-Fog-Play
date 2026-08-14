# TASK-044 observed-failure record — Payment-boundary Back is a no-op

## Public-safe identity

- Finding alias: `TASK044-FINDING-NAV-001`
- Scenario: `QA-044-023`
- Final scenario status: `observed_fail` (not `confirmed_defect`)
- Lane: `tv-tpv-013` / `tv-tpv-a12-013`
- APK family: `television-full`
- Evidence status: `confirmed`
- Cause evidence status: `hypothesis`
- Safety classification: `PROD_CONDITIONAL`

## Trigger

Reach the approved payment-boundary screen without starting payment, then press
`Back` once under the bounded navigation oracle.

## Expected result

The app returns to the safe parent screen or presents another explicitly
classified non-mutating navigation state.

## Observed result

The visible payment-boundary state did not change. The no-op was retained as a
navigation failure and was not treated as safe recovery. The observation is
confirmed; its product cause remains a hypothesis and this record is not a
confirmed product-defect claim.

## Recovery and boundary

No payment, purchase, browser/WebView traversal, QR navigation or external
action occurred. A target-app-only force-stop recovered to a safe state. QR
decode, when required for inventory, remained local-only through the established
`jsqr` path and the raw target was never published or followed.

## Test-design implication

Back behavior must be asserted per screen family with visual evidence. A
force-stop fallback is recorded separately and cannot convert the original
payment-boundary no-op to PASS.
