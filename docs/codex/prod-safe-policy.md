# Production-safe policy

## Classification

Every command/test/action must be classified:

- `PROD_SAFE`;
- `PROD_CONDITIONAL`;
- `PROD_FORBIDDEN`.

## PROD_SAFE

Examples:

- reading repository docs;
- editing local docs/tests/scripts;
- local unit tests;
- static checks;
- local redaction tests;
- no-op report generation;
- public-safe docs bootstrap that excludes raw artifacts and executable runtime recipes.

## PROD_CONDITIONAL

Examples:

- production-signed APK runtime smoke;
- approved QA account login;
- staging payment flow;
- network shaping;
- collecting logs that may include sensitive-looking data;
- contract tests against approved QA/staging endpoints.

Required conditions:

- synthetic/test user;
- approved environment;
- resource budget;
- no real payment/user mutation;
- cleanup plan;
- rollback/kill switch when applicable;
- redaction;
- audit trail.

## PROD_FORBIDDEN

Forbidden:

- destructive production writes;
- real payment without explicit approval;
- load tests without budget;
- secret/token/private endpoint extraction;
- TLS/pinning/security bypass;
- APK patching;
- mutating real user/payment state;
- tests without cleanup for mutable flows.
- committing raw APK dumps, compiled cache files, endpoint inventories or executable device command recipes to a public repository, except the exact owner-approved TASK-016 ADB inventory allowlist documented for local preflight.

## Public repository rule

Public source-of-truth docs may describe approved runtime categories, prerequisites and safety gates. They must not publish direct device command recipes, raw dumps, compiled artifacts, secrets, real endpoints or low-level private evidence, except the narrow TASK-016 local ADB inventory allowlist after owner approval. Runtime/app/device recipes outside that allowlist remain forbidden.

## Stop rule

If Codex cannot classify an action confidently as `PROD_SAFE`, it must treat it as at least `PROD_CONDITIONAL` and ask before execution unless conditions are already documented.
