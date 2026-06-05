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
