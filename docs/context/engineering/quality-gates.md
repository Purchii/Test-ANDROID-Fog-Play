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
