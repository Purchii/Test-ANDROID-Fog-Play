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

The first exact approved C0P-PREP attempt failed closed before mutation with
`shared_ignored_parent_missing`; its one-shot GO is consumed, invalid and
non-reusable. Shared-parent provisioning is therefore a separate contour with
id `epic-phone-001-shared-parent-provision`, class `PROD_SAFE` and qualifier
`ZERO_SECRET_ZERO_DEVICE_FIXED_SHARED_PARENT_PROVISIONING`. The fixed executor
`automation/phone/epic_phone_001_shared_parent_provision.py` may create only
`.qa_local` and `.qa_local/evidence`, in that order, and creates no files. Its
exact initial-state category is either `both_absent` or
`qa_local_present_evidence_absent`; mismatch, both-present, reparse, collision,
hash/TTL/GO drift or insufficient capacity fails closed. The first created
directory is the durable consumed-attempt marker. A later failure leaves it,
with no cleanup, retry or reuse. The contour has one host executor, zero child
processes and zero secret/serial/device/app/network/auth/runtime actions. Its
`--execute` mode remains blocked pending a post-commit canonical plan and fresh
literal Security GO; `--validate-only` is repository-safe. Because Windows
path-based `mkdir` cannot atomically rule out a hostile external reparse swap
after lstat, the plan must also bind a Security-attested exclusive-workspace,
no-external-path-mutator precondition for the complete two-minute window. If
that precondition cannot be assured, Security must not issue GO.

Any C0P-PREP reconsideration after successful parent provisioning must bind
`prep_attempt_id=c0p-prep-002` in the candidate, plan and public aggregate.
The consumed first plan/token cannot be relabeled, replayed or inferred as the
new attempt. Candidate, plan, result and validate-only contract identifiers are
therefore bumped to `v2`; legacy `v1` missing-field envelopes fail closed.

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

### Owner-local provisioner expiry and authority renewal

The owner-local provisioner is accepted as repository logic only. Its final
immutable bindings are executor SHA-256
`f47d97769ca1501dadd235776ced5f76f8dfa5230e09100d4fa142b8bb224263`,
loader SHA-256
`1cf7ebc750d31c363e21b27622510d0db3e03404ef7025c3b2d1a9cf27503797`
and focused-test SHA-256
`b9c92bf887c276fac0a870dfb89162c5f8551ca39883c0e4d93a8f63fa7c9375`.
Focused verification is 40 passed; the earlier combined EPIC repository set is
168 passed. QA-A, QA-B and Security repository R0/R1 are 0/0. Anomalies
`EPICPHONE001-PROCESS-ANOMALY-056` through `-070` remain append-only evidence.

The prepared authorities expired at `2026-08-18T05:50:28Z` before any fixture
write or GO. They are immutable and non-replayable. No process may extend,
overwrite, edit, relabel, rename or reuse them or their consumed plan. Secret,
device, app, network, auth and runtime counters remain zero; fixture write,
C0P, C1, auth and runtime remain blocked.

The only next safe design is
`ZERO_SECRET_ZERO_DEVICE_CREATE_NEW_VERSIONED_AUTHORITY_RENEWAL`. It creates
new versioned artifacts with create-new semantics and does not modify old
artifacts. Security-resolved identities are `authority-renewal-001`,
`c0p-authority-003`, `c0p-prep-003` and `security-c0p-003`; fixed paths are
under `authority-sets/c0p-authority-003`. These ids and paths do not authorize
execution or issue GO. The final owner-local provisioner source/HEAD rebind and
renewal candidate must be reviewed together and committed once; no interim
provisioner commit is permitted.

Four rejected discovery/legacy-transform helper/test drafts were removed from
the untracked candidate set. Their anomaly records remain; cleanup is complete
and touched no `.qa_local` path. The accepted provisioner candidate remains
untracked until the joint rebind/renewal review and final commit.

### Final renewal/rebind repository snapshot

The joint snapshot is accepted for repository commit only. Anomalies
`EPICPHONE001-PROCESS-ANOMALY-071` through `-082` are closed at repository
level and retained. Exact source bindings are renewal
`eaa8400c4ee881a3e7ed09067ffd338d42780ef1a5e61776060f10e86ed23468`
(`35832` bytes), renewal loader
`a34c006ede9543387c78bb09ed605d13d8d2b4f7840c6dc9d9fb93e51070c083`
(`13073` bytes), C0P
`323a3f6c8db65e10461d0537828aa800e3da958525824182f2f7c623168c4a22`,
controller `04bef96a5bd71c48ca80041745eb11fe61ea968ba71f7cc8d854295b81c33397`,
provisioner `280d993f55d8833da6397758ab0f5eb97ebc46764938723ac73bbfea3a270121`
and provisioner loader
`71b3387505a5ae4229315de38ae1d7e2855060ea3fdb1bfe3bf08db1fdf14441`.
The corresponding renewal/C0P/controller/provisioner test hashes are
`471d6e985e4de59cd4b1a6ff76e0f0a82efeeaefa4969fe092e14dab2d57df21`,
`a73550396cd9a6b261a188d22e36899cab5ab20b59bd962fda01ffc722e5890f`,
`868c69cf00ef90f7bdbe1bafbd99db1d97b6117b4a059a33053602dd3c1ee607`
and `3bd3121b615c3a1d35105665ce4f0f9ef7de87afc71506f434bbeef199a19231`.

