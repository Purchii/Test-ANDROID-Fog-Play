# TASK-061 — Phone Full input, lifecycle and safe recovery coverage

## Contract

- Mode: `BOUNDED_AUTONOMOUS`; runtime is `PROD_CONDITIONAL`.
- Dependencies: TASK-060 aggregate `PASS`, all required approved/reachable rows
  `covered`, zero release-blocking rows, cleanup confirmed, and current TASK-057 plus Security
  gates.

## Goal and acceptance

Exercise only approved phone touch/back/keyboard and lifecycle paths: focus or
selection state, back-stack, foreground/background, orientation/display changes
when supported, safe process stop/relaunch, transient overlay recovery and
session persistence within the synthetic fixture contract. Record before/after
state, first attempt, retry, recovery and cleanup as separate ledger rows.

No successful recovery may erase an initial failure. Each covered transition
requires a fresh visually inspected screenshot, UI tree and bounded target-app
log/marker; tooling gaps and screenshot/XML mismatches are explicit events.

The UI tree and bounded target-app log/marker are mandatory, not optional.
Checkpoint before each input/lifecycle action with screen/state/evidence,
focus/action categories and risk/hypothesis; record anomalies immediately.
Missing modalities are `blocked_by_tooling` / `blocks_release` and
`not_run_out_of_scope` is forbidden for approved reachable rows.

## Tracked deliverables and exact terminal closure

Tracked ledgers: input-attempt, lifecycle-transition, focus/state,
failure/retry/recovery, anomaly and cleanup. Required columns are `row_id`,
`source_crosswalk_id`, `input_or_lifecycle_category`, `approved_scope`,
`reachable`, `before_checkpoint_id`, `after_checkpoint_id`, `first_attempt`,
`retry_index`, `recovery_of`, `status`, `focus_category`, `action_category`,
`evidence_status`, `screenshot_ids`, `ui_tree_ids`, `log_marker_ids`,
`cleanup_status`, `release_effect` and `reason_code`.

Every required and discovered attempt/transition is terminally `covered` or
release-blocking `blocked_*`; no first failure may disappear after retry.
Closure publishes exact expected/actual/covered/blocked/recovered counts and
rejects missing, duplicate or merged rows. Revalidate TASK-057 and current
synthetic-session state before every resumed run. PASS requires all approved
reachable rows covered and cleanup confirmed.

A blocked or partial TASK-060 closure cannot authorize TASK-061.

## Gates, safety, cleanup and release effect

- Exact device/build/session/evidence/Security authority must remain current.
- No clear data, uninstall, downgrade, OS/device reset, load/soak, network
  shaping, real-user action or unknown input target.
- Cleanup restores the approved foreground safe state, releases all injected
  inputs, stops capture and confirms no fixture/account mutation.
- Focus traps, failed back/exit, unsafe recovery, persistence uncertainty or
  incomplete cleanup block release.
