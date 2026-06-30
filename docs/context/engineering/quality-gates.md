# Quality gates

## Universal task gates

A task is done only when:

- fresh thread verified;
- mode declared;
- task branch used;
- strict multi-agent cycle completed;
- acceptance criteria met;
- relevant checks run or blocked with reason;
- diff reviewed;
- docs updated;
- final Russian report produced;
- next task handoff recorded.

## Docs-only gates

- Markdown files are readable and linked from source-of-truth docs.
- No secrets/private endpoints/PII/payment data introduced.
- No product facts copied from unrelated reference projects.
- Decisions and risks updated when workflow changes.
- Manual screen/focus map templates use public-safe aliases and never claim runtime behavior without approved evidence.

## Automation gates

- Tests handle missing device/APK/config gracefully.
- No hardcoded secrets/endpoints/package private data unless approved and redacted.
- Reports include app version/device/status/evidence_status/risk_level.
- Log/screenshot artifacts are redacted or stored in ignored local evidence paths.
- No destructive runtime or production commands by default.
- Screen/focus map report generators fail closed: absent prerequisites are `blocked`, template-only plans are `not_run`, and runtime facts remain `unknown`.
- Fixture contracts and approval checklists fail closed: absent, expired, revoked or non-confirmed fixture approvals keep dependent runtime tasks `blocked`.
- Payment-like fixture gates require staging-only, non-real-payment approval before execution.
- Network/offline safe runners fail closed: absent or non-confirmed profile, budget, redaction, evidence storage, cleanup or review prerequisites keep dependent tasks `blocked`.
- Compatibility/device matrix report generators fail closed: absent or non-confirmed build, target class, config, fixture, redaction, evidence storage, cleanup or review prerequisites keep compatibility execution `blocked`, and template-only matrix rows remain `not_run`/`unknown`.
- WebView/payment safe report generators fail closed: absent or non-confirmed WebView fixture policy, staging-only non-real-payment policy, synthetic user policy, resource budget, redaction, evidence storage, cleanup or review prerequisites keep dependent tasks `blocked`, and template-only planned checks remain `not_run`/`unknown`.
- CI/nightly smoke report generators fail closed: absent or non-confirmed static CI scope, schedule policy, repository safety policy, resource budget, redaction, evidence storage, artifact retention, dependency policy or review prerequisites keep CI/nightly execution `blocked`, and template-only planned checks remain `not_run`/`unknown`.
- Navigation transition map report generators fail closed: absent or non-confirmed build, target, config, navigation scope, screen alias policy, input event policy, fixture policy, resource budget, redaction, evidence storage, cleanup or review prerequisites keep transition execution `blocked`, and template-only transition rows remain `not_run`/`unknown`.
- Safe task prioritization and approval-dependency maps are planning-only: they may select public-safe docs/static work, but they must keep runtime/device/APK/WebView/WebRTC/payment/network/live CI tasks `blocked` until every required dependency is `present=true`, `evidence_status=confirmed` and reviewed.
- Next-task selection blocker and safe backlog refresh docs must not approve execution: proposed follow-up tasks may be selected only when they are public-safe, bounded, locally verifiable and require no user secrets, private endpoints, APK handling, device execution, real accounts, real payments or production interaction.
- Approval metadata validators must fail closed: missing/malformed/non-object metadata, missing required fields, non-approved or non-confirmed approvals, expired approvals, missing approver role, unsupported approver role, missing build/target aliases, missing structured targets, unsafe device aliases, phone-only TASK-005 target sets, invalid fixture statuses, non-out-of-scope current stream/WebView/payment fixtures, pending/blocked/invalid evidence policy, non-local ignored storage, unsupported runtime scope, forbidden runtime scope, raw phone/OTP, device identifiers, unknown cleanup levels, C5 cleanup without separate approval, and missing/pending reviews keep runtime approval `blocked`. A valid approval report may return only `approved_for_limited_runtime` with `runtime_execution_status=not_run`; it must not claim runtime pass.
- Final approval metadata validators must also block non-actionable P0 TV/STB targets, `adb_available` other than `yes`, heuristic/manual-review-required runtime targets, reserved alias tokens, `phone` outside the first form-factor segment of structured phone aliases, runtime profile alias prefix/index or Android-major mismatch, manual-confirmed TV/STB alias/form-factor mismatch, unsafe build alias tokens, empty or incomplete TASK-005 runtime scope, ambiguous auth mode, scope/evidence mismatch, raw-evidence public report policies, weak APK SHA-256 policy, incomplete APK allowed actions, forbidden build actions in `allowed_actions`, missing critical forbidden build actions and mismatched allowed/structured target categories.
- Final approval metadata validators must block unsafe synthetic QA user path metadata, IP-like approval values, unknown structured device fields, compound reserved build alias tokens and duplicate public approval list values.
- ADB device inventory preflight must be inventory-only: default execution makes no ADB calls and returns blocked/not-run; owner-approved `--allow-adb` may run only `adb devices -l`, safe getprop fields, `wm size`, `wm density` and `pm list features`; raw serial/IP data must stay under `.qa_local/devices/`; public-safe inventory must exclude raw identifiers and always report runtime/app statuses as `not_run`.
- ADB device inventory output paths must be validated before any ADB invocation and must remain under `.qa_local/devices/`.
- ADB device inventory must validate existing alias-map entries before using them in public-safe output. Unsafe persisted aliases block public inventory rather than being trusted. Secondary phone inventory aliases may use `phone-*` only when the structured form factor is `phone`; phone-only inventory never satisfies TASK-005 P0 TV/STB runtime readiness.
- TASK-015D/016C has a hard two-phase gate: Phase B inventory-only ADB is blocked until Phase A approval hardening passes. Generated inventory remains heuristic/manual-review-required and cannot satisfy TASK-005 runtime approval without separate owner/QA manual confirmation.
- Release gate reports must require `qa_reviewer_a`, `qa_reviewer_b`, `security_prod_safety_reviewer` and `docs_scribe` to be `approved` or `confirmed` before `release_decision=pass`, even when all R0/R1 gates are otherwise passing.
- Exported component guard reports must block when any required prerequisite has `present != true` or `evidence_status != confirmed`.