Verification is core `144 passed`, named safety suites
`public_repo_safety`/`full_tree_hygiene` `14 passed`, combined `158 passed`,
plus compile and diff PASS. Final QA-A R0/R1/P2 is `0/0/1`, QA-B `0/0/0`,
and Security `0/0/1`. Cooperative timeout is the only P2 and requires fresh
owner acceptance before later execution.

`c0p-prep-003 --validate-only` is superseded by renewal. It grants no pending
execution step and cannot be replayed. No GO was issued and no renewal,
fixture-write, C0P, C1, secret, device, app, network, authentication or runtime
action executed; checkpoint-local counters are zero. Expired authorities stay
immutable/non-replayable. The joint implementation commit is
`2ca38ae9fff08550a0be533f9d8d934b8c7b7da6`, pushed/aligned on the epic branch;
the worktree was clean before the docs-only lifecycle delta. The post-doc final
HEAD must bind any new canonical candidate/plan and fresh owner/Security
authority. `origin/main@b268b1f198f595ec835e066169c97cdf839cc05b` remains
not integrated, and product/runtime coverage is not claimed.

### Generation 004 repository snapshot

Renewal `001` materialized immutable authority set `003` on HEAD
`92a60f8d585d5887a465563902c66a2aa2b373b4` from public candidate
`da2dfb73dbcd6d8bf7d9584809eb941e392fd7777386158a19f8c6d284580cb0`
(`10136` bytes) and plan
`48f2eaa1fee9047c3ca084fbbbf048e65fb8cc2a030e82473af90343abf0d49c`
(`5395` bytes). Result `authority_set_materialized` contains four artifacts,
two directories and six files with zero forbidden actions. Its literal GO is
consumed. Downstream passports expired at `2026-08-18T10:44:00Z`; no
provisioner, C0P, authentication or runtime contour executed. The generic
renewal-001 candidate/plan must remain removed and unstaged, with hashes
retained only as history.

Generation `004` repository bindings are:

- renewal `11a067beaf5d93d22bac9cb345f26d5eae64f4160b5c2684561f68a03aded007`
  / `36363`, loader
  `44e3d051b9bf5040c8c5b66087b5e74c4d3e2d0ce1cfeb22e11d5b209afde599`
  / `13051`;
- C0P `9e93e04577c3335717e9df649f8354100dd85eb69953233bbdc48fb44321aca0`
  / `42226`, controller
  `faa879fbbcffc7a3f30d55d9da4a4686d502ef0bfce2c9048f149787689a1540`
  / `59251`;
- provisioner
  `7e025a7e11f616b53f840e8a25e6c31b53cd0144a42584df4a3b380c8f1e73b5`
  / `59828`, provisioner loader
  `57bf6ae0df45fa1f36f61c3b38345f55ff8a02b0522a815d8b7c7397771bb3c9`
  / `22736`;
- authority/prep/controller/provisioner tests
  `4a025d2a86ad566548197a61655d98b5d1ab90b265cabd23462abdc4238c1013`,
  `77b79887be8eb34e2093bef9a0b0db51827b087350b5e131d4cb26db28e9ace5`,
  `96fedabeb06c2709f4ba594627cee2e5874d40066df198b89cc534c3b6919c23`
  and `cd06975e35104136a022aca77a8a812445b777c15a6ff8bd1eedc43ed3b05465`.

Core `170`, safety `14` and shared-parent `21` pass; the exact combined command
is `205 passed`. The safe full suite
`python -m pytest -q --ignore=tests/test_task045_paired_virtual_gamepad.py`
is `1609 passed, 4 skipped`. Compileall, AST, docs `187/0`, public safety
`443/0`, both hygiene modes, diff and cached-diff checks pass. QA-A is
`0/0/0`; QA-B delta is `0/0/0`, with integration P2 for expired-input
removal and docs; Security is `0/0/2`. Security P2 is cooperative no-hard-kill
plus a maximum ten-minute orchestration envelope. Closed R1 regressions cover
no-mutator alias `002`, unread preservation of existing set `003` with
create-only set `004`, provisioner dual actual-HEAD validation, and optional
loose-ref support in all three readers.

Anomalies 085–088 are retained; 087 is the orchestration anomaly. Generation
`004` is pending commit and has no GO. Renewal `002` requires the final
committed HEAD, fresh owner no-mutator authority `002`, a combined weekly
provision envelope, a canonical plan and Security GO. No default integration
or product/runtime coverage is claimed.

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
