# TASK-063 — Phone-only evidence aggregation and QA release gate

## Contract

- Mode: `BOUNDED_AUTONOMOUS`.
- Repository aggregation: `PROD_SAFE_OFFLINE_STATIC_ONLY`.
- Dependencies for PASS: TASK-058 through TASK-062 each PASS with zero
  release-blocking rows and cleanup confirmed plus authoritative current
  TASK-057/Security gate records. Terminal blocked predecessors may be ingested
  only to publish `blocks_release`.

## Goal and acceptance

Aggregate only validated Phone Full v2 evidence and exact row-level ledgers into
one phone-only release decision. The generator must reject missing/stale/hash-
drifted authority, historical audit-only evidence, blocked rows presented as
PASS, absent visual modalities, unresolved R0/R1 findings, incomplete cleanup
and any cross-family substitution.

Phone PASS requires every required first-launch, pre-auth, synthetic-session,
core-navigation, exhaustive graph, input/lifecycle and boundary row to have
eligible fresh evidence and all required reviewer/cleanup gates to pass. A
terminal blocker remains visible and produces `blocks_release`.

## Tracked deliverables and closure

Tracked outputs: crosswalk validation ledger, task-authority ledger,
coverage-rollup ledger, reviewer/cleanup gate ledger and v2 phone-only release
summary. Required columns include `source_task`, `source_row_id`, `owner_task`,
`applicability`, `freshness`, `terminal_status`, `evidence_ids`,
`modality_complete`, `cleanup_status`, `review_status` and `release_effect`.

The gate requires all 26 TASK-045 rows and all 17 TASK-045A rows from
`docs/qa/phone/phone_only_roadmap_crosswalk.csv` exactly once, plus every
append-only runtime discovery. It rejects missing, duplicate, renamed, merged
or owner-mismatched rows. `A001` remains audit-only/non-coverage and paired/TV
rows remain deferred. For approved reachable Phone Full rows,
`not_run_out_of_scope` is invalid: only `covered` or release-blocking
`blocked_*` is allowed. Revalidate every input authority/hash/freshness and
review/cleanup gate on each generation; no cached PASS is reused.

TASK-063 may aggregate a terminal blocked/partial predecessor only to publish
`blocks_release`; it cannot turn that closure into PASS or authorize a later
runtime task. A phone PASS requires every runtime predecessor to have PASS,
zero release-blocking rows and confirmed cleanup.

## Safety, evidence, cleanup and release effect

- No device, APK, app, account, network, QR or raw-evidence action is allowed.
- Read only tracked public-safe manifests, ledgers and summaries; raw serials,
  paths, hashes, accounts, package values, QR targets and media remain local.
- Cleanup is repository-only: verify deterministic output and no local-evidence
  inclusion.
- The result governs Phone Full only. It cannot complete or unblock YandexTV,
  SberBox, AOSP Stick, generic TV, Television Full, cross-family or five-APK
  claims, which retain their prior statuses and owner-policy deferral.
