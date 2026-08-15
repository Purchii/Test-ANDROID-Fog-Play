# TASK-057R — Phone Full authorized reinstall and readiness revalidation

## Contract

- Mode: `BOUNDED_AUTONOMOUS`.
- Repository work: `PROD_SAFE`.
- Exact target-only uninstall/install contour: `PROD_CONDITIONAL` after the
  owner authorization dated 2026-08-16 and the task-local Security plan gate.
- Dependency: completed blocked TASK-057 plus the fresh owner authorization.
- Branch: `qa/task-057r-phone-full-authorized-reinstall-readiness-revalidation`.
- Result: reinstall `observed_pass`; readiness `blocked`; `BLOCK_RUNTIME`;
  `blocks_release`; TASK-058 `not_run` and remains blocked.

## Goal

Uninstall only the freshly mapped installed Phone Full target, accepting the
authorized loss of that target application's local data/session, install only
the selected local-only `main-apk-03` candidate by an ordinary install, then
perform launch-free metadata checks and freshly re-evaluate the exact seven
TASK-057 readiness rows.

The authorized uninstall is not a clear-data action, downgrade bypass, device
reset, rollback promise or general permission to mutate packages. A successful
install cannot infer synthetic-session, clean-first-launch, evidence/cleanup
passport, runtime budget, kill switch, cleanup/rollback or Security
`GO_RUNTIME` authority.

## Exact bounded action result

The public-safe action ledger records one freshly mapped target, exactly one
pre-action Security plan GO, a distinct pre-action one-shot contingency, exactly
one authorized uninstall, target absence after uninstall, exactly one ordinary
install of `main-apk-03`, exact post-install candidate metadata/signing/hash
equivalence, zero unrelated-package delta, and zero launch, product navigation
or TASK-058 actions. Phase/order fields prove that Security GO and the
contingency preceded uninstall. Raw paths, device identifiers, package names,
hashes, signing values and command output remain ignored/local-only.

The reinstall-action kill switch is
`confirmed_stop_no_retry_on_drift_or_failure`. If uninstall or install had
failed, execution would stop without retry and recovery would require new owner
authority. The contingency was not used because the one-shot sequence passed.
This is distinct from both the accepted data loss/no-rollback statement and the
absent runtime kill switch/passport required for later product runtime.

The target application's prior local data/session was intentionally lost under
the owner authorization. It was not restored and no rollback of that data is
claimed.

## Exact seven-row readiness result

The revalidation preserves the seven independent TASK-057 authority subjects:

1. `main-apk-03`: `observed_pass` only because fresh category-level evidence
   independently confirms integrity, provenance, signing, version, emitted
   min-SDK, target-SDK, ABI and install compatibility. No raw values are
   published; omission of any category blocks the row.
2. `installed-phone-full-build`: `observed_pass` from fresh launch-free
   post-install exact candidate equivalence.
3. `phone-current-001`: `observed_pass` from fresh stable selector mapping and
   authorization.
4. `ordinary-downgrade-guard`: `observed_pass`; the authorized uninstall was
   target-scoped and no downgrade override, patch, re-sign or bypass was used.
5. `synthetic-session-passport`: `blocked_by_fixture`; absence of a session
   after uninstall is not a synthetic-session passport.
6. `clean-first-launch-fixture`: `blocked_by_fixture`; a successful reinstall
   is not an approved clean-first-launch fixture/passport.
7. `evidence-cleanup-passport`: `blocked_by_fixture`; task-local redaction and
   bounded cleanup evidence do not establish the runtime passport, runtime
   budget, kill switch, cleanup/rollback or Security `GO_RUNTIME`.

The aggregate is exactly four `observed_pass` and three blocking rows.
Readiness remains `BLOCK_RUNTIME` / `blocks_release`; TASK-058 was not executed.

## Process anomalies

All three anomalies are `confirmed`, fail-closed, occurred before package
mutation and have no product impact:

- `TASK057R-PROCESS-ANOMALY-001`, public alias
  `same_repository_common_dir_path_normalization_failure`: rooted and relative
  Git common-directory values were initially normalized incorrectly. The
  recovery normalized each value by rootedness without weakening provenance.
- `TASK057R-PROCESS-ANOMALY-002`, public alias
  `powershell_line_selection_expression_errors`: bounded PowerShell line
  selection/expression attempts failed before action. The recovery used a
  corrected bounded expression and accepted no evidence from failed output.
- `TASK057R-PROCESS-ANOMALY-003`, public alias
  `split_package_false_ambiguity`: an initial package-shape classifier treated
  a permitted split-package representation as ambiguous. Exact target mapping
  and a corrected category-only classifier resolved the tooling error before
  mutation; no alternate package was touched.

A fourth repository-only Builder anomaly is also `confirmed` with no product
impact: `TASK057R-PROCESS-ANOMALY-004`, alias
`reviewer_gate_uppercase_slug_validation_mismatch`. The first focused suite
expected the fixed contract to pass but valid uppercase reviewer-gate enums
were incorrectly checked as lowercase slugs, causing eight test failures. The
field now uses its exact enum contract and the focused rerun passes; the first
failure remains recorded.

## Tracked deliverables

- `automation/runtime_authority/task057r_phone_full_authorized_reinstall_readiness.py`;
- `tests/test_task057r_phone_full_authorized_reinstall_readiness.py`;
- `docs/qa/reports/task057r_phone_full_authorized_reinstall_readiness.readiness-ledger.csv`;
- `docs/qa/reports/task057r_phone_full_authorized_reinstall_readiness.reinstall-action-ledger.csv`;
- `docs/qa/reports/task057r_phone_full_authorized_reinstall_readiness.cleanup-ledger.csv`;
- `docs/qa/reports/task057r_phone_full_authorized_reinstall_readiness.summary.json`.

The runner is repository-only. It validates or regenerates fixed sanitized
tracked ledgers and never reads `.qa_local`, invokes Android tooling/ADB,
performs package actions or accepts arbitrary input/output path overrides.

## Stop and safety rules

Stop on selector drift, artifact ambiguity, unexpected package state, failed
uninstall/install, raw-output spill, unrelated-package delta or scope expansion.
Do not launch the app, authenticate, navigate, use a real/unknown session,
perform clear-data/reset, change another package, bypass downgrade controls,
modify/re-sign/decompile the APK, shape the network, traverse QR/browser
boundaries or execute TASK-058.
