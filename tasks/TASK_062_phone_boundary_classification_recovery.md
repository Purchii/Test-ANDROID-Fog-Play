# TASK-062 — Phone Full boundary classification and safe recovery

> Superseded on 2026-08-16 as internal stage 5 of
> `EPIC-PHONE-001 — Full mobile application test coverage`. This specification
> is retained for lossless objective/history only and must not be executed as
> a separate task, thread or branch.

## Contract

- Mode: `BOUNDED_AUTONOMOUS`; runtime is `PROD_CONDITIONAL`.
- Dependencies: TASK-060 and TASK-061 each aggregate `PASS`, all required
  approved/reachable rows `covered`, zero release-blocking rows and cleanup confirmed, plus
  current TASK-057 and Security gates.

## Goal and acceptance

Inventory every safely reachable payment, QR, legal/WebView, captcha,
entitlement, stream/session-start, external-app and account/settings boundary.
Capture the boundary screen as a first-class state, classify the target only at
category level, record whether navigation was followed (`false`), and verify
safe Back recovery or approved non-destructive force-stop/relaunch recovery.

For each new visible QR, once boundary capture is approved, local-only decode
with the established `.qa_local/tools/qrdecode/` `jsqr` path is mandatory. For
an identical recurrence, reference the prior local-only decode artifact instead
of decoding it again. If decode is unsafe, unavailable or fails, classify the
row `blocked_by_tooling`, record an immediate process anomaly, stop boundary
progression and safely recover. Raw targets never enter tracked output and are
never followed. A payment screen is a checkpoint, not inventory completion.

Checkpoint before any boundary navigation with screen/state/evidence,
focus/action categories and risk/hypothesis; record anomalies immediately.
Covered boundary/recovery rows require fresh visually inspected screenshot, UI
tree and bounded target-app log/marker. Missing modalities block release;
`not_run_out_of_scope` is forbidden for approved reachable rows.

## Tracked deliverables and closure

Tracked ledgers: boundary, QR-category/reference, recovery-transition, anomaly
and cleanup. Use TASK-058 common columns plus `boundary_category`,
`external_navigation_followed`, `mutation_performed`, `qr_visible`,
`qr_decode_status`, `qr_local_reference_id` and `recovery_status`. Closure
requires exact required/discovered/covered/blocked counts and zero missing,
duplicate or merged rows. Revalidate TASK-057/Security budget before every
resume. PASS requires all approved reachable boundaries covered with
`external_navigation_followed=false`, `mutation_performed=false` and cleanup.

A blocked or partial TASK-060/TASK-061 closure cannot authorize TASK-062.

## Gates, safety, cleanup and release effect

- Revalidate synthetic fixture, action budget, evidence retention and Security
  `GO` before approaching a boundary.
- Never pay, purchase, start a paid/active stream or session, authenticate in an
  external surface, follow QR/browser links, mutate account/profile, shape the
  network or bypass security controls.
- Cleanup returns to the prior approved in-app state and verifies no external
  launch, transaction, account/session or media action occurred.
- An unclassified boundary, followed target, mutation, raw publication or failed
  recovery blocks release.
