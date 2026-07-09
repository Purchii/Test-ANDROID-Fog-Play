# TASK-031 - STOMP signaling and device protocol contract tests

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

`TASK-031 - STOMP signaling and device protocol contract tests`

## Branch

`qa/task-031-stomp-protocol-contracts`

## Production safety classification

`PROD_SAFE_OFFLINE_WITH_LOCAL_QUARANTINE_INPUT`

TASK-031 is offline/local only. It may read the ignored API-layer quarantine
pack to validate STOMP signaling and device protocol fixture categories. It
must not make live STOMP/WebSocket/DataChannel connections, REST/backend calls,
auth/session/token replay, Android runtime/ADB/APK actions, endpoint
discovery/publication, payment/order/session mutation or executable API
recipes.

## Context

TASK-028 created the API-layer offline intake. TASK-029 and TASK-030 covered
REST schema/fixture and mocked REST negative/cache/state-sequence contracts.
TASK-036 records the remaining protocol follow-up area but its `protocol`
count includes DataChannel/gamepad rows that belong to TASK-032.

TASK-031 narrows the next follow-up into offline fixture contracts for only
`stomp_signaling` and `stomp_device` groups. It does not replace TASK-032
DataChannel/gamepad work, TASK-033 redaction guard work or TASK-034 optional
approved staging/live execution.

## Scope

In scope:

- validate tracked TASK-028, TASK-030 and TASK-036 public summaries
  fail-closed;
- validate TASK-031 rows from the ignored local quarantine pack when present;
- include only `fixtures/stomp_signaling/` and `fixtures/stomp_device/` rows in
  TASK-031 pack-backed coverage;
- explicitly report `datachannel` and `gamepad` rows as TASK-032 out of scope;
- validate protocol fixture references stay inside allowed fixture groups;
- validate protocol fixture JSON readability and minimal shape;
- emit a public-safe TASK-031 report with aliases, counts, categories,
  statuses and blockers only;
- add synthetic pytest coverage for pass and fail-closed cases.

## Out of scope

- live STOMP/WebSocket handshakes, subscriptions, sends or publishes;
- DataChannel/WebRTC runtime or fixture coverage, reserved for TASK-032;
- DataChannel/gamepad protocol rows, reserved for TASK-032;
- live REST/backend calls;
- auth header/cookie/session/token replay;
- endpoint discovery, endpoint publication or executable API recipes;
- Android runtime, ADB, APK read/hash/install/launch or modification;
- network capture/proxying;
- real user, account, payment, order, profile, device binding or session
  mutation data;
- TLS/pinning bypass, APK modification, decompilation, smali or app source use.

## Acceptance criteria

- TASK-031 active-run metadata, task spec, backlog entry and public report
  exist.
- Validator returns `pass` for the present local quarantine pack while keeping
  runtime/live/network statuses `not_run`.
- Missing local pack returns controlled `partial_blocked` with
  `blocked_missing_local_quarantine_pack`, not product evidence.
- Public report contains no raw endpoints, URLs, STOMP destinations, headers,
  payloads, fixture bodies, tokens, cookies, device/account/payment values or
  local paths.
- Report explicitly avoids claiming all `protocol` rows as TASK-031 coverage
  when DataChannel/gamepad rows remain TASK-032 out of scope.
- Tests cover clean synthetic pack/report, missing pack blocker, malformed
  protocol fixture JSON, invalid protocol fixture shape, unsafe fixture
  reference group, source summary mismatch, raw-public rejection,
  live-network/WebSocket overclaim rejection and CLI behavior.
- Multi-agent Planner, Builder, QA A, QA B, Security/Prod-safety and
  Docs/Scribe reviews complete without unresolved R0/R1 blockers.

## Verification

```text
git status --short --branch
git diff --check
python automation/api_layer_contract/validate_task031_stomp_protocol_contracts.py --pack-root .qa_local/api_layer_audit_20260706 --report docs/qa/reports/task031_stomp_protocol_contracts.summary.json
python -m pytest -q tests/test_task028_api_layer_contract.py tests/test_task036_api_layer_exhaustive_coverage.py tests/test_task029_rest_schema_fixture_contracts.py tests/test_task030_rest_negative_cache_sequences.py tests/test_task031_stomp_protocol_contracts.py
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

## Stop conditions

Stop and report a blocker if:

- implementation requires live API/backend/network/runtime/ADB/APK execution;
- implementation requires live STOMP/WebSocket/DataChannel connections;
- public output would include raw endpoints, URLs, STOMP destinations, headers,
  payloads, fixture bodies, tokens, cookies, device/account/payment values or
  local paths;
- local pack is absent and the task cannot return a controlled partial blocker;
- TASK-028/TASK-030/TASK-036 public summary reconciliation fails;
- protocol rows cannot be safely separated from DataChannel/gamepad rows;
- tests fail and cannot be fixed inside TASK-031 scope;
- QA or Security review reports unresolved R0/R1 risk.
