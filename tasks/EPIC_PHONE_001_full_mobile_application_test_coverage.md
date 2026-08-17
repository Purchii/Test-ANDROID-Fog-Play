# EPIC-PHONE-001 — Full mobile application test coverage

## Mode, scope and terminal result

- Mode: `BOUNDED_AUTONOMOUS`.
- Branch: `qa/epic-phone-001-full-mobile-application-test-coverage`.
- Repository planning, harness, ledgers and validation: `PROD_SAFE_REPOSITORY_ONLY`.
- Runtime and device actions: `PROD_CONDITIONAL`, currently blocked.
- Authentication or credential entry: `PROD_CONDITIONAL`, currently blocked.
- Current Security verdict:
  `GO_REPOSITORY_CONTROLLER_CONSTRUCTION / NO_GO_C1_EXECUTION / BLOCK_RUNTIME / BLOCK_AUTH_ENTRY`.
- Terminal baseline: `closed_by_ledger`, `partial_blocked`, `blocks_release`.

The former TASK-059, TASK-060, TASK-061 and TASK-062 objectives are internal
stages of this single epic. They are not independent tasks, threads or
branches. Completed TASK-058/TASK-058A history is immutable. TASK-058A consumed
the clean-first-launch state and closed with readiness 6/7; readiness row 03 is
still `unknown` and the owner override is not reusable as normal runtime
authority.

## Current fail-closed authority decision

On 2026-08-16 the owner confirmed the category-only authority for fixture alias
`epic-phone-001-fixture-001`: it is fully synthetic/test-only, is not linked to
a real user, is approved only for the current MTC Fog Play build/environment
and authorized phone, and authentication/read-only navigation cannot create
billing, payment, subscription or entitlement impact. Authority lasts only for
run `epic-phone-001-20260816-r01` until completion or revocation. Synthetic
session creation, read-only navigation and safe logout are allowed in scope;
payment, subscription, entitlement, profile/account mutation, paid session and
external/QR traversal are forbidden. The owner also stated that the OTP is
constant; its value was not requested, accessed, recorded or published.

This confirmation closes only the category-level fixture-classification
prerequisite. It does not authorize secret presence inspection, C1 execution,
application launch, authentication or runtime. Those remain blocked pending
their distinct exact plans, local passports and fresh literal Security tokens.
The current interim Security decision permits repository controller
construction only.

The immutable pre-confirmation baseline retains its historical Security
verdict `GO_REPOSITORY_PLAN/BLOCK_RUNTIME/BLOCK_AUTH_ENTRY`; this is provenance
for that report, not current runtime authority and not a reusable GO.

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

The already-published blocked baseline remains immutable evidence of the
pre-confirmation checkpoint. Its remaining `phone_required` rows keep their
then-current reason
`synthetic_fixture_classification_absent_and_no_literal_runtime_go`; that old
reason is not reused as a claim about current owner authority. Current runtime
coverage remains blocked because no C0P or C1 literal token has been issued and
no contour has run. Paired/non-phone deferred rows preserve their crosswalk
status and release effect. `A001` remains audit-only `blocked_by_tooling`; it
never counts as product coverage. No approved reachable phone row is silently
converted to `not_run_out_of_scope`.

## Unified action and evidence contract

The current authorized maximum and actual budget are both zero. There were zero
device, application, runtime, authentication, credential-value and forbidden
actions. The following ceilings are plan-only and do not authorize runtime:

- epic total plan ceiling is subject to each contour's fresh GO; checkpoint
  capacity must always be at least state-changing actions plus one when
  adjacent post/pre checkpoint sharing is used: concurrency `1`, state-changing
  actions `<=340`, checkpoint triplets `<=349`, launches/relaunches `<=8`,
  runtime `<=180` minutes, local-only QR decodes `<=20`, raw sink `<=1 GiB`;
- C1 launch-free readiness: one external executor call, zero retries, `<=10`
  minutes, `20` seconds command timeout, `<=3` selector snapshots, `<=8`
  target-only read-only metadata queries, `48 MiB` soft and `64 MiB` hard sink
  limits, and zero launch/UI/auth/credential/mutation actions;
