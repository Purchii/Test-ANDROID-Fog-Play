# TASK-024 - Native post-auth regression pack + selected-lane runtime regression

## Mode

`BOUNDED_AUTONOMOUS`

Owner authorization in this thread permits task-branch push, verified
integration into the detected default branch and default-branch push after all
TASK-024 gates pass. The detected default branch is `main`.

## Branch

```text
qa/task-024-native-post-auth-regression-pack
```

## Goal

Repair clean-archive test/report hygiene, restore TASK-021 source-of-truth, and
turn TASK-020/TASK-021/TASK-022/TASK-023 selected-lane evidence into a
public-safe native post-auth regression pack.

## Phase Gates

- Phase A: repository/test/report hygiene repair.
- Phase B: native regression model, runner, suite and public report validator.
- Phase C: selected-lane runtime regression only after Phase A and Phase B pass
  and only when runtime prerequisites and collector/input evidence are
  approved.
- Phase D: public-safe report, docs, handoff, reviews and integration.

If Phase A fails, Phase B/C must not run. If Phase B fails, Phase C must not
run.

## Baseline Evidence

- TASK-019 auth/session restore on `tv-tpv-013`.
- TASK-020 post-auth navigation and full screen-family inventory.
- TASK-021 reversible DNS offline-like runtime data point.
- TASK-022 Xbox-like/gamepad inventory.
- TASK-023 full public-safe data inventory and dynamic-list policy.

## Production Safety

- `PROD_SAFE`: docs, validators, tests, static/hygiene scans and default
  fail-closed runner behavior.
- `PROD_CONDITIONAL`: selected-lane Phase C runtime only after Phase A/B pass,
  with raw evidence under ignored `.qa_local/evidence/task-024/`.
- `PROD_FORBIDDEN`: payment, subscription, purchase, checkout, external
  QR/browser/WebView traversal, stream/WebRTC/media playback, paid game/session
  start, Steam/account connection, profile/account mutation, captcha
  solving/bypass, network/offline manipulation, packet capture, proxying,
  TLS/security bypass, APK patch/decompile/resign and private endpoint/deeplink
  extraction.

## Regression Policy

TASK-024 asserts screen/state family, focus/actionability, category-level data,
boundary classification, recovery behavior, session persistence and redaction.
It does not assert fixed game titles, game counts, server counts, server
aliases, ping values, GPU/CPU values, tariff/price values, QR target values or
account-like labels.

## Deliverables

- `docs/qa/native-regression/task024_native_regression_model.md`
- `docs/qa/native-regression/task024_native_regression_suite.json`
- `docs/qa/native-regression/task024_native_regression_report_template.md`
- `automation/native_regression/run_native_regression_probe.py`
- `automation/native_regression/validate_native_regression_report.py`
- `tests/test_native_regression_probe.py`
- `tests/test_native_regression_report_validator.py`
- `docs/qa/reports/task024_native_post_auth_regression.summary.json`
- `docs/qa/reports/task024_native_post_auth_regression.md`

## Acceptance Criteria

- Phase A full test/hygiene/report gate passes.
- Phase B targeted tests pass and default TASK-024 runner returns
  `overall_status=blocked`, `runtime_execution_status=not_run`.
- Public validator rejects raw values, raw paths, dynamic value dumps, forbidden
  coverage claims and boundary entries marked as pass.
- Phase C either runs with approved collector/input evidence or blocks before
  ADB/runtime with exact reason.
- Public reports use aliases/categories/evidence ids only.
- Multi-agent QA/Security/Docs review passes before integration.
