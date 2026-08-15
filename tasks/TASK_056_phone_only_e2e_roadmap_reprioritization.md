# TASK-056 — Phone-only end-to-end QA roadmap reprioritization

## Mode and safety

- Mode: `BOUNDED_AUTONOMOUS`.
- Repository planning and validation: `PROD_SAFE_DOCS_ONLY`.
- Physical phone runtime: `PROD_CONDITIONAL`, currently `BLOCK_RUNTIME`.
- No ADB, APK read/install, application launch, account/session action, network
  shaping, QR traversal or raw-evidence access is authorized by this task.

## Goal

Replace the post-TASK-048 selection dead end with an owner-authorized,
phone-only execution roadmap. The near-term program must close every safely
reachable approved Phone Full screen, state, transition and boundary from first
launch onward, while preserving all Television, Stick and other device-family
history as deferred work rather than completed work.

## Branch

`qa/task-056-phone-only-e2e-roadmap-reprioritization`

## Authoritative inputs and evidence status

- `confirmed`: the owner currently makes one physical phone available.
- `confirmed`: TASK-045 and TASK-045A are closed historical authorities whose
  current Phone Full result remains incomplete and release-blocking.
- `confirmed`: TASK-045 recorded 26 terminal phone rows, but only two covered
  rows; TASK-045A recorded 17 terminal branch families with zero fresh covered
  branches.
- `confirmed`: historical TASK-045 visual/runtime material is audit-only and
  the Security-forbidden local TASK-045 source must not be read, restored or
  rerun to manufacture verification.
- `unknown`: current task-authoritative phone mapping/authorization, canonical
  Phone Full build integrity and installed-build compatibility.
- `unknown`: a current approved synthetic-session passport and a safe,
  non-destructive first-launch fixture.

### Exact authority matrix to revalidate in TASK-057

| Authority item | Current public status | What TASK-057 must prove separately |
|---|---|---|
| Canonical Phone Full `main-apk-03` | presence-only; content integrity and runtime compatibility `unknown_not_verified` | exact task-bound family/build alias plus permitted integrity/provenance oracle |
| Installed Phone Full build | distinct historical installed-newer alias | current installed/canonical compatibility without downgrade bypass |
| Physical phone | neutral `current-phone-selector` is unresolved; `phone-realme-001` is a historical TASK-045 candidate only | bind a new public-safe current-phone alias through fresh mapping, authorization and unchanged snapshot; reuse the historical alias only after an exact fresh match |
| Install attempt | ordinary canonical install was rejected as downgrade | preserve rejection; never uninstall, clear data or override downgrade safety |
| Synthetic fixture policy | public policy exists | fresh task-authoritative local-only session passport with TTL and Security approval |
| Clean first-launch state | `unknown` | owner-approved pre-provisioned state requiring no destructive reset |
| Evidence and cleanup | historical task-local records only | exact storage/retention/redaction, action budget, kill switch and cleanup/rollback passport |

No matrix row can infer or satisfy another. TASK-057 revalidates each row and
publishes a separate public-safe status/evidence alias.

The owner statement that a phone exists does not promote any unknown runtime
gate to confirmed and is not evidence for Television, Stick or another APK
family.

## Resource-policy overlay

From 2026-08-15, the active near-term lane is only Phone Full on the single
available physical phone. YandexTV, SberBox, AOSP FogPlay Stick, generic TV,
Television Full and all other APK/device variants are
`deferred_by_owner_resource_policy_2026-08-15` until the owner restores exact
resources. This overlay does not change or complete any historical task row.

TASK-046 through TASK-055 retain their recorded statuses, blockers and release
effects. Phone evidence is categorically ineligible for their TV/Stick,
cross-family, compatibility or five-APK claims.

## Phone-only roadmap

The roadmap is sequential and each row is an independent fresh-thread task.
Every runtime task must maintain an explicit screen/state/transition/boundary
coverage ledger. Every approved reachable item must end as `covered`,
`blocked_by_boundary`, `blocked_by_tooling`, or
`blocked_by_external_state`, with public-safe evidence identifiers.
`not_run_out_of_scope` is reserved for explicitly excluded or non-phone rows,
never for an approved reachable Phone Full item. A blocked row is terminal for
the run but never a PASS.

