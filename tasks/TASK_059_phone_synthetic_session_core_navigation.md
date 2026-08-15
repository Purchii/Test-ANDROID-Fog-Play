# TASK-059 — Phone Full synthetic-session and core navigation coverage

## Contract

- Mode: `BOUNDED_AUTONOMOUS`; runtime is `PROD_CONDITIONAL`.
- Dependencies: TASK-058 aggregate `PASS`, all required approved/reachable rows
  `covered`, zero release-blocking rows, cleanup confirmed; a fresh task-authoritative
  synthetic-session passport; and current TASK-057 plus Security gates.

## Goal and acceptance

Establish only the approved synthetic test session through the approved fixture
mechanism, then inventory core home, primary navigation, search entry, catalog,
detail and settings routes that are safely reachable. Record auth loading,
captcha/error/retry/expired-session and unexpected preserved-session states as
first-class events. Each screen/state/transition requires the TASK-058 evidence
triplet and explicit focus/action categories.

The task cannot PASS if session provenance is unknown, a real account is
present, any approved core route is absent from the ledger, or recovery hides a
first failure.

Checkpoint before navigation and record screen/state/evidence/focus/action/risk
fields; anomalies are recorded immediately. Covered rows require a fresh
visually inspected screenshot, UI tree and bounded target-app log/marker.
Missing modalities are `blocked_by_tooling` / `blocks_release`, and
`not_run_out_of_scope` is forbidden for approved reachable rows.

## Tracked deliverables and closure

Tracked ledgers: session-provenance, auth-state, screen/state, transition,
anomaly, boundary and cleanup, using the TASK-058 common columns plus
`session_passport_alias`, `passport_freshness` and `mutation_observed`.
Closure requires exact crosswalk ownership and expected/actual/covered/blocked
counts with zero missing/duplicate rows. Revalidate TASK-057 and passport TTL
before each resume. PASS requires approved synthetic provenance, zero mutation
and all approved reachable core rows covered.

A blocked or partial TASK-058 closure cannot authorize TASK-059.

## Gates, safety, cleanup and release effect

- Revalidate phone/build/passport TTL, evidence path, action budget, kill
  switch and Security `GO` before the first input.
- Never publish or request credentials/tokens/account values; never mutate
  profile, subscription, payment or real-user state.
- Cleanup uses only the approved fixture method, returns to its defined safe
  state and verifies no unauthorized session/account change. Logout is
  forbidden unless separately fixture-approved and non-destructive.
- Unknown session provenance, auth mutation, missing evidence or core-route gap
  blocks release and TASK-060.
