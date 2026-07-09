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

## TASK-030 REST negative/cache/state-sequence harness

TASK-030 implements the next REST follow-up from the TASK-028/TASK-029 API
audit chain. It validates tracked TASK-028/TASK-029/TASK-036 summaries and,
when the ignored local quarantine pack is present, checks mocked-transport REST
negative rows, cache behavior rows and state-sequence fixture shapes.

Current TASK-030 result:

- tracked TASK-028/TASK-029/TASK-036 summary reconciliation: `pass`;
- local quarantine pack mocked-transport validation: `pass`;
- TASK-030 matrix rows checked: `73`;
- mocked HTTP rows: `51`;
- mocked sequence rows: `22`;
- cache behavior rows: `10`;
- state-machine sequence rows: `12`;
- live REST/backend/runtime/network execution: `not_run`;
- raw pack fixture values remain local-only.

TASK-030 does not validate live backend behavior, real authorization/ACL,
payment/order/session mutation behavior, Android runtime correlation or real
backend cache/state behavior. TASK-031, TASK-032 and TASK-033 remain the planned
offline protocol/datachannel/redaction follow-ups; TASK-034 remains the optional
approved staging/live execution gate.

## TASK-031 STOMP signaling and device protocol harness

TASK-031 implements the next protocol follow-up from the TASK-028/TASK-036 API
audit chain. It validates tracked TASK-028/TASK-030/TASK-036 summaries and,
when the ignored local quarantine pack is present, checks only
`stomp_signaling` and `stomp_device` protocol fixture references and JSON
shapes.

Current TASK-031 local result:

- tracked TASK-028/TASK-030/TASK-036 summary reconciliation: `pass`;
- local quarantine pack STOMP/device protocol fixture validation: `pass`;
- TASK-031 matrix rows checked: `36`;
- `stomp_signaling` rows: `17`;
- `stomp_device` rows: `19`;
- protocol negative rows checked in TASK-031 scope: `12`;
- protocol sequence-or-fixture rows checked in TASK-031 scope: `5`;
- DataChannel/gamepad protocol rows are explicitly reserved for TASK-032:
  `26`;
- live STOMP/WebSocket/backend/runtime/network execution: `not_run`;
- raw pack fixture values remain local-only.

TASK-031 does not validate live STOMP/WebSocket behavior, backend subscription
routing or delivery, real device pairing behavior, backend authorization/ACL,
Android runtime correlation or DataChannel/gamepad behavior.

## TASK-032 DataChannel and gamepad protocol harness

TASK-032 implements the next protocol follow-up from the TASK-028/TASK-036 API
audit chain. It validates tracked TASK-028/TASK-031/TASK-036 summaries and,
when the ignored local quarantine pack is present, checks only `datachannel`
and `gamepad` protocol fixture references and JSON shapes.

Current TASK-032 local result:

- tracked TASK-028/TASK-031/TASK-036 summary reconciliation: `pass`;
- local quarantine pack DataChannel/gamepad fixture validation: `pass`;
- TASK-032 matrix rows checked: `26`;
- `datachannel` rows: `25`;
- `gamepad` rows: `1`;
- protocol negative rows checked in TASK-032 scope: `6`;
- fixture references checked in TASK-032 scope: `26`;
- live WebRTC/DataChannel/backend/runtime/network execution: `not_run`;
- live controller input or Android runtime behavior: `not_run`;
- raw pack fixture values remain local-only.

TASK-032 does not validate live WebRTC/DataChannel behavior, backend data
delivery, real gamepad/controller input behavior, backend authorization/ACL or
Android runtime correlation.

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