| Task | Purpose | Dependencies | Current status | Release semantics |
|---|---|---|---|---|
| TASK-057 | Phone Full lane, build and fixture authority gate | TASK-056; TASK-042/TASK-045/TASK-045A public authority | `planned_blocked_by_authority` | `blocks_release`; no runtime task may start before an explicit `GO_RUNTIME` |
| TASK-058 | Non-destructive first-launch and pre-auth coverage | TASK-057 `GO_RUNTIME` plus approved clean first-launch fixture | `planned_blocked_by_dependency` | any uncovered approved first-launch/pre-auth row blocks phone release |
| TASK-059 | Approved synthetic-session establishment and core navigation | TASK-058 plus current synthetic-session passport | `planned_blocked_by_dependency` | real/unknown session use, auth uncertainty or core-navigation gaps block release |
| TASK-060 | Exhaustive Phone Full screen/state/transition inventory | TASK-059 | `planned_blocked_by_dependency` | ledger closure is not PASS; every approved reachable row needs eligible fresh evidence |
| TASK-061 | Phone input, lifecycle and safe recovery coverage | TASK-060 | `planned_blocked_by_dependency` | failed focus/back/relaunch/recovery or unclean cleanup blocks release |
| TASK-062 | Phone boundary classification and safe recovery | TASK-060, TASK-061 | `planned_blocked_by_dependency` | unclassified/followed external, payment, QR or account boundary blocks release |
| TASK-063 | Phone-only evidence aggregation and release gate | TASK-057 through TASK-062 | `planned_blocked_by_dependency` | PASS requires authoritative fresh evidence for all required phone rows; no cross-family claim |

TASK-059 through TASK-062 require every predecessor to have aggregate `PASS`,
all required approved/reachable rows `covered`, zero release-blocking rows,
cleanup confirmed and current TASK-057/Security gates. A blocked or partial
closure does not authorize the next runtime task. `observed_pass` is reserved
for TASK-057 readiness rows. TASK-063 may aggregate blocked terminal
predecessors only to publish `blocks_release`; it cannot promote them to PASS.

The detailed contracts are in `tasks/TASK_057_phone_full_runtime_authority_gate.md`
through `tasks/TASK_063_phone_only_release_gate.md`.

## Lossless historical-to-roadmap crosswalk

`docs/qa/phone/phone_only_roadmap_crosswalk.csv` preserves every required
TASK-045 `phone-coverage-001`…`phone-coverage-026` row and every TASK-045A
`A001`…`A017` row. It records current status, evidence freshness, Phone Full
applicability, exactly one owner task, allowed terminal status and release
effect. `A001` is owned by TASK-063 as a static audit-preservation row and can
never count as product coverage;
paired/TV-only rows stay deferred and retain their old release blockers.

Runtime discovery is append-only: new screen/state/transition/boundary rows are
added to the active task ledger and crosswalk; required rows may not be deleted,
renamed, merged or silently reclassified. TASK-063 must reject a missing,
duplicate or merged required row and any owner-task mismatch.

In the crosswalk, `covered_or_release_blocking_blocked_star` expands only to
`covered`, `blocked_by_boundary`, `blocked_by_tooling` or
`blocked_by_external_state`; every blocked value has `blocks_release`.
`not_run_out_of_scope` is allowed only for an explicitly non-phone or currently
unapproved/not-reachable row and becomes invalid immediately if runtime
discovery makes that row approved and reachable.

## Current eligibility decision

No phone runtime execution task is currently eligible. TASK-057 is the next
planned task, but it is blocked before its first device action because the
current repository authority does not prove all of the following together:

1. a task-bound mapped and authorized phone alias;
2. current canonical Phone Full artifact integrity/provenance and compatibility
   with the installed state;
3. an approved local-only synthetic-session passport;
4. an approved non-destructive first-launch fixture;
5. exact evidence retention, cleanup/rollback and Security approval.

Historical installed-newer presence and historical screenshots/logs do not
satisfy these gates. Ordinary downgrade rejection must not be bypassed.

