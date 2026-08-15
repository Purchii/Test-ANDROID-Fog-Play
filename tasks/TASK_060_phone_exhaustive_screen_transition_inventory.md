# TASK-060 — Phone Full exhaustive screen, state and transition inventory

## Contract

- Mode: `BOUNDED_AUTONOMOUS`; runtime is `PROD_CONDITIONAL`.
- Dependencies: TASK-059 aggregate `PASS`, all required approved/reachable rows
  `covered`, zero release-blocking rows, cleanup confirmed, and current TASK-057 plus Security
  lane/build/fixture authority.

## Goal and acceptance

Close the full approved Phone Full graph across navigation branches, search,
catalog/list segments, detail variants, menus expanded/collapsed, overlays,
loaders, errors, empty/entitlement states, recurrence and safe returns. Runtime
discovery adds rows; it never silently merges or removes them. A coverage ledger
must list every currently reachable approved screen family and safe branch as
`covered`, `blocked_by_boundary`, `blocked_by_tooling`, or
`blocked_by_external_state`, with row-level evidence ids and evidence status.
`not_run_out_of_scope` is allowed only for a row explicitly excluded from the
approved Phone Full scope before runtime and is forbidden for approved
reachable rows.

A bottom-of-list, recurring QR/settings screen, screensaver recovery or terminal
ledger count is only a checkpoint. Full coverage requires all reachable
branches terminally classified and every covered edge to have distinct
from/to checkpoints with fresh visual/UI-tree/log evidence. All anomalies are
recorded immediately with trigger, expected/observed result, status, alias,
cause hypothesis and test implication.

Before continuing from every observed state record its screenshot-inspected
checkpoint, UI tree, bounded target-app log/marker, focus/action categories and
risk/hypothesis. Missing modalities are `blocked_by_tooling` / `blocks_release`;
anomalies are recorded immediately. `not_run_out_of_scope` is forbidden for
approved reachable rows.

## Tracked deliverables and closure

Tracked ledgers: crosswalk intake, scenario, screen/state, transition,
long-list/menu, overlay/recurrence, anomaly, boundary and cleanup. They use the
TASK-058 common columns plus `parent_branch_id`, `discovered_during_run`,
`list_segment`, `menu_state`, `recurrence_of` and `visual_xml_match`. Discovery
is append-only. Closure requires exact required plus discovered row counts,
zero missing/duplicate/merged rows and a terminal status for every row.
Revalidate TASK-057 before each resumed run. PASS requires all approved
reachable rows covered; every `blocked_*` retains `blocks_release`.

A blocked or partial TASK-059 closure cannot authorize TASK-060.

## Gates, safety, cleanup and release effect

- Revalidate all TASK-057 gates and Security budget before every resumed run.
- No destructive state reset, real session/payment, network shaping or external
  QR/browser action. System ambient/screensaver surfaces remain external
  evidence, not app coverage.
- Cleanup safely backs out of each branch or uses an approved non-destructive
  force-stop/relaunch recovery, then verifies fixture state and local capture.
- Any approved reachable row without eligible fresh evidence or permitted
  blocker keeps full phone coverage false and blocks release.
