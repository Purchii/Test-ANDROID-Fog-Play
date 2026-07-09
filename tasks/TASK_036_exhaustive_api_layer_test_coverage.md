# TASK-036 - Exhaustive API-layer test coverage and exploratory evidence intake

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

`TASK-036 - Exhaustive API-layer test coverage and exploratory evidence intake`

## Branch

`qa/task-036-exhaustive-api-layer-test-coverage`

## Production safety classification

`PROD_SAFE_OFFLINE_STATIC_AND_SYNTHETIC_ONLY`

Any live REST/backend, WebSocket/STOMP, DataChannel/WebRTC, Android runtime,
ADB, APK, network capture/proxy, payment/order/session or stream action is
`PROD_CONDITIONAL` and out of this task unless a separate approved execution
task records all prerequisites.

## Context

TASK-028 created the first offline API-layer contract intake from an
owner-provided local quarantined API audit pack. TASK-028 validated:

- `217` matrix rows;
- `213` ready or fixture-only rows;
- `4` runtime-optional deferred rows;
- `214` fixture JSON files;
- `21` schema JSON files;
- `67` inventory items;
- `0` missing fixture references.

TASK-036 aggregates the TASK-029 through TASK-033 offline follow-up scope into a
single public-safe exhaustiveness guard. It does not replace the need for a
separate TASK-034-style live/staging execution task.

## Scope

In scope:

- validate the tracked TASK-028 public-safe summary fail-closed;
- account for all currently known API-layer categories by aliases, counts and
  test classes;
- support optional local quarantine pack cross-check when the pack exists;
- record missing pack-backed parametrization as a blocker without publishing
  raw pack data;
- define a fail-closed exploratory evidence intake gate for unknown live API
  behavior;
- add synthetic/local pytest coverage for pass and fail-closed cases.

## Out of scope

- live REST/backend calls;
- live WebSocket/STOMP/DataChannel connections;
- Android runtime, ADB, APK install/launch, network capture or proxying;
- endpoint discovery, endpoint publication or executable API recipes;
- auth header/cookie/session/token replay;
- real user data, payment/order/session mutation or stream/session start;
- TLS/pinning bypass, APK modification, decompilation, smali or app source
  code use;
- raw endpoint, URL, header, payload, fixture body, token, payment, device
  identifier or local path publication.

## Acceptance criteria

- TASK-036 active-run metadata, task spec and backlog entry exist.
- Validator checks TASK-028 summary arithmetic: count totals, fixture/schema
  group totals, status totals, follow-up task coverage and public safety flags.
- Public TASK-036 summary records known coverage areas and exact blockers using
  aliases/counts/categories/statuses only.
- Missing local quarantine pack is reported as
  `blocked_missing_local_quarantine_pack`, not as product evidence.
- Live exploratory intake is blocked until staging/test backend, synthetic user,
  budget/rate limits, cleanup/rollback, kill switch, local-only raw storage,
  redaction and QA/Security approvals are confirmed.
- Unit tests cover clean summary validation, missing pack blocker, pack
  cross-check pass, inconsistent count blocker, live network claim rejection,
  raw API-like text rejection and CLI behavior.

## Verification

```text
git status --short --branch
git diff --check
python automation/api_layer_contract/validate_task036_api_layer_exhaustive_coverage.py --task028-report docs/qa/reports/task028_api_layer_contract_coverage.summary.json --pack-root .qa_local/api_layer_audit_20260706 --report docs/qa/reports/task036_api_layer_exhaustive_coverage.summary.json
python -m pytest -q tests/test_task028_api_layer_contract.py tests/test_task036_api_layer_exhaustive_coverage.py
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

The pack-root validator invocation is expected to produce
`partial_blocked` in this worktree when the ignored local quarantine pack is
absent. That is an accepted task result as long as tracked summary validation
passes and no live/API/runtime behavior is overclaimed.

## Documentation updates

- `docs/context/handoff/active-run.md`;
- `docs/tasks/backlog.md`;
- `docs/context/current-state.md`;
- `docs/context/engineering/quality-gates.md`;
- `docs/context/engineering/verification-memory.md`;
- `docs/context/governance/risk-register.md`;
- `docs/qa/api-layer/api-layer-coverage-plan.md`;
- `docs/qa/reports/task036_api_layer_exhaustive_coverage.summary.json`.

## Stop conditions

Stop and report a blocker if:

- local implementation requires live API/backend/network/runtime/ADB/APK
  execution;
- public output would include raw endpoints, URLs, headers, payloads, fixture
  bodies, tokens, payment values, device identifiers or local paths;
- TASK-028 summary arithmetic or safety invariants fail;
- tests fail and cannot be fixed inside this task scope;
- QA or Security review reports unresolved R0/R1 risk.
