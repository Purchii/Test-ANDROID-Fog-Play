# TASK-029 - REST schema and fixture contract harness

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

`TASK-029 - REST schema and fixture contract harness`

## Branch

`qa/task-029-rest-schema-fixture-contracts`

## Production safety classification

`PROD_SAFE_OFFLINE_WITH_LOCAL_QUARANTINE_INPUT`

TASK-029 is offline/local only. It may read the ignored API-layer quarantine
pack to validate REST matrix rows, REST fixture JSON files and REST schema
shapes. It must not make live REST/backend calls, WebSocket/STOMP/DataChannel
connections, Android runtime/ADB/APK actions, auth/session/token replay,
payment/order/session mutation, endpoint discovery/publication or executable
API recipes.

## Context

TASK-028 created the first public-safe API-layer contract intake from the
ignored local API audit pack. TASK-036 added an aggregate guard over TASK-028
and recorded that pack-backed per-row parametrization was blocked when the
local quarantine pack was absent in that worktree.

TASK-029 narrows that aggregate follow-up into a concrete REST schema/fixture
contract harness. It does not replace TASK-030 cache/state-sequence work or
TASK-034 optional approved staging/live execution.

## Scope

In scope:

- validate tracked TASK-028 and TASK-036 public summaries fail-closed;
- validate REST matrix rows from the local quarantine pack when present;
- validate REST fixture references stay inside allowed pack fixture groups;
- validate REST fixture JSON readability;
- validate REST schema JSON shape at required-key/category level;
- emit a public-safe TASK-029 report with aliases, counts, categories, statuses
  and blockers only;
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

- TASK-029 active-run metadata, task spec, backlog entry and public report
  exist.
- Validator returns `pass` for the present local quarantine pack while keeping
  runtime/live/network statuses `not_run`.
- Missing local pack returns controlled `partial_blocked` with
  `blocked_missing_local_quarantine_pack`, not product evidence.
- Public report contains no raw endpoints, URLs, headers, payloads, fixture
  bodies, tokens, cookies, device/account/payment values or local paths.
- Tests cover clean synthetic pack/report, missing pack blocker, malformed REST
  schema/fixture/reference failures, raw-public rejection, live-network
  overclaim rejection and CLI behavior.
- Multi-agent Planner, Builder, QA A, QA B, Security/Prod-safety and
  Docs/Scribe reviews complete without unresolved R0/R1 blockers.

## Verification

```text
git status --short --branch
git diff --check
python automation/api_layer_contract/validate_task029_rest_schema_fixture_contracts.py --pack-root .qa_local/api_layer_audit_20260706 --report docs/qa/reports/task029_rest_schema_fixture_contracts.summary.json
python -m pytest -q tests/test_task028_api_layer_contract.py tests/test_task036_api_layer_exhaustive_coverage.py tests/test_task029_rest_schema_fixture_contracts.py
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
- TASK-028/TASK-036 public summary reconciliation fails;
- tests fail and cannot be fixed inside TASK-029 scope;
- QA or Security review reports unresolved R0/R1 risk.
