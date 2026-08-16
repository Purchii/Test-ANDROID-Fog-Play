# TASK-058A — Phone Full launch-readiness and pre-auth continuation

## Contract

- Mode: `BOUNDED_AUTONOMOUS`.
- Repository work and synthetic-only checks: `PROD_SAFE`.
- Launch-free package/device inspection and the bounded first pre-auth run:
  `PROD_CONDITIONAL` and forbidden until the exact Security gates below pass.
- Branch: `qa/task-058a-phone-launch-readiness-pre-auth-continuation`, based on
  remote default `main` at `adc601edfe579ac5cf63bf2a4c3c149be0686c72`.
- This is a continuation of completed TASK-058 only. It must not rewrite any
  historical TASK-058 artifact and must not execute TASK-059 or later work.

## Owner authority and irreversible fixture note

The owner authority dated 2026-08-16 permits one launch-free verification of
the already installed selected build, current selector and unrelated-package
delta without reinstall. It accepts the current `installed_never_launched`
state as the clean-first-launch fixture and absence of a real session as the
synthetic pre-auth fixture. It permits exactly one launch and no more than 20
safe pre-auth actions with local screenshot, UI-tree and bounded target-app
marker/log evidence under redaction-by-default.

The owner does not permit uninstall, install, alternate artifact selection,
clear-data, device reset or retry. Consuming the never-launched state cannot be
rolled back without a reinstall, and TASK-058A must never claim that rollback
or restoration exists.

## Goal

Close TASK-057 readiness rows 02 and 03 using a purpose-built launch-free,
one-shot collector whose native stdout and stderr are written directly to an
ignored task/run-bound sink before any parsing or public projection. The
collector must establish exact installed/candidate compatibility at category
level: package and family, version, signing, base-or-split topology and hashes;
it must also establish one stable authorized selector and zero unrelated-
package delta against the authorized reference snapshot.

Materialize three independent ignored task/run-bound passports:

1. `pre_auth_no_real_session`;
2. `owner_approved_clean_first_launch`;
3. `runtime_evidence_cleanup`.

Each passport requires a current TTL, public-safe aliases, retention/redaction,
the exact action budget, an observation result and an independent Security
review result. Owner authority alone does not promote a pending observation or
review to `confirmed`.

## Exact gates

Before any launch-free device command, Security/Prod-safety reviews the exact
collector source, fixed command allowlist, raw sink, three passport files,
retention/redaction, action budget, kill switch and cleanup plan. A plan review
may authorize only launch-free collection; it is not `GO_RUNTIME`.

Security may issue `GO_RUNTIME` only after all seven readiness rows are freshly
`observed_pass` in this run. The collector and repository reporter are not
Security principals and never self-issue `GO_RUNTIME`. Any pending, expired,
ambiguous, missing or blocked row means `BLOCK_RUNTIME` and zero launch.

That legacy gate was not met by the one-shot collector. The later runtime used
a distinct owner-risk path: after the owner confirmed that the installed app is
the supplied same build, explicitly authorized testing it, verbatim waived
selector and unrelated-package-delta revalidation and accepted drift risk,
Security issued a hash-bound `GO_RUNTIME_OWNER_OVERRIDE`. This decision applies
only to this exact run. It is not `GO_RUNTIME`, does not convert row 03 into
observed evidence and cannot authorize TASK-059 or a later run.

The exact runtime budget is:

- launch: `1` maximum and exactly one only after either the normal
  `GO_RUNTIME` gate or the explicit one-run `GO_RUNTIME_OWNER_OVERRIDE`
  exception documented above;
- safe pre-auth actions: `20` maximum;
- credentials, data entry, authentication, payment/account mutation, media or
  paid-session start, network shaping, QR/browser/external traversal and
  destructive UI: `0` each;
- reinstall, uninstall, alternate artifact, clear-data, reset and retry: `0`
  each.

