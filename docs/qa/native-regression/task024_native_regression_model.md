# TASK-024 native post-auth regression model

## Purpose

TASK-024 converts selected-lane discovery from TASK-020, TASK-021, TASK-022 and
TASK-023 into repeatable native regression oracles. It is not a new exhaustive
navigation claim.

## Baseline evidence

- TASK-019: selected-lane auth/session restore and session persistence.
- TASK-020: post-auth navigation, full screen-family inventory, QR/boundary and
  recovery findings.
- TASK-021: reversible DNS offline-like screen and refresh recovery data point.
  True Wi-Fi-off product verdict remains `unknown`.
- TASK-022: Xbox-like/gamepad hints, payment QR boundary and Settings Gamepad
  section evidence.
- TASK-023: public-safe data categories, dynamic list policy and automation
  anomalies.

## Regression oracles

The suite asserts category-level outcomes:

- screen/state family reached;
- focus/actionability observed;
- expected data category exists;
- visible keyboard input path is used where required;
- dynamic lists expose stable field categories and scroll/focus behavior;
- boundary surfaces are classified and not entered;
- recovery route works or a known anomaly is reported;
- session persistence checkpoints are recorded;
- public report redaction invariants hold.

## Forbidden oracles

Do not assert fixed game titles, game counts, server counts, server aliases,
ping values, GPU/CPU values, tariff or price values, QR target values,
account-like labels, raw URLs or raw local evidence paths.

## Required cases

The canonical suite is
`docs/qa/native-regression/task024_native_regression_suite.json`.
Required cases are `NR-001` through `NR-010`; `NR-011` and `NR-012` link
TASK-021/TASK-022 baselines without broad network or gamepad compatibility
claims.
