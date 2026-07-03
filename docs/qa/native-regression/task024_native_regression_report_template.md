# TASK-024 native regression report template

This public report records selected-lane native regression results using
aliases, categories and evidence ids only.

## Required status

- `run_status`: `pass`, `pass_with_known_anomalies`, `partial`, `blocked` or
  `fail`.
- `runtime_execution_status`: `pass`, `partial`, `blocked`, `not_run` or
  `fail`.
- Every required regression case `NR-001` through `NR-010` must have a result.
- `blocked`, `blocked_by_boundary`, `not_run`, `fail` and `known_anomaly`
  results require a public-safe reason.

## Public-safety requirements

Public reports must not include raw phone/OTP values, device identifiers, raw
screenshots, XML, logs, videos, APK paths/hashes, QR targets, private URLs,
endpoints, routes, game title dumps, server names, prices, ping values,
hardware rows or account-like values.

Boundary screens are valid regression evidence only when the boundary is
classified and not entered. Payment, WebView/browser/external QR traversal,
stream/media/session start, account/profile mutation, controller reset/remap
and network manipulation must never be marked as a passed action in TASK-024.

## Dynamic data policy

TASK-024 asserts screen families, focus/actionability, field categories,
boundary handling, recovery and redaction. It intentionally does not assert
fixed game titles, game counts, server rows, server aliases, ping values,
hardware strings, prices, QR targets or account-like labels.
