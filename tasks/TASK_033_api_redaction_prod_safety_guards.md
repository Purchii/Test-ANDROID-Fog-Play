# TASK-033 - API-layer redaction and production-safety guard tests

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

`TASK-033 - API-layer redaction and production-safety guard tests`

## Branch

`qa/task-033-api-redaction-prod-safety-guards`

## Production safety classification

`PROD_SAFE_OFFLINE_STATIC_AND_SYNTHETIC_ONLY`

TASK-033 is local/static and synthetic-only. It must not read raw API pack
values, make live API/backend/network calls, run Android runtime or ADB, read
or install APKs, execute WebRTC/DataChannel/STOMP/WebSocket traffic, use
gamepad input, perform payment/order/session/profile/device mutation, replay
auth headers/tokens/cookies, publish endpoints or use security bypasses.

## Context

TASK-028 created the offline API-layer intake and identified 8 security/
redaction rows. TASK-029 through TASK-032 covered REST, mocked REST sequence,
STOMP/device protocol and DataChannel/gamepad fixture contracts. TASK-036
tracks TASK-033 as the remaining synthetic guard layer with
`tracked_summary_validated_synthetic_guard_tests_required`.

TASK-033 closes that offline redaction and production-safety guard slice. It
does not replace TASK-034 optional staging/live execution, which remains
blocked until explicit `PROD_CONDITIONAL` approvals exist.

## Scope

In scope:

- validate TASK-028 and TASK-036 public summaries for the 8 known API-layer
  security/redaction guard rows;
- add a synthetic guard ledger for fabricated credential, cookie/session,
  endpoint/route, payload, local artifact, device identifier, account/payment,
  QR target, runtime-live-action and budget-counter specimens;
- reject raw-looking nested values or keys in public reports;
- reject live/runtime/API/ADB/APK/payment/session overclaims and nonzero live
  budget counters;
- reject unsafe public-safety booleans, unknown fields, missing required
  fields and pass-with-blockers reports;
- generate a public-safe TASK-033 report containing only aliases, counts,
  categories, statuses and blockers;
- add focused pytest coverage for pass and fail-closed cases.

## Out of scope

- live REST/backend/API calls;
- STOMP/WebSocket/DataChannel/WebRTC execution;
- Android runtime, ADB, APK read/hash/install/launch or modification;
- reading ignored local API quarantine pack raw values;
- endpoint discovery/publication or executable API recipes;
- auth/session/token/header/cookie replay;
- payment/order/session/profile/account/device mutation;
- real QR target traversal;
- gamepad/controller runtime input or pairing;
- security bypass, APK patching, decompilation, smali or app source use.

## Acceptance criteria

- TASK-033 task spec, active-run metadata, validator, tests and public report
  exist.
- Public report status is `pass` for embedded fabricated synthetic specimens.
- Source reconciliation confirms TASK-028/TASK-036 public summaries expose 8
  known security/redaction rows for TASK-033 and keep live/runtime statuses
  `not_run`.
- Validator fails closed on raw-looking nested text or keys, local path leaks,
  unsafe public-safety flags, unknown fields, missing fields, pass-with-
  blockers, live/runtime/API overclaims and nonzero live budget drift.
- Missing optional external synthetic specimen file is a controlled
  `partial_blocked` report and CLI exits nonzero unless an explicit partial
  blocker flag is used.
- Public report contains no raw endpoints, URLs, headers, payloads, fixture
  bodies, tokens, cookies, QR targets, device/account/payment/session values,
  local paths, protocol payload bodies or gamepad mapping values.
- Multi-agent Planner, Builder, QA A, QA B, Security/Prod-safety and
  Docs/Scribe reviews complete without unresolved R0/R1 blockers.

## Verification

```text
git status --short --branch
git diff --check
python automation/api_layer_contract/validate_task033_api_redaction_prod_safety_guards.py --report docs/qa/reports/task033_api_redaction_prod_safety_guards.summary.json
python -m pytest -q tests/test_task033_api_redaction_prod_safety_guards.py
python -m pytest -q tests/test_task028_api_layer_contract.py tests/test_task036_api_layer_exhaustive_coverage.py tests/test_task029_rest_schema_fixture_contracts.py tests/test_task030_rest_negative_cache_sequences.py tests/test_task031_stomp_protocol_contracts.py tests/test_task032_datachannel_gamepad_contracts.py tests/test_task033_api_redaction_prod_safety_guards.py tests/test_task037_production_api_runtime_report.py
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

## Stop conditions

Stop and report a blocker if:

- implementation requires live API/backend/network/runtime/ADB/APK execution;
- implementation requires reading or publishing raw API pack material;
- public output would include raw endpoints, URLs, headers, payloads, fixture
  bodies, tokens, cookies, QR targets, device/account/payment/session values,
  local paths, protocol payload bodies or gamepad mapping values;
- TASK-028/TASK-036 public summary reconciliation fails and cannot be fixed in
  TASK-033 scope;
- tests fail and cannot be fixed inside TASK-033 scope;
- QA or Security review reports unresolved R0/R1 risk.