## Runtime Android gates

Runtime check can be marked passed only if:

- physical device or approved emulator was available;
- APK/config were available;
- command output was captured;
- screenshots/logs were collected and redacted;
- no crash/ANR evidence appeared;
- report names exact device/app version.

If device/APK/config missing, status is `blocked`, not `pass`.

## Fixture gates

Future runtime, auth/session, stream, WebView, payment, network and offline tasks may use fixtures only when:

- fixture approval is recorded with `evidence_status=confirmed`;
- owner roles, scope, allowed/disallowed flows, resource budget, redaction, evidence storage and cleanup/rollback are documented;
- credentials, private endpoints, real accounts, real payment data and raw evidence remain outside public source control;
- Security/Prod-safety and QA reviewers approve the fixture boundary;
- real payments, security bypasses and production mutation without cleanup remain forbidden.

## Network/offline gates

Future network/offline tasks may execute only when:

- approved build, Android TV target and runtime configuration are recorded with `evidence_status=confirmed`;
- network profile policy is approved using public-safe category aliases only;
- resource budget covers duration, retry, traffic, account and stream limits;
- Security/Prod-safety and QA reviewers approve the boundary before execution;
- evidence storage and redaction are approved before capture;
- cleanup or rollback restores normal connectivity and any mutable fixture state;
- public reports exclude endpoint values, packet captures, proxy setup, TLS bypass details, raw traffic/log evidence and executable device/network recipes.

TASK-007 local report generation is `PROD_SAFE`; real network/offline execution remains `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## Compatibility/device matrix gates

Future compatibility/device matrix execution may run only when:

- approved build, Android TV target class and runtime configuration are recorded with `evidence_status=confirmed`;
- approved device matrix policy uses public-safe category aliases only, never real serials or private lab identifiers;
- WebView, WebRTC, payment, network/offline and auth/session rows have confirmed fixture approvals before execution;
- Security/Prod-safety and QA reviewers approve the boundary before execution;
- evidence storage and redaction are approved before capture;
- cleanup or rollback is documented for any mutable fixture state;
- public reports exclude raw screenshots, logs, videos, APK paths, endpoint values, account identifiers and executable Android/device/runtime recipes.

TASK-009 local report generation is `PROD_SAFE`; real compatibility execution remains `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## WebView/payment gates

Future WebView/payment execution may run only when:

- approved build, Android TV target and runtime configuration are recorded with `evidence_status=confirmed`;
- approved WebView fixture policy uses public-safe aliases only, never private URLs, redirect chains, headers, payloads, cookies or endpoints;
- approved payment staging policy is staging-only, non-real-payment and excludes card, wallet, bank, billing token and receipt data from public reports;
- synthetic user/session boundaries are approved when account-bound WebView or payment-like paths are in scope;
- resource budget covers duration, retries, redirects, accounts and staging transaction attempts;
- Security/Prod-safety and QA reviewers approve the boundary before execution;
- evidence storage and redaction are approved before capture;
- cleanup or rollback is documented for sessions and staging transaction state;
- public reports exclude raw WebView logs, private redirect data, payment data, raw screenshots, APK paths, endpoint values and executable Android/device/runtime/network recipes.

TASK-008 local report generation is `PROD_SAFE`; real WebView/payment execution remains `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## CI/nightly smoke gates

Future CI/nightly execution may run only when:

- approved static CI scope, schedule policy and repository safety policy are recorded with `evidence_status=confirmed`;
- resource budget covers timeout, retry, concurrency, branch scope and runner limits;
- dependency policy excludes secret-backed private services unless separately approved and redacted;
- evidence storage and artifact retention are approved before any public artifact is published;
- Security/Prod-safety and QA reviewers approve the boundary before live scheduling;
- runtime/device/APK/WebView/WebRTC/payment/network lanes remain disabled unless their own approved prerequisites are confirmed;
- public reports exclude CI secrets, private runner credentials, raw logs, raw screenshots, APK paths, endpoint values, account identifiers, payment values and executable Android/device/runtime recipes.

TASK-010 local report generation is `PROD_SAFE`; live CI scheduling and runtime lanes remain `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## Navigation transition gates

