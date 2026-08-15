# TASK-058 — Phone Full first-launch and pre-auth coverage

## Contract

- Mode: `BOUNDED_AUTONOMOUS`; runtime is `PROD_CONDITIONAL`.
- Dependencies: TASK-057 `GO_RUNTIME` and an owner-approved, pre-provisioned
  clean first-launch fixture that needs no destructive reset.

## Goal and acceptance

Capture every approved safely reachable state and transition from OS launch
intent through first-render, loading, onboarding/legal/consent/auth-entry,
retry/error/empty and back/exit behavior. Maintain explicit screen, state,
transition, overlay, recurrence, anomaly, boundary and cleanup ledgers. Long or
paged content must record initial/later segments and truncation/lazy-loading.

Every approved reachable row must be `covered` with fresh run-window screenshot
visual inspection, UI tree and bounded target-app marker/log,
or carry one permitted terminal blocker. XML never substitutes for visual
inspection. Historical evidence cannot count.

Before every navigation action record a checkpoint with screen alias, state,
evidence status, focus/action categories and risk/hypothesis. Record anomalies
immediately. A missing modality is `blocked_by_tooling` / `blocks_release`.
`not_run_out_of_scope` is forbidden for approved reachable rows.

## Tracked deliverables and closure

Tracked ledgers: scenario, screen/state, transition, overlay/recurrence,
anomaly, boundary and cleanup. Common columns are `row_id`, `source_crosswalk_id`,
`approved_scope`, `reachable`, `status`, `screen_alias`, `state_category`,
`focus_category`, `action_category`, `evidence_status`, `screenshot_id`,
`ui_tree_id`, `log_marker_id`, `reason_code`, `release_effect` and
`cleanup_status`; transitions also require distinct `from_checkpoint_id` and
`to_checkpoint_id`. Closure publishes exact required/discovered/covered/blocked
counts with no missing/duplicate rows. Revalidate TASK-057 authority before
each resumed run. PASS requires all approved reachable TASK-058 rows covered.

## Gates, safety, cleanup and release effect

- Device/build/fixture passport from TASK-057 must still be current and exact.
- No real/unknown session, credential entry, account mutation, external
  browser/QR traversal, network shaping, clear data, uninstall or downgrade.
- Cleanup returns to the owner-approved safe pre-auth state without creating an
  account/session, verifies capture shutdown and preserves raw media locally.
- An unreproducible genuine first launch, missing visual modality, unclassified
  screen/transition or unsafe boundary is release-blocking.
