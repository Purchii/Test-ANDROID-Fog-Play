# TASK-057 — Phone Full runtime authority and fixture readiness gate

## Contract

- Mode: `BOUNDED_AUTONOMOUS`.
- Repository checks: `PROD_SAFE`; any bounded device metadata check:
  `PROD_CONDITIONAL` after Security `GO`.
- Dependencies: completed TASK-056 and public TASK-042/TASK-045/TASK-045A
  authority.
- Current status: `planned_blocked_by_authority` / `BLOCK_RUNTIME`.

## Goal and acceptance

Establish one task-bound phone lane without executing product navigation. The
task passes readiness only when a fresh bounded record confirms the mapped
authorized phone alias, exact Phone Full family/build alias, permitted build
integrity/provenance and installed compatibility, approved synthetic-session
passport, pre-provisioned non-destructive first-launch state, evidence storage,
action budget, kill switch, cleanup/rollback and Security `GO_RUNTIME`.

Missing or stale fields must become explicit `blocked_by_device`,
`blocked_by_fixture`, `blocked_by_oracle` or `blocked_by_external_state` rows.
Presence, historical installed-newer evidence, task-local TASK-045 authority or
a successful metadata command alone cannot produce PASS.

The readiness matrix has seven independent rows: canonical `main-apk-03`
presence/integrity/provenance; distinct installed-newer build and compatibility;
fresh neutral `current-phone-selector` binding to a new public-safe current
phone alias; preserved ordinary
downgrade rejection; synthetic-session passport; clean first-launch fixture;
and evidence/cleanup passport. Current authority is respectively
`presence_only_integrity_unknown`, `distinct_compatibility_unknown`,
`unresolved_historical_candidate_only`, `rejected_no_bypass`, `policy_only_no_passport`,
`unknown`, and `unknown`. TASK-057 must revalidate each independently.

`phone-realme-001` is historical TASK-045 evidence, not a required current
identity. TASK-057 may reuse that alias only after a fresh exact match; otherwise
it creates a different public-safe alias without publishing raw identity.

## Tracked deliverables and closure

- readiness ledger columns: `authority_id`, `subject_alias`, `current_status`,
  `freshness`, `evidence_status`, `evidence_ids`, `reviewer_gate`, `expires_at`,
  `terminal_status`, `release_effect`, `reason_code`;
- public-safe blocked/ready summary plus cleanup ledger;
- exactly seven required authority rows with zero missing/duplicate/merged rows.

PASS requires all seven rows fresh and `observed_pass` plus Security
`GO_RUNTIME`; otherwise the task closes `blocked` / `blocks_release`. Resume or
device-set change revalidates every row; no prior row is carried forward by
assumption.

## Safety, evidence, cleanup and release gate

- Do not navigate the app, authenticate, clear data, uninstall, install over a
  downgrade, modify/decompile/patch an APK, or inspect raw TASK-045 evidence.
- Keep serials, paths, full hashes, package identifiers, credentials and raw
  command output ignored/local-only; publish aliases, categories and status.
- Cleanup ends metadata capture, verifies that no install/app/account/session
  mutation occurred and records the unchanged bounded device snapshot.
- Any missing acceptance item keeps `BLOCK_RUNTIME` and `blocks_release` for
  TASK-058…063.