The one-shot runtime kill switch is target-package force-stop followed by Home,
then capture shutdown. Cleanup is the same target force-stop, Home and capture
shutdown. It does not restore `installed_never_launched`.

## Runtime coverage after exact Security runtime authority

Launch exactly once. Before the first action and before every later action,
capture all three fresh modalities: screenshot with visual inspection, UI tree
and bounded target-app marker/log. Record screen alias, state category,
evidence status, focus/action categories and a concise risk or hypothesis.
Record every anomaly immediately before continuing or recovering.

The required inherited rows are lossless and distinct:

- `phone-coverage-001` — first launch;
- `phone-coverage-017` — auth guard;
- `A002` — cold-launch-to-auth-guard transition.

Append every newly discovered safely reachable first-launch or pre-auth state,
transition, overlay, recurrence, anomaly and boundary. Continue until the
coverage ledger assigns every approved reachable branch one terminal status:
`covered`, `blocked_by_boundary`, `blocked_by_tooling` or
`blocked_by_external_state`. `not_run_out_of_scope` is forbidden for an
approved reachable row. TASK-059+ screens and actions remain out of scope.

Do not follow QR/browser or other external boundaries, enter data, authenticate,
mutate account or payment state, start media, shape network, or use destructive
UI. Unexpected authenticated, payment or external state; missing modality; raw
spill; selector/build/package drift; budget exhaustion; or cleanup failure
triggers the one-shot kill switch and immediate stop.

## Evidence and public projection

Raw command output, raw paths, device identifiers, package names, certificate
digests, artifact hashes, screenshots, XML and logs remain only below the
ignored `.qa_local/task058a/` sink. The collector emits no raw native output to
the console. Public reports contain only aliases, category-level booleans,
counts, statuses and evidence identifiers.

The tracked fixed-path reporter validates a sanitized projection from the exact
ignored task/run path. It rejects duplicate or missing readiness rows, expired
passports, a false `observed_pass`, unsafe-shaped public values, action-budget
drift, missing modalities, and any claim that the clean-first-launch fixture was
restored. The pre-execution baseline was intentionally `BLOCK_RUNTIME`; the
actual owner-override result remains release-blocking for the independent row
03 reason described below.

## Actual execution and owner-override result

Security first issued a collection-only GO after reviewing the one-shot
collector and its evidence containment. The collector executed exactly once
and failed closed with public-safe result
`artifact_metadata_ambiguous:min_sdk`. No retry, package mutation, reinstall,
uninstall, clear-data, reset or launch occurred in that phase, and the
ambiguous value was not promoted to evidence.

The owner then supplied the confirmations and final waiver described above.
Security bound `GO_RUNTIME_OWNER_OVERRIDE` to that exact authority and current
evidence hash. Readiness closed as six `observed_pass` rows plus one
`blocked_by_external_state` row:

- row 03 remains `evidence_status=unknown` with reason
  `selector_unrelated_delta_waived_owner_override` because selector and
  unrelated-package delta were not revalidated;
- the other six rows are `observed_pass` under the current owner-confirmed
  installed-build, pre-auth fixture, clean-first-launch, evidence/cleanup and
  Security authority;
- the aggregate remains release-blocking and does not satisfy TASK-059.

One prelaunch checkpoint showed Home with the target absent from the visible
foreground. Exactly one launch then produced a postlaunch checkpoint with
screenshot visual inspection, UI tree and bounded target-app marker/log. The
visible screen was the Fog Play pre-auth login surface and therefore an
authentication boundary. No UI action followed.

`phone-coverage-001`, `phone-coverage-017` and `A002` are covered with fresh
evidence. The discovered login/authentication boundary is terminal
`blocked_by_boundary`. Credentials, data entry, authentication, account or
payment mutation, media/session start, network shaping, external/QR traversal,
destructive action and TASK-059 actions are all zero.

