# Post-Auth Navigation Transition Coverage

Task: `TASK-020 XL+ - Post-auth native navigation transitions`

This document defines bounded post-auth native navigation coverage for the
selected `tv-tpv-013` lane. It converts the TASK-011 planning model into a
runtime-ready coverage frontier without treating the result as exhaustive app
proof.

## Lane

```text
device_alias: tv-tpv-013
runtime_profile_alias: tv-tpv-a12-013
build_alias: task-005-local-apk-001
synthetic_user_alias: qa-user-phone-001
```

## Coverage Dimensions

- screen inventory after auth;
- safe native transition edges;
- D-pad focus path sampling;
- Back behavior and recovery;
- Home/foreground session persistence;
- force-stop/relaunch session persistence;
- natural loading, empty, error and entitlement states if encountered;
- payment/WebView/stream/account/network boundaries reached and not entered;
- coverage frontier and unknowns.

## Boundary Rule

When a control or screen appears related to payment, WebView/redirect,
stream/media playback, profile/account mutation or network/offline
manipulation, the probe records a boundary and does not enter it.

```json
{
  "result": "blocked_by_boundary",
  "action_taken": "not_entered"
}
```

Correct boundary detection is not a product failure.

## Coverage Status

Use one of:

```text
sampled_bounded_runtime_coverage
partial_budget_limited_coverage
blocked
not_run
```

Never report TASK-020 as exhaustive navigation proof.
