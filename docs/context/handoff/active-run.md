# Active run

## Run Metadata

Mode: `BOUNDED_AUTONOMOUS`
Thread title: `TASK-024 - Native post-auth regression pack + selected-lane runtime regression`
Thread status: `phase_c_blocked_before_runtime; final verification in progress`
Fresh thread verified: `yes; thread title set and goal created for TASK-024`
Task ID: `TASK-024`
Task branch: `qa/task-024-native-post-auth-regression-pack`
Default branch: `main`
Base commit: `5482bfb0cf25846aece34ed014201b174a80c049`
Merge/push authority: `Owner explicitly authorized push/merge/push to detected default branch after all TASK-024 gates pass; no force-push`
Production safety classification: `PROD_SAFE` for docs/tests/static tooling and default fail-closed runners; `PROD_CONDITIONAL` for Phase C selected-lane runtime only after Phase A/B pass and approved runtime prerequisites/collector input are present.

## Goal

TASK-024 repairs clean-archive hygiene blockers, restores TASK-021
source-of-truth, and builds a native post-auth regression pack from
TASK-020/TASK-021/TASK-022/TASK-023 selected-lane evidence.

Approved lane for any Phase C runtime:

- `device_alias`: `tv-tpv-013`;
- `runtime_profile_alias`: `tv-tpv-a12-013`;
- `build_alias`: `task-005-local-apk-001`;
- `synthetic_user_alias`: `qa-user-phone-001`.

Raw evidence, if produced, must remain under ignored
`.qa_local/evidence/task-024/`.

## Phase Status

- Phase A: passed. Path validation no longer depends on existing `.qa_local`,
  JSON/BOM hygiene is enforced for committed JSON, TASK-021 source-of-truth is
  restored, and full pytest is green.
- Phase B: passed. Native regression model, suite, fail-closed runner,
  validator and targeted tests are implemented.
- Phase C: blocked before runtime. The explicit `--allow-runtime` command was
  run, but no approved TASK-024 runtime collector/input report was available,
  so no ADB/device/APK navigation executed.
- Phase D: public-safe report/docs/handoff in progress.

## Multi-Agent Status

- Orchestrator: `active`.
- Planner: `complete`.
- Builder scout: `complete`.
- QA Reviewer A: `complete_with_findings_to_address`.
- QA Reviewer B: `complete_with_validator_edge_cases`.
- Security/Prod-safety Reviewer: `complete_with_fail_closed_checklist`.
- Docs/Scribe: `complete_with_docs_update_map`.

## Deliverables

- `tasks/TASK_021_network_offline_runtime_probe.md`
- `tasks/TASK_024_native_post_auth_regression_pack.md`
- `automation/native_regression/run_native_regression_probe.py`
- `automation/native_regression/validate_native_regression_report.py`
- `docs/qa/native-regression/task024_native_regression_model.md`
- `docs/qa/native-regression/task024_native_regression_suite.json`
- `docs/qa/native-regression/task024_native_regression_report_template.md`
- `docs/qa/reports/task024_native_post_auth_regression.summary.json`
- `docs/qa/reports/task024_native_post_auth_regression.md`

## Stop Conditions

Stop before runtime if Phase A or Phase B fails. Stop before selecting or
entering any payment, WebView/browser/external QR, stream/WebRTC/media,
paid game/session, Steam/account connection, profile/account mutation,
captcha-solving, network/offline manipulation, packet capture/proxy/TLS bypass,
private endpoint/deeplink extraction or APK modification path. Stop if raw
phone/OTP, QR targets, screenshots/XML/logs/videos, device identifiers, APK
hashes/paths or dynamic game/server/payment values risk entering public output.
