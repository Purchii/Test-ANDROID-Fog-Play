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
