# API-layer coverage plan

## TASK-028 baseline

TASK-028 creates the first executable offline API-layer coverage harness. It
validates the quarantined audit pack and records this public-safe baseline:

| Area | Count |
|---|---:|
| Matrix rows | 217 |
| REST rows | 132 |
| Protocol rows | 61 |
| State-machine sequence rows | 12 |
| Security/redaction rows | 8 |
| Runtime-optional deferred rows | 4 |
| Fixture JSON files | 214 |
| Schema JSON files | 21 |
| Inventory items | 67 |

Coverage status:

- offline matrix/fixture/schema intake: `pass`;
- live API execution: `not_run`;
- Android runtime correlation: `not_run`;
- backend behavior evidence: `unknown`.

## Follow-up implementation sequence

1. `TASK-029` - REST schema and fixture contract harness.
2. `TASK-030` - REST negative, cache and state-sequence contract tests.
3. `TASK-031` - STOMP signaling and device protocol contract tests.
4. `TASK-032` - DataChannel and gamepad protocol contract tests.
5. `TASK-033` - API-layer redaction and production-safety guard tests.
6. `TASK-034` - optional approved staging API execution gate.

`TASK-029` through `TASK-033` are offline and `PROD_SAFE`. They should generate
parametrized tests from aliases and local quarantined fixtures without making
network calls or publishing raw payloads.

`TASK-034` is `PROD_CONDITIONAL`. It may start only after explicit approval for
a staging/QA environment, synthetic user, resource budget, cleanup/rollback,
audit trail, redaction and reviewer sign-off.

## TASK-036 aggregate offline guard

TASK-036 aggregates the TASK-029 through TASK-033 offline follow-up scope into a
single public-safe exhaustiveness validator over the tracked TASK-028 summary.
It validates count arithmetic, follow-up coverage classes, public-safety flags
and the fail-closed exploratory intake gate.

Current TASK-036 result:

- tracked TASK-028 summary validation: `pass`;
- local quarantine pack cross-check: `blocked_missing_local_quarantine_pack`
  in the current worktree;
- live API/backend/runtime exploration: `not_run` and blocked until
  TASK-034-style `PROD_CONDITIONAL` prerequisites are confirmed.

TASK-036 does not publish raw pack contents and does not claim live API
behavior. Pack-backed per-row parametrization remains blocked until the
approved ignored local quarantine pack is present in the active worktree.

## TASK-029 REST schema/fixture harness

TASK-029 implements the first concrete REST follow-up from the TASK-028 API
audit chain. It validates the tracked TASK-028/TASK-036 summaries and, when the
ignored local quarantine pack is present, checks REST matrix rows, REST fixture
references, REST fixture JSON readability, REST schema shape and public-safety
boundaries.

Current TASK-029 result:

- tracked TASK-028/TASK-036 summary reconciliation: `pass`;
- local quarantine pack REST contract validation: `pass`;
- known REST matrix rows: `132`;
- REST contract rows checked through fixture/schema-oriented targets: `71`;
- REST schema JSON files: `17`;
- live REST/backend/runtime/network execution: `not_run`;
- raw pack signal categories are counted only and raw values remain local-only.

TASK-029 does not validate live backend behavior, real authorization/ACL,
payment/order/session mutation behavior, Android runtime correlation or real
cache behavior against a backend. TASK-030 remains the planned offline mocked
REST negative/cache/state-sequence follow-up.

## Assertions policy

Offline API tests should assert:

- schema shape and required field categories;
- positive fixture validity;
- malformed/negative fixture rejection;
- cache and sequence state transitions in mocked transport;
- protocol message category validity;
- fail-closed behavior for unknown, malformed or missing fields;
- redaction of API, payment, device, session and protocol evidence classes.

Offline API tests must not assert:

- fixed private endpoint values;
- fixed live response values;
- real account/payment/order/session data;
- backend availability;
- production authorization behavior;
- complete live API surface coverage.
