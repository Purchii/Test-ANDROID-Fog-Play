# API-layer import policy

## Scope

TASK-028 introduces a public-safe import policy for owner-provided API-layer
audit packs.

Allowed public artifacts:

- API/test aliases;
- matrix row counts;
- fixture and schema counts;
- layer/domain/test-type categories;
- evidence status;
- blocked/not-run live execution status;
- follow-up task decomposition.

Forbidden public artifacts:

- raw endpoints, URLs, hosts, paths or query values;
- headers, tokens, cookies, sessions or Authorization values;
- raw request/response payloads;
- raw fixture bodies;
- phone, OTP, captcha or account values;
- payment instruments, billing values, receipts or payment URLs;
- device identifiers;
- local machine paths or raw archive paths;
- executable curl/Postman/backend recipes.

## Evidence status

The API audit pack is a no-source QA artifact. TASK-028 may mark the pack
structure and offline coverage ledger as `likely` after local validation, but
it must not mark live API behavior as `confirmed`.

Live backend behavior, ACLs, authorization, payment/order/session mutation,
stream signaling and runtime correlation remain `unknown` until separate
approved evidence exists.

## Safety gates

Every API-layer task must keep these gates:

- no live network calls by default;
- no private endpoint publication;
- no secret/header/payload replay;
- no real payment/order/session mutation;
- no stream/session start;
- no Android runtime or APK action unless a separate runtime task approves it;
- raw pack and raw evidence stay in ignored local storage;
- public reports contain only aliases, counts and categories.

Any staging or QA backend execution requires a separate `PROD_CONDITIONAL`
task with approved environment aliases, synthetic user, resource budget,
cleanup/rollback, redaction, audit trail and QA/Security reviews.
