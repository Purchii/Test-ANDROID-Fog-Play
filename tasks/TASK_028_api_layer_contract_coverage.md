# TASK-028 - API-layer contract coverage from quarantined audit pack

## Mode

`NON_AUTONOMOUS`

## Production safety classification

`PROD_SAFE_OFFLINE_WITH_LOCAL_QUARANTINE_INPUT`

TASK-028 reads the owner-provided API audit pack only from ignored local
quarantine storage and emits public-safe counts, aliases and coverage
categories. It does not run live REST, WebSocket, STOMP, DataChannel, Android
runtime, APK, payment, stream/session, account or production actions.

## Objective

Build the first real executable API-layer autotest foundation from the API
audit pack:

- validate the pack shape;
- validate matrix-to-fixture/sequence references;
- validate JSON readability of schema and fixture files;
- produce a public-safe coverage ledger;
- define the next rollback-sized API coverage tasks.

In TASK-028, `exhaustive` means every known matrix row, fixture reference,
fixture JSON file and schema JSON file in the quarantined pack is accounted for.
It does not mean live backend/API behavior is exhaustively verified.

## Inputs

Local-only owner-provided archive:

```text
api-layer-audit-pack-20260706
```

Raw archive contents and extracted files remain under ignored local storage.
Public reports may record only derived aliases, counts and category-level
status.

## In scope

- Local pack validation.
- Offline contract coverage summary.
- Fail-closed CLI and pytest tests.
- Public-safe source-of-truth updates.
- Follow-up decomposition for REST, sequences, protocol, DataChannel/gamepad,
  redaction/security and optional staging execution.

## Out of scope

- Live REST/backend calls.
- WebSocket/STOMP/DataChannel live connections.
- Endpoint extraction or endpoint publication.
- Auth with real user data.
- Token/cookie/session/header replay.
- Real order, payment method, payment, stream or session mutation.
- Android device/APK/runtime execution.
- TLS/pinning/security bypass.
- APK patching/decompilation/source-code use.

## Implementation

Added:

- `automation/api_layer_contract/validate_task028_api_layer_contract.py`;
- `tests/test_task028_api_layer_contract.py`;
- `docs/qa/reports/task028_api_layer_contract_coverage.summary.json`;
- `docs/qa/api-layer/api-layer-import-policy.md`;
- `docs/qa/api-layer/api-layer-coverage-plan.md`.

The validator accepts an extracted local pack root and writes a public-safe JSON
summary:

```text
python automation/api_layer_contract/validate_task028_api_layer_contract.py --pack-root <ignored-local-pack-root> --report docs/qa/reports/task028_api_layer_contract_coverage.summary.json
```

## Result

The quarantined pack validated successfully for offline intake:

- matrix rows: `217`;
- fixture/sequence refs: `217`;
- fixture JSON files: `214`;
- schema JSON files: `21`;
- inventory items: `67`;
- missing fixture references: `0`;
- live API execution: `not_run`;
- runtime execution: `not_run`.

Raw-value signals were detected in local quarantine, so raw pack content must
remain local-only. The committed report contains no raw endpoints, URLs,
headers, payloads, fixture bodies, tokens, phone/OTP/captcha values, payment
values, device identifiers or local machine paths.

## Follow-up tasks

- `TASK-029` - REST schema and fixture contract harness.
- `TASK-030` - REST negative, cache and state-sequence contract tests.
- `TASK-031` - STOMP signaling and device protocol contract tests.
- `TASK-032` - DataChannel and gamepad protocol contract tests.
- `TASK-033` - API-layer redaction and production-safety guard tests.
- `TASK-034` - Optional approved staging API execution gate.

`TASK-034` is `PROD_CONDITIONAL` and requires explicit staging/QA environment,
synthetic user, resource budget, cleanup/rollback, audit trail, redaction and
QA/Security approval before any live API execution.

## Verification

Required TASK-028 checks:

```text
git status --short --branch
git diff --check
python automation/api_layer_contract/validate_task028_api_layer_contract.py --pack-root .qa_local/api_layer_audit_20260706 --report docs/qa/reports/task028_api_layer_contract_coverage.summary.json
python -m pytest -q tests/test_task028_api_layer_contract.py
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```