- authentication: `<=1` launch, `<=40` safe inputs, at most one phone submit
  and one OTP submit, `<=42` checkpoints, `<=15` minutes, zero wrong-code,
  captcha or retry attempts;
- core navigation: `<=60` actions, `<=61` checkpoints, `<=25` minutes;
- each exhaustive-inventory slice: `<=80` actions, `<=81` checkpoints,
  `<=30` minutes, at most two slices with aggregate `<=120` actions and
  `<=122` checkpoints, always within the epic total;
- lifecycle/input: `<=40` inputs, `<=2` Home/foreground cycles, `<=1`
  target-only force-stop/relaunch cycle, `<=47` checkpoints, `<=25` minutes;
  orientation/display actions remain zero without separate review;
- boundary coverage: `<=60` actions, `<=20` boundaries, `<=20` local-only QR
  decodes, one known-safe Back attempt at most per boundary, `<=61` checkpoints,
  `<=30` minutes, and zero external follow/auth/payment/session start.
- terminal cleanup: `<=3` state-changing actions and `<=4` checkpoints,
  target-only stop/Home/capture shutdown, under its own fresh literal GO.

For `N` state-changing actions a contour must reserve at least `N+1` complete
triplet checkpoints. A post-action checkpoint may serve as the next pre-action
checkpoint only after all three modalities and the target/oracle/budget gate
validate; otherwise sharing is forbidden. This correction prevents C2 or any
later contour from claiming a 40-action budget with only 12 checkpoints.

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

`automation/phone/epic_phone_001_runtime_controller.py` is the separate
fail-closed runtime-controller contract. Its fixed public aliases are target
`phone-current-001`, build `task058-selected-phone-full-001`, fixture
`epic-phone-001-fixture-001`, run `epic-phone-001-20260816-r01`, and C1 contour
`epic-phone-001-c1-launch-free-readiness`. `--validate-only` and `--dry-run`
perform no ignored-storage, secret, subprocess, device or application access.
Future `--preflight-c1 --allow-prod-conditional-c1` validates only fixed local
plan/passport/token artifacts; it has no executor and cannot run C1.

The separate guarded C0P interface is
`--preflight-c0p --allow-prod-conditional-c0p`. It is inert without the exact
allow flag and literal C0P token. After every source/plan/passport/token binding
passes, it atomically creates the fixed durable one-shot attempt marker and only
then reads the fixed secret source once with an `8 KiB` ceiling. The marker is
never removed on parser, validation, result-write or interruption failure, so
the same token cannot authorize a second read. C0P accepts exactly the two
approved ASCII fields once each, writes the fixed canonical local-only result,
and emits only the approved five-field aggregate. It starts no subprocess and
performs no ADB, device, application or auth action.

### C0P-PREP artifact preparation contour

C0P cannot create the plan/passports that gate its own execution. The proposed
`C0P-PREP` contour is therefore separate from C0P and C1. Its review uses the
canonical class `PROD_SAFE` with scope qualifier
`ZERO_SECRET_ZERO_DEVICE_LOCAL_PREPARATION`, but it must not execute until
Security reviews and explicitly approves the exact prep plan.

The tracked preparer is
`automation/phone/epic_phone_001_c0p_prep.py`. Current authority is
`GO_REPOSITORY_CONSTRUCTION_ONLY`; only `--validate-only` may be run during
construction/review. Future `--execute` has no path overrides and requires a
fresh literal `EPIC_PHONE_001_C0P_PREP_GO` value bound to the SHA-256 of the
exact canonical fixed prep plan. The fixed public-safe inputs use directory
`docs/qa/phone/` and filenames `epic-phone-001-c0p-prep-candidate.json` and
`epic-phone-001-c0p-prep-plan.json`. The plan binds committed
HEAD, controller and preparer source hashes, exact candidate size/hash,
`.gitignore` hash, aliases, TTL, budgets, output paths and failure policy.
Neither input is accepted through a CLI override.