The postlaunch screenshot contained a partial green overlay at the left edge
that was absent from the UI tree. The screenshot/XML mismatch is `confirmed`;
system/tooling overlay is `likely`, and product cause is `unknown`. It is
recorded as a first-class anomaly rather than product evidence.

Boundary stop invoked the one-shot kill switch. Target force-stop, Home and
capture shutdown succeeded. Final counters are launch `1`, safe pre-auth UI
actions `0`, forbidden actions `0`, checkpoints `2` and cleanup `1`. The
installed-never-launched fixture was consumed and is unrecoverable without a
prohibited reinstall; no rollback is claimed.

Confirmed public-safe process anomalies are:

- `TASK058A-PROCESS-ANOMALY-001`,
  `collector_artifact_metadata_min_sdk_ambiguous`: the one authorized
  collector execution blocked before runtime; no failed output was accepted
  and no retry occurred;
- `TASK058A-PROCESS-ANOMALY-002`,
  `runtime_controller_security_defects_pre_device`: Security found controller
  defects before device execution; they were fixed and re-reviewed before any
  device action, so no unsafe product action occurred;
- `TASK058A-RUNTIME-ANOMALY-001`,
  `partial_green_left_edge_visual_xml_mismatch`: the postlaunch screenshot
  showed a visual overlay absent from XML; retain screenshot inspection and do
  not infer overlay absence from the UI tree.

Final repository verification passes: runner `--validate-only` and
`--validate-report`; 161 focused related/release tests; the supplementary suite
excluding only the Security-forbidden TASK-045 environment-coupled test with
1392 passed and 4 skipped; compile; report manifest with 35 records, 12
authoritative and 23 legacy; both hygiene modes; public safety 421/0; docs
consistency/link sanity 186/0; and diff checks.

QA Reviewer A and QA Reviewer B each returned final `GO` with R0/R1/P2
`0/0/0`. Security returned
`GO_REPOSITORY_CLOSURE / NO_NEW_RUNTIME_AUTHORITY` with R0/R1/P2 `0/0/0`.
Docs/Scribe final reconciliation returned `GO`. Lifecycle is
`inactive_completed_release_blocked`: implementation commit
`65b9b9e07515ee77e2aa27f9b5f21b4b5f0840ff` and reviewed closure commit
`3b7e8b12e15989b791363d2be9a216fc38d2633f` are pushed to the task branch,
and the reviewed closure was fast-forwarded to remote `main`.

## Acceptance criteria

- Historical TASK-058 tracked files are byte-for-byte unchanged.
- The launch-free collector is purpose-built, local-only, one-shot, no-retry,
  no-mutation and no-launch, with direct stdout/stderr capture.
- The three independent passports are task/run-bound, unexpired at use, and do
  not infer observation or Security approval from owner authority.
- The normal readiness path proves row 02 installed/candidate compatibility,
  including base-or-split and hash/signing equivalence, and row 03 stable
  selector plus zero unrelated-package delta. The actual exception records the
  owner's same-build confirmation and keeps waived row 03 unknown rather than
  manufacturing collector evidence.
- The normal runtime path starts only at exact `7/7 observed_pass` plus
  Security `GO_RUNTIME`. The actual one-run exception uses the separately
  hash-bound `GO_RUNTIME_OWNER_OVERRIDE`, keeps row 03 unknown, stays
  release-blocking and cannot be reused.
- If runtime is authorized, all three inherited rows plus discovered states
  reach a valid terminal ledger status with fresh three-modality evidence for
  each covered checkpoint.
- Cleanup records target force-stop, Home and capture shutdown without a false
  rollback claim.
- Focused repository and synthetic-only checks pass, followed by independent QA
  and Security reviews before integration.

## Stop conditions

Stop before launch on any readiness or passport blocker, Security `NO_GO`, raw
spill, drift or ambiguity. During runtime, immediately execute the kill switch
and stop on any forbidden boundary, modality failure, budget exhaustion or
cleanup failure. No retry, reset, reinstall, alternate artifact or expansion
to TASK-059+ is allowed.
