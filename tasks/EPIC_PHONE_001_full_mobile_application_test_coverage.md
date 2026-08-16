# EPIC-PHONE-001 — Full mobile application test coverage

## Mode, scope and terminal result

- Mode: `BOUNDED_AUTONOMOUS`.
- Branch: `qa/epic-phone-001-full-mobile-application-test-coverage`.
- Repository planning, harness, ledgers and validation: `PROD_SAFE_REPOSITORY_ONLY`.
- Runtime and device actions: `PROD_CONDITIONAL`, currently blocked.
- Authentication or credential entry: `PROD_CONDITIONAL`, currently blocked.
- Security verdict: `GO_REPOSITORY_PLAN/BLOCK_RUNTIME/BLOCK_AUTH_ENTRY`.
- Terminal baseline: `closed_by_ledger`, `partial_blocked`, `blocks_release`.

The former TASK-059, TASK-060, TASK-061 and TASK-062 objectives are internal
stages of this single epic. They are not independent tasks, threads or
branches. Completed TASK-058/TASK-058A history is immutable. TASK-058A consumed
the clean-first-launch state and closed with readiness 6/7; readiness row 03 is
still `unknown` and the owner override is not reusable as normal runtime
authority.

## Current fail-closed authority decision

The owner stated that phone-number and OTP fixture values are available, but
the tracked authority does not classify them as fully synthetic/test-only.
Values are neither requested nor accessed. Credential entry remains blocked.
No literal runtime GO exists for this epic. Repository work may close with a
terminal blocked ledger; product coverage and release readiness may not pass.

Authentication can be reconsidered only after an explicit owner/team statement
classifies the exact local fixture alias as synthetic/test-only, not a real
user, approved for the exact app/environment, and incapable of real billing or
entitlement impact. That statement must also provide a task/run alias, TTL and
allowed/forbidden mutation scope; values themselves remain local-only and
redacted. Task/run-bound synthetic-session and evidence/retention/cleanup
passports plus a controller dry-run are also prerequisites.

Every materially different conditional action contour requires a fresh exact
Security plan and a literal runtime GO. The epic harness cannot issue either.

## Internal stages

1. Epic authority/readiness and synthetic-fixture gate — terminal
   `blocked_by_external_state`.
2. Authenticated-session and core-navigation coverage — terminal
   `blocked_by_external_state`.
3. Exhaustive screen/state/transition inventory — terminal
   `blocked_by_external_state`.
4. Input/lifecycle/safe-recovery coverage — terminal
   `blocked_by_external_state`.
5. Boundary classification and safe recovery — terminal
   `blocked_by_external_state`.
6. Regression ledger, public-safe reports, repository cleanup and reviews —
   repository-only closure; it does not change the blocked product result.

## Coverage closure contract

The fixed tracked crosswalk is consumed exactly once and must contain exactly 43
distinct rows in canonical order: 26 TASK-045 rows plus 17 TASK-045A rows.
Rows `phone-coverage-001`, `phone-coverage-017` and `A002` may remain `covered`
only when the tracked TASK-058A v2 summary, scenario-ledger hash and all three
visual/UI-tree/bounded-log modality references validate exactly.

All remaining `phone_required` rows are terminal
`blocked_by_external_state` with reason
`synthetic_fixture_classification_absent_and_no_literal_runtime_go` and block
release. Paired/non-phone deferred rows preserve their crosswalk status and
release effect. `A001` remains audit-only `blocked_by_tooling`; it never counts
as product coverage. No approved reachable phone row is silently converted to
`not_run_out_of_scope`.

## Unified action and evidence contract

The current authorized maximum and actual budget are both zero. There were zero
device, application, runtime, authentication, credential-value and forbidden
actions. The following ceilings are plan-only and do not authorize runtime:

- epic total: concurrency `1`, launches/relaunches `<=8`, UI actions `<=340`,
  checkpoints `<=200`, local-only QR decodes `<=20`, runtime `<=180` minutes,
  raw sink `<=1 GiB`;
- readiness metadata: `<=3` selector snapshots and `<=8` target-only read-only
  metadata queries, with zero launch/input;
- authentication: `<=1` launch, `<=40` safe inputs, at most one phone submit
  and one OTP submit, `<=12` checkpoints, `<=15` minutes, zero wrong-code,
  captcha or retry attempts;
- core navigation: `<=60` actions, `<=35` checkpoints, `<=25` minutes;
- each exhaustive-inventory slice: `<=80` actions, `<=50` checkpoints,
  `<=30` minutes, always within the epic total;
