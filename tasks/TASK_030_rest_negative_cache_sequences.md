# TASK-030 - REST negative, cache and state-sequence contract tests

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

`TASK-030 - REST negative, cache and state-sequence contract tests`

## Branch

`qa/task-030-rest-negative-cache-sequences`

## Production safety classification

`PROD_SAFE_OFFLINE_WITH_LOCAL_QUARANTINE_INPUT`

TASK-030 is offline/local only. It may read the ignored API-layer quarantine
pack to validate REST negative, cache and state-sequence rows using mocked
transport fixtures. It must not make live REST/backend calls, auth/token/header
replay, WebSocket/STOMP/DataChannel connections, Android runtime/ADB/APK
actions, endpoint discovery/publication, payment/order/session mutation or
executable API recipes.

## Context

TASK-028 created the API-layer offline intake. TASK-029 validated REST
schema/fixture contracts and left real backend cache/state behavior as
`not_run`/`unknown`.

TASK-030 narrows the next REST follow-up into offline mocked-transport
contracts for negative responses, cache behavior and state-sequence fixtures.
It does not replace TASK-031/TASK-032 protocol work, TASK-033 redaction guard
work or TASK-034 optional approved staging/live execution.

## Scope

In scope:

- validate tracked TASK-028, TASK-029 and TASK-036 public summaries
  fail-closed;
- validate TASK-030 rows from the ignored local quarantine pack when present;
- validate mocked REST negative fixture references stay under allowed fixture
  groups;
- validate state/cache sequence fixtures have sequence-like JSON shape;
- emit a public-safe TASK-030 report with aliases, counts, categories,
  statuses and blockers only;
- add synthetic pytest coverage for pass and fail-closed cases.

## Out of scope

- live REST/backend calls;
- auth header/cookie/session/token replay;
- endpoint discovery, endpoint publication or executable API recipes;
- WebSocket/STOMP/DataChannel live connections;
- Android runtime, ADB, APK read/hash/install/launch or modification;
- network capture/proxying;
- real user, account, payment, order, profile or session mutation data;
- TLS/pinning bypass, APK modification, decompilation, smali or app source use.

## Acceptance criteria

- TASK-030 active-run metadata, task spec, backlog entry and public report
  exist.
- Validator returns `pass` for the present local quarantine pack while keeping
  runtime/live/network statuses `not_run`.
- Missing local pack returns controlled `partial_blocked` with
  `blocked_missing_local_quarantine_pack`, not product evidence.
- Public report contains no raw endpoints, URLs, headers, payloads, fixture
  bodies, tokens, cookies, device/account/payment values or local paths.
- Tests cover clean synthetic pack/report, missing pack blocker, malformed
  mocked fixture JSON, invalid sequence fixture shape, unsafe fixture reference
  group, source summary mismatch, raw-public rejection, live-network overclaim
  rejection and CLI behavior.
- Multi-agent Planner, Builder, QA A, QA B, Security/Prod-safety and
  Docs/Scribe reviews complete without unresolved R0/R1 blockers.

## Verification

```text
git status --short --branch
git diff --check
python automation/api_layer_contract/validate_task030_rest_negative_cache_sequences.py --pack-root .qa_local/api_layer_audit_20260706 --report docs/qa/reports/task030_rest_negative_cache_sequences.summary.json
python -m pytest -q tests/test_task028_api_layer_contract.py tests/test_task036_api_layer_exhaustive_coverage.py tests/test_task029_rest_schema_fixture_contracts.py tests/test_task030_rest_negative_cache_sequences.py
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

## Stop conditions

Stop and report a blocker if:

- implementation requires live API/backend/network/runtime/ADB/APK execution;
- public output would include raw endpoints, URLs, headers, payloads, fixture
  bodies, tokens, cookies, device/account/payment values or local paths;
- local pack is absent and the task cannot return a controlled partial blocker;
- TASK-028/TASK-029/TASK-036 public summary reconciliation fails;
- tests fail and cannot be fixed inside TASK-030 scope;
- QA or Security review reports unresolved R0/R1 risk.
