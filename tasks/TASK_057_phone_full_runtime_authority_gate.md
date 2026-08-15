# TASK-057 — Phone Full runtime authority and fixture readiness gate

## Contract

- Mode: `BOUNDED_AUTONOMOUS`.
- Repository checks: `PROD_SAFE`; any bounded device metadata check:
  `PROD_CONDITIONAL` after Security `GO`.
- Dependencies: completed TASK-056 and public TASK-042/TASK-045/TASK-045A
  authority.
- Current status: `inactive_completed_blocked_runtime` / readiness `blocked` /
  `BLOCK_RUNTIME` / `blocks_release`.

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

## 2026-08-15 closure result

The tracked ledger contains exactly seven rows: two `observed_pass` and five
blocking. Fresh `phone-current-001` mapping/authorization stayed unchanged
across three snapshots, and ordinary downgrade rejection was preserved without
bypass. Candidate `main-apk-03` presence, integrity, provenance, signature,
version relation, target-SDK and ABI metadata were confirmed; device/candidate
ABI intersection is true. However, candidate min-SDK metadata was not emitted
and installed/candidate signing certificates mismatch. The fresh
`candidate_newer` relation remains distinct from the historical installed-newer
build and historical `phone-realme-001` was not reused without exact mapping.

Current synthetic-session, non-destructive clean-first-launch and
evidence/cleanup passports are absent. Security remains `BLOCK_RUNTIME`.
Metadata cleanup confirmed stable snapshots and no mutation, but it cannot
infer the missing passport row. The bounded budget was one non-overwrite
candidate copy, one hash/signature/metadata extraction, three ADB snapshots
and four per-device read-only commands; all install, app/UI/navigation, auth,
account, payment, session, network and external-boundary action counts were
zero. TASK-058 remains blocked.

Public-safe owner actions are to provide a signer-compatible, non-downgrade
Phone Full candidate with permitted min-SDK metadata; a current ignored/local-
only synthetic test-session passport; a pre-provisioned non-destructive clean-
first-launch fixture; and a current evidence/cleanup passport covering
retention/redaction, action budget, kill switch and cleanup/rollback. Security
`GO_RUNTIME` may be reconsidered only after all seven rows are freshly
revalidated.

## Safety, evidence, cleanup and release gate

- Do not navigate the app, authenticate, clear data, uninstall, install over a
  downgrade, modify/decompile/patch an APK, or inspect raw TASK-045 evidence.
- Keep serials, paths, full hashes, package identifiers, credentials and raw
  command output ignored/local-only; publish aliases, categories and status.
- Cleanup ends metadata capture, verifies that no install/app/account/session
  mutation occurred and records the unchanged bounded device snapshot.
- Any missing acceptance item keeps `BLOCK_RUNTIME` and `blocks_release` for
  TASK-058…063.
