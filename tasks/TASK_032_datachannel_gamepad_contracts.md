# TASK-032 - DataChannel and gamepad protocol contract tests

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

`TASK-032 - DataChannel and gamepad protocol contract tests`

## Branch

`qa/task-032-datachannel-gamepad-contracts`

## Production safety classification

`PROD_SAFE_OFFLINE_WITH_LOCAL_QUARANTINE_INPUT`

TASK-032 is offline/local only. It may read the ignored API-layer quarantine
pack to validate DataChannel and gamepad protocol fixture categories. It must
not make live WebRTC/DataChannel connections, STOMP/WebSocket connections,
REST/backend calls, auth/session/token replay, Android runtime/ADB/APK actions,
endpoint discovery/publication, payment/order/session mutation or executable
API recipes.

## Context

TASK-028 created the API-layer offline intake. TASK-029 and TASK-030 covered
REST schema/fixture and mocked REST negative/cache/state-sequence contracts.
TASK-031 covered only `stomp_signaling` and `stomp_device` protocol fixture
groups, and explicitly reserved DataChannel/gamepad rows for TASK-032.

TASK-032 narrows the next follow-up into offline fixture contracts for only
`datachannel` and `gamepad` groups. It does not replace TASK-033 redaction
guard work or TASK-034 optional approved staging/live execution.

## Scope

In scope:

- validate tracked TASK-028, TASK-031 and TASK-036 public summaries
  fail-closed;
- validate TASK-032 rows from the ignored local quarantine pack when present;
- include only `fixtures/datachannel/` and `fixtures/gamepad/` rows in
  TASK-032 pack-backed coverage;
- explicitly report STOMP/device rows as already covered by TASK-031;
- validate protocol fixture references stay inside allowed fixture groups;
- validate protocol fixture JSON readability and minimal shape;
- emit a public-safe TASK-032 report with aliases, counts, categories,
  statuses and blockers only;
- add synthetic pytest coverage for pass and fail-closed cases.

## Out of scope

- live WebRTC/DataChannel handshakes, channel negotiation, sends or receives;
- live gamepad input, controller pairing, Android input injection or HID
  behavior;
- live STOMP/WebSocket handshakes, subscriptions, sends or publishes;
- live REST/backend calls;
- auth header/cookie/session/token replay;
- endpoint discovery, endpoint publication or executable API recipes;
- Android runtime, ADB, APK read/hash/install/launch or modification;
- network capture/proxying;
- real user, account, payment, order, profile, device binding or session
  mutation data;
- TLS/pinning bypass, APK modification, decompilation, smali or app source use.

## Acceptance criteria

- TASK-032 active-run metadata, task spec, backlog entry and public report
  exist.
- Validator returns `pass` for the present local quarantine pack while keeping
  runtime/live/network/Android statuses `not_run`.
- Missing local pack returns controlled `partial_blocked` with
  `blocked_missing_local_quarantine_pack`, not product evidence.
- Public report contains no raw endpoints, URLs, headers, payloads, fixture
  bodies, tokens, cookies, device/account/payment values, local paths,
  DataChannel payload bodies or gamepad mapping raw values.
- Report explicitly avoids claiming live WebRTC/DataChannel or live gamepad
  behavior from offline fixture checks.
- Tests cover clean synthetic pack/report, missing pack blocker, malformed
  protocol fixture JSON, invalid protocol fixture shape, unsafe fixture
  reference group, source summary mismatch, raw-public rejection,
  live-WebRTC/DataChannel overclaim rejection, Android runtime overclaim
  rejection and CLI behavior.
- Multi-agent Planner, Builder, QA A, QA B, Security/Prod-safety and
  Docs/Scribe reviews complete without unresolved R0/R1 blockers.

## Verification

```text
git status --short --branch
git diff --check
python automation/api_layer_contract/validate_task032_datachannel_gamepad_contracts.py --pack-root <ignored-local-api-audit-pack> --report docs/qa/reports/task032_datachannel_gamepad_contracts.summary.json
python -m pytest -q tests/test_task028_api_layer_contract.py tests/test_task036_api_layer_exhaustive_coverage.py tests/test_task029_rest_schema_fixture_contracts.py tests/test_task030_rest_negative_cache_sequences.py tests/test_task031_stomp_protocol_contracts.py tests/test_task032_datachannel_gamepad_contracts.py
python -m pytest -q tests/test_task032_datachannel_gamepad_contracts.py
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

## Stop conditions

Stop and report a blocker if:

- implementation requires live API/backend/network/runtime/ADB/APK execution;
- implementation requires live WebRTC/DataChannel or live gamepad execution;
- public output would include raw endpoints, URLs, headers, payloads, fixture
  bodies, tokens, cookies, device/account/payment values, local paths,
  DataChannel payload bodies or gamepad mapping raw values;
- local pack is absent and the task cannot return a controlled partial blocker;
- TASK-028/TASK-031/TASK-036 public summary reconciliation fails;
- protocol rows cannot be safely separated into DataChannel/gamepad scope;
- tests fail and cannot be fixed inside TASK-032 scope;
- QA or Security review reports unresolved R0/R1 risk.