## Owner action required before TASK-057 runtime preflight

The owner must approve, through public-safe aliases and ignored local contracts:

- the one phone as the current task lane and a bounded read-only authorization
  check;
- the exact Phone Full build selection and a permitted non-mutating
  integrity/compatibility oracle;
- a synthetic test-only session fixture and task-bounded passport, without
  publishing credentials, tokens or account values;
- a pre-provisioned clean first-launch state that does not require Codex to
  clear data, uninstall, downgrade or bypass platform safety;
- local-only evidence storage, retention, cleanup/rollback and kill-switch
  terms.

If any item is unavailable, TASK-057 must publish only a blocked public-safe
readiness result and stop before runtime.

## Global phone-task gates

Every TASK-057…063 task must satisfy all applicable gates before runtime:

- **Device:** exact public-safe alias, current mapping, authorization, unchanged
  bounded snapshot and no raw serial/IP publication.
- **Build:** exact Phone Full family binding, current provenance/integrity and
  installed compatibility; no decompile, modification, patch, downgrade
  override, uninstall or clear-data operation.
- **Fixture:** synthetic test-only identity/session and state provenance; never
  a real or unknown preserved session.
- **Security:** task-local Security/Prod-safety `GO`, minimal action budget,
  kill switch, no real payment/account mutation, no network shaping and no
  external QR/browser traversal.
- **Evidence:** fresh run-window screenshot visual inspection plus UI tree and
  bounded target-app marker/log are mandatory for every covered screen and
  transition; screenshot/XML mismatch,
  recurrence, retry and recovery are first-class events. Raw media, paths,
  identifiers, hashes and QR targets remain ignored/local-only.
- **Cleanup:** close overlays, return to the approved safe state, verify no
  transaction/account/session mutation, stop capture, retain only approved
  local evidence and publish redacted aliases/statuses.

Every runtime task records a checkpoint before navigation, including public-safe
screen alias, state category, evidence status, focus/action categories and a
risk/hypothesis note. An anomaly is written immediately before continuing or
recovering. If screenshot, UI tree or bounded target-app log/marker is missing,
the row is `blocked_by_tooling` and `blocks_release`; partial modalities never
produce `covered`.

For every approved and currently reachable row, `not_run_out_of_scope` is
forbidden. Such a row must be `covered` or a release-blocking `blocked_*` status.
Each runtime task closes with exact expected/actual/covered/blocked/not-reachable
counts and zero missing or duplicate required rows.

Visible QR is mandatory inventory. Before claiming decode unavailable, use the
established ignored `.qa_local/tools/qrdecode/` `jsqr` path or reference the
prior local-only decode artifact for an identical recurrence. Decode/tool
failure is `blocked_by_tooling` plus a process anomaly; never follow or publish
the raw target.

## Acceptance criteria

- Exactly one phone-only roadmap with TASK-057…063 dependencies and release
  gates is authoritative.
- Existing TASK-041…055 history and status values are preserved.
- Deferred TV/Stick/other-family work is marked by owner policy, not completed.
- Repository/static readiness, historical evidence and fresh runtime evidence
  remain distinct.
- No physical runtime or local raw authority is accessed in TASK-056.
- TASK-057 is recorded as next planned but runtime-blocked, with exact owner
  actions and fail-closed first-action semantics.
- QA A, QA B, Security/Prod-safety and Docs/Scribe independently return GO with
  no open R0/R1 findings.
- Required static verification passes before task/default-branch integration.

## Verification

```text
git status --short --branch
git diff --check
python automation/quality/official_export_index.py validate-epic --root .
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

Do not run an unfiltered suite or read/restore the Security-forbidden local
TASK-045 source merely to claim a full-suite PASS.

## Stop conditions

Stop and record a blocker if remote default drifts, a required reviewer rejects
the plan, a raw/local-only value could enter tracked output, or execution would
require credentials, a real/unknown session, payment, account mutation,
destructive reset, downgrade bypass, network shaping or external traversal.

TASK-056 closes after verified branch/default integration. It must not execute
TASK-057 or any other independent runtime task in this thread.