An approved `C0P-PREP` may create only the fixed ignored run-directory tree for
`epic-phone-001-20260816-r01`, its canonical `c0p-plan.local.json`,
`fixture-authority-passport.local.json`, `target-build-passport.local.json` and
`evidence-cleanup-passport.local.json`. The fixed sink tree may contain the
empty readiness directories `raw/`, `checkpoints/` and `public-safe/`; prep may
not place runtime evidence in them. Prep validates fixed-root containment,
tracked ignore-policy coverage, no-reparse state, capacity and exclusive
create-new access. The evidence-cleanup passport is a policy/readiness
declaration only: prep does not prove OS ownership, ACL privacy, later capture
control or retention enforcement. Those controls require a separate gate
before runtime evidence capture. It does not prove force-stop/Home/capture-
shutdown execution, zero mutation or successful post-run cleanup; later
contour evidence must prove those outcomes.

`C0P-PREP` has exact zero reads of `.qa_local/secrets/qa_user.env`, the serial
map or any credential/identity source; one approved host executor process and
zero child subprocesses, ADB, device, app or network contact; zero runtime/auth
actions; and zero C0P attempt/result writes.
It cannot issue, write, derive or infer a GO token. C0P remains the separate
one-shot `PROD_CONDITIONAL` contour described above.

The shared ignored parents `.qa_local/` and `.qa_local/evidence/` must already
exist. Exclusive creation of the task-specific prep-attempt root is the first
mutation and durable consumed-attempt marker; the fixed run root follows under
it. Any interruption or I/O/validation failure after that point leaves the partial root
in place and permanently blocks retry/reuse; the preparer performs no cleanup,
delete, overwrite, append or rename. Success creates exactly four canonical
files and the empty `raw/`, `checkpoints/` and `public-safe/` directories. Its
safe aggregate reports seven directory targets, exactly five created task/run
directories and four successful files, with one host process, zero child processes
and zero secret/device/app/network/auth/runtime actions.

The target-build passport is authorization-only. It binds public aliases and
the owner's current-epic permission but is not current target/build freshness,
installed-state, selector, mapping or runtime evidence. Security blocker
`CURRENT_EPIC_TARGET_BUILD_FRESHNESS_AUTHORITY_ABSENT` remains open; C1 must
obtain fresh launch-free target/build evidence under its own later literal GO.

The pre-correction binding used repository HEAD
`3df6b883301b6512cb90ed1e616221f10cc48e26`, controller implementation commit
`68e8bebd1162fef9aea51d88e603ebf4832d41c4` and controller source SHA-256
`793e03d2dc3c141d728bcd9cc0b1c58e8ee79d760d58e634915f83fe8d486e68`.
Any commit containing this source-of-truth correction changes HEAD, so the
candidate C0P plan hash prefix `f883` is invalid and must be recomputed after
the final reviewed docs commit. No token may bind or reuse that candidate hash.

The C1 plan hash is SHA-256 over canonical NFC-normalized, key-sorted, minified
UTF-8 JSON. The literal token format is
`GO_EPIC_PHONE_001_C1_LAUNCH_FREE_READINESS__epic-phone-001-20260816-r01__<64_lowercase_plan_sha256>`.
Its Security passport alias is `epic-phone-001-security-c1-001`, and token
validity may not exceed 30 minutes.
Checkpoint `C1-000` is the mandatory pre-execution gate; `C1-999` is mandatory
after success, failure, timeout or kill-switch handling and cannot be omitted.

Local phone/OTP presence is a distinct C0P contour
`epic-phone-001-c0p-local-presence`, not part of C1. It requires its own plan,
Security alias `epic-phone-001-security-c0p-001`, and literal token format
`GO_EPIC_PHONE_001_C0P_LOCAL_PRESENCE__epic-phone-001-20260816-r01__<64_lowercase_c0p_plan_sha256>`.
Its exact public aggregate contains only `required_field_count=2`,
`required_fields_present`, `unexpected_fields_absent`,
`phone_format_policy_pass`, and `otp_format_policy_pass`. Raw field names,
values, individual-presence flags, lengths and credential hashes may never be
emitted.

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