- lifecycle/input: `<=40` inputs, `<=2` Home/foreground cycles, `<=1`
  target-only force-stop/relaunch cycle, `<=30` checkpoints, `<=25` minutes;
  orientation/display actions remain zero without separate review;
- boundary coverage: `<=60` actions, `<=20` boundaries, `<=20` local-only QR
  decodes, one known-safe Back attempt at most per boundary, `<=40` checkpoints,
  `<=30` minutes, and zero external follow/auth/payment/session start.

Before every future conditional action, capture directly into the fixed ignored
run sink a screenshot for visual inspection, a UI tree, and a target-only
bounded log marker. The log is limited to 200 lines and 64 KiB per checkpoint;
native output goes directly to the raw sink and is never echoed. Record
checkpoint id, public-safe screen alias, state/evidence/focus/action categories,
intended target and oracle, remaining budget, boundary flag and a
risk/hypothesis note. Act only when all three modalities exist, the target is
unambiguous and safe, no drift/raw spill/boundary is present, and budget remains.
After the action, capture the same triplet and record the actual result. Missing
modality means `blocked_by_tooling`; screenshot/XML mismatch is an immediate
first-class anomaly. The screenshot governs visible overlays.

This is the mandatory checkpoint before every action contract.
Here, `action` means a state-changing navigation, input, lifecycle or boundary
operation. Passive collection of the prerequisite evidence triplet and an
emergency kill switch are exempt from recursively requiring their own prior
triplet; they remain separately counted and audited.

The future raw sink is a fresh contained ignored run directory under
`.qa_local/evidence/epic-phone-001/<run_id>/`, with no symlink/reparse point,
retention/expiry and capture-shutdown controls. Secret presence may be checked
only at a fixed ignored local source without enumerating or printing keys or
values. The public projection allowlist is limited to aliases, category-level
booleans/enums, counters, timestamps, evidence ids and reason/status codes.

Anomalies must be recorded before continuation or recovery with trigger,
expected/observed result, evidence status, public-safe alias, cause
classification and test-design implication. Recurrences and recovery paths
remain distinct events.

Visible QR codes are first-class checkpoints. A recurring QR references its
prior local artifact; a new QR uses the established local `jsqr` path. The raw
target stays local-only and is never followed. Decode failure is recorded first
as a process anomaly and `blocked_by_tooling`. Payment or other boundary
recovery permits at most one known-safe Back attempt; an unchanged or unsafe
state invokes the kill switch.

The future kill switch is target-only force-stop + Home + capture shutdown.
It never authorizes uninstall, reinstall, clear/reset, APK modification,
security bypass or broad device cleanup. Cleanup must verify zero transaction,
account or unintended session mutation and keep all raw evidence local-only.

## Hard boundaries

Forbidden: real payment, real-user mutation, external QR/browser traversal,
production load or network shaping, APK modification/bypass, destructive
device actions, secret/raw endpoint extraction, and publication of phone/OTP,
tokens, QR targets, identities or raw evidence. Payment/QR/auth/external
boundaries are inventory surfaces, not permission to cross them.

A future contour remains blocked until Security returns a fresh literal token
bound to epic id, contour id, run id, plan hash, target/build/passport aliases
and hashes/expiry, and the contour budget. Drift, resume, expiry, material
contour change or a kill-switch event invalidates that token. The repository
and controller cannot derive or self-issue a GO.

If freshness fails because the controller clock may be skewed, stop and verify
trusted UTC alignment before retrying the repository check. Never rewrite
inherited evidence or weaken the no-future gate to cure clock skew.

## Fixed-path harness and artifacts

`automation/phone/epic_phone_001_full_mobile_coverage.py` supports only:

```text
--validate-only
--publish-blocked-baseline
--validate-report
```

It accepts no path/input override, never reads ignored local storage, never
starts subprocesses and has no device/network/credential interface. It emits
the v2 blocked summary and coverage, readiness, stage, action-budget, anomaly
and cleanup ledgers under `docs/qa/reports/`.

## Acceptance and stop conditions

- Exact 43-row lossless terminal ledger, with zero missing/duplicate rows.
- TASK-058A inheritance is hash- and modality-validated or fails closed.
- Current row 03 remains `unknown`; clean-first-launch remains consumed and is
  not claimed restorable.
- Summary is `blocks_release`; all action counters are zero.
- Exact Security verdict is preserved and cannot be upgraded by the harness.
- Focused tests, compile, report validation, manifest regeneration/validation,
  diff review and independent QA/Security reviews pass before integration.
- Stop before runtime/auth if synthetic classification and fresh literal
  Security GO are absent; stop on source/hash drift or unsafe public content.
