# TASK-037 - Production bounded API/runtime exploratory coverage

## Mode

`BOUNDED_AUTONOMOUS`

## Thread title

`TASK-037 - Production bounded API/runtime exploratory coverage with read-only/live safe lane`

## Branch

`qa/task-037-production-api-runtime-exploratory-coverage`

## Production safety classification

`PROD_CONDITIONAL_LIVE_READ_ONLY_SAFE_LANE`

The owner explicitly approved a bounded production safe lane for TASK-037.
Every live action remains conditional and must stay inside the recorded
read-only scope, with concurrency `1`, retry cap `3`, minimal requests and
local-only raw evidence.

## Context

TASK-028 validated the offline API-layer audit pack and left live REST,
STOMP/WebSocket, DataChannel/WebRTC, backend authorization and Android runtime
correlation as `not_run`/`unknown`.

TASK-036 added an exhaustive offline/static guard over the tracked TASK-028
public summary and a fail-closed exploratory intake gate. TASK-037 is the
separate owner-approved live/read-only runtime/API task for the safe lane
described in the current handoff.

## Scope

In scope:

- record the owner safe-lane passport and reviewer gates before live action;
- preflight ignored local evidence storage without publishing local paths;
- preflight synthetic secret material presence without printing values;
- preflight the owner-approved runtime target by public-safe alias only;
- collect bounded read-only API/runtime evidence for allowed categories when
  gates pass;
- summarize public coverage using only aliases, counts, categories, statuses,
  evidence ids and blockers;
- record boundaries as `blocked_by_boundary` and recover safely;
- record anomalies immediately.

Allowed API categories:

- config;
- catalog;
- reference dictionaries;
- available statuses;
- synthetic-user profile/status;
- synthetic-user entitlement/status;
- synthetic auth/session bootstrap or refresh.

Allowed runtime categories:

- app launch or relaunch;
- current screen alias;
- screenshot/XML checkpoint category;
- bounded log-snippet/crash check;
- boundary recovery.

## Out of scope

- stream start or paid/free session activation;
- order creation or order changes;
- payment, checkout, payment QR follow/open/confirmation or external payment
  navigation;
- profile/account mutation;
- device binding mutation;
- destructive, revoke, update or delete operations;
- load/fuzz testing or concurrency above `1`;
- endpoint discovery/publication beyond public-safe category aliases;
- raw endpoint/header/token/cookie/payload/QR/device/local-path publication;
- APK patching/modification, decompilation, smali/method body/source use;
- TLS/pinning/security bypass.

## Acceptance criteria

- TASK-037 active-run metadata, task spec, backlog entry, public report and
  validator exist.
- Security/Prod-safety pre-execution review is recorded as `GO_CONDITIONAL`.
- Preflight confirms or blocks synthetic secrets, target, local-only evidence
  storage, redaction policy and forbidden-action guard without printing raw
  values.
- Live/read-only coverage, if executed, stays inside the allowed categories and
  records request counts, retry counts and mutation flags.
- Public report fails closed on raw/private evidence-like text, mutation
  overclaims, boundary action execution, budget drift, missing preflight fields
  and unsupported categories.
- Raw evidence remains ignored and uncommitted.
- Verification and multi-agent reviews pass before merge/push.

## Verification

```text
git status --short --branch
git diff --check
python automation/api_layer_contract/validate_task037_production_api_runtime_report.py --report docs/qa/reports/task037_production_api_runtime_exploratory.summary.json
python -m pytest -q tests/test_task037_production_api_runtime_report.py
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

Runtime/live preflight and execution evidence is local-only. Public docs must
not include executable private API/device recipes.

## Documentation updates

- `docs/context/handoff/active-run.md`;
- `docs/tasks/backlog.md`;
- `docs/context/current-state.md`;
- `docs/context/engineering/quality-gates.md`;
- `docs/context/engineering/verification-memory.md`;
- `docs/context/governance/risk-register.md`;
- `docs/qa/reports/task037_production_api_runtime_exploratory.summary.json`.

## Stop conditions

Stop and report a blocker if:

- local synthetic secret preflight is missing or would require value printing;
- target selection is ambiguous or outside the approved TASK-037 lane;
- any action would mutate profile, account, device binding, payment, order,
  stream/session or backend state;
- captcha, anti-abuse, account lock, suspicious activity or rate-limit signals
  appear;
- concurrency `1`, retry cap `3` or minimal request budget cannot be enforced;
- raw endpoint/header/token/cookie/payload/QR/device/local-path data would enter
  tracked output;
- tests fail and cannot be fixed inside TASK-037 scope;
- QA or Security review reports unresolved R0/R1 risk.