Future navigation transition execution may run only when:

- approved build, Android TV target and runtime configuration are recorded with `evidence_status=confirmed`;
- transition scope uses public-safe screen and action category aliases only, never private routes, deeplinks, package/class names or endpoint values;
- resource budget covers duration, retry, account/session, stream and Back/Home traversal limits;
- Security/Prod-safety and QA reviewers approve the boundary before execution;
- evidence storage and redaction are approved before capture;
- cleanup or rollback is documented for any mutable session, stream, WebView or account state;
- public reports exclude raw screenshots, logs, videos, APK paths, endpoint values, account identifiers, payment values, raw route/deeplink values and executable Android/device/runtime recipes.

TASK-011 local report generation is `PROD_SAFE`; real navigation transition execution remains `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## Safe task prioritization gates

Future autonomous task selection may proceed only when:

- the candidate task is in `docs/tasks/backlog.md` or explicitly requested by the user;
- scope, branch, acceptance criteria and verification are bounded;
- the task is public-safe docs/static/fail-closed work, or all conditional execution dependencies are confirmed;
- approval dependencies are category-level only and exclude private values, raw evidence, APK paths, endpoints, credentials, account identifiers, payment values and executable runtime recipes;
- strict multi-agent Planner, QA and Security review is available;
- no R0/R1 blocker remains.

TASK-012 documentation is `PROD_SAFE`; it does not approve runtime/device/APK/WebView/WebRTC/payment/network/live CI execution.

## Safe backlog refresh gates

Future autonomous selection from refreshed backlog entries may proceed only when:

- the candidate task is explicitly listed as `proposed` in `docs/tasks/backlog.md` or explicitly requested by the user;
- the task specification can be created using public-safe category-level content only;
- the task is docs/static/local-only or fail-closed local tooling;
- no approved build, APK, target, runtime configuration, fixture, secret, private endpoint, account, payment data, raw evidence or live CI access is required;
- strict multi-agent Planner, QA, Security/Prod-safety and Docs/Scribe review is available;
- TASK-005 and runtime-dependent tasks remain blocked unless their approval dependencies are confirmed.

TASK-013 documentation is `PROD_SAFE`; it only records a selection blocker and proposed public-safe backlog. It does not approve runtime/device/APK/WebView/WebRTC/payment/network/live CI execution.

## Approval metadata gates

Future TASK-005 limited runtime smoke may be considered only after:

- approval metadata validates as `approved_for_limited_runtime`;
- approval evidence is `confirmed` and unexpired;
- approved build is represented by a public-safe alias and local ignored `.qa_local/` path pattern;
- approved targets use public-safe aliases only;
- approved runtime targets include at least one manually confirmed P0 Android TV/STB D-pad target with ADB available and manual review no longer required;
- evidence capture policy is explicit and non-pending;
- raw storage policy is local ignored storage;
- cleanup/rollback levels exclude C5 unless separately approved;
- stream, WebView and payment fixtures remain out of scope unless separately approved;
- required QA, Security/Prod-safety and Docs reviews are approved or confirmed.

TASK-015 validation is `PROD_SAFE`; Android runtime execution remains `PROD_CONDITIONAL` and blocked until a separate task executes under confirmed approvals.

## ADB device inventory preflight gates

For TASK-015D/016C, Phase B inventory-only ADB is additionally blocked until
the Phase A approval-hardening gate passes.

TASK-016 local ADB inventory may run only after owner approval and only through
the preflight allowlist. It must not install, launch, start activities, use
monkey, collect logcat, capture screenshots/videos, run WebView/WebRTC/payment
flows, mutate accounts/profiles or modify APKs.

Generated local raw files must remain ignored under `.qa_local/devices/`:

```text
.qa_local/devices/raw_adb_devices.json
.qa_local/devices/serial_alias_map.json
.qa_local/devices/preflight_report.json
```

Generated public-safe inventory remains ignored until manually reviewed:

```text
.qa_local/devices/device_inventory.public_safe.generated.json
```

TASK-016 inventory evidence can confirm only device/build inventory collection,
alias generation and redaction. It cannot confirm APK install, app launch,
runtime smoke, WebView, WebRTC, payment or navigation behavior.

## Merge gates

To merge/push default branch in `BOUNDED_AUTONOMOUS`:

- all relevant checks pass;
- QA Reviewer A approves;
- QA Reviewer B approves;
- Security/Prod-safety Reviewer approves;
- Docs/Scribe confirms docs updated;
- no R0/R1 blocker remains;
- git status clean except intended changes;
- no force-push needed.

Before starting the next independent task in autonomous continuation:

- the completed task branch must be merged into the detected default/trunk branch;
- the detected default/trunk branch must be pushed to origin;
- post-push verification must confirm local HEAD and `origin/<default-branch>` are aligned;
- if this cannot be verified, record a blocker and do not start the next task.
