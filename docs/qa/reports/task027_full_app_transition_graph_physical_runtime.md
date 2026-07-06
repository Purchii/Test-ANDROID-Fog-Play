# TASK-027R full app transition graph physical runtime

Mode: `NON_AUTONOMOUS`

Current status: `full_graph_closed` by terminal ledger classification.
Continuation is not required for TASK-027R unless the owner opens a new task to
solve the rail focus/input tooling blocker.

TASK-027R executed the approved selected-lane physical runtime boundary after
the TASK-027 preparation/preflight thread. TASK-025B, TASK-020 and TASK-023
remain baselines only; they do not count as this run's full graph closure.

Public-safe machine-readable report:
`docs/qa/reports/task027_full_app_transition_graph_physical_runtime.summary.json`

## Runtime Result

The selected APK update/install and explicit app launch/relaunch were executed
under post-preflight QA/Security approval. Runtime evidence was captured as
local-only screenshots/XML/log/crash artifacts under ignored evidence storage.
Public artifacts reference only checkpoint IDs and category-level findings.

Covered or terminally classified in TASK-027R runtime:

- launch/relaunch, external ambient/screensaver recurrence and recovery to
  actionable catalog;
- catalog rail focus movement and dynamic catalog scroll sampling;
- game card activation into game detail and server-list sampling without
  payment/session activation;
- Search keyboard route and confirmed recovery trap;
- Settings root, safe Gamepad entry and Gamepad close recovery;
- Home/foreground persistence from a safe post-auth state;
- catalog QR, payment/session-like, profile/account and external traversal
  boundaries as guarded terminal categories.
- continuation relaunch to actionable catalog, followed by bounded safe
  rail-route attempts that remained on the catalog instead of opening session
  journal, Steam/top-up or feedback destinations.

Closure basis:

- `full_graph_closed` means every currently reachable approved branch has a
  terminal ledger classification: `covered`, `blocked_by_boundary`,
  `blocked_by_tooling`, `blocked_by_external_state` or
  `not_run_out_of_scope`.
- Session journal, Steam/top-up QR and feedback QR destinations are not covered.
  They are terminally `blocked_by_tooling` with confirmed no-destination
  catalog evidence.
- Search typed no-results remains `blocked_by_tooling`.
- Complete dynamic game-title and server-row enumeration remains out of scope;
  TASK-027R asserts categories, focus/scroll behavior, boundaries and
  redaction only.
- Payment completion, stream/session start, external browser/WebView traversal,
  account/profile mutation and network/offline manipulation were not performed
  and remain guarded terminal categories.

## Anomalies

All anomalies are recorded immediately as a global project rule. Current
TASK-027R public-safe anomaly IDs are tracked in the summary JSON:

- `ANOM-025B-001` rechecked: launch/ambient recovery can enter prolonged
  loader; clean direct cleanup relaunch recovered catalog.
- `ANOM-025B-002` rechecked: Search keyboard Back/Escape recovery trap
  persisted.
- `ANOM-025B-003` rechecked: precise Gamepad safe-entry route succeeded without
  logout/profile mutation.
- `ANOM-027R-001` through `ANOM-027R-007`: evidence capture tooling, QR decode
  tooling, server-list Back recovery, promo keyboard trap, post-cleanup loader,
  adb helper wrapper and rail-route tap no-op anomalies.
- `ANOM-027R-008`: continuation relaunch reached actionable catalog, but
  D-pad, visual-coordinate tap and bounded key sanity sampling did not move
  focus or open session journal, Steam/top-up or feedback rail destinations;
  UIAutomator did not expose the visible rail labels as target nodes.

## Boundaries

No real payment, paid session, stream/WebRTC/media playback, external QR or
browser traversal, Steam/account connection mutation, profile/account mutation,
network/offline manipulation, APK modification or security bypass was
performed. Raw APK hashes, device identifiers, account-like values, QR targets,
screenshots, XML, logs and private runtime values remain local-only and are not
committed.

## Validator Hardening

The TASK-027 validator now treats session journal, Steam/top-up QR and feedback
QR as required directed transition families. It also blocks premature
`full_graph_closed` claims unless runtime status is `closed_by_ledger` and
`unverified_areas` is empty. This continuation also restricts accepted
TASK-027 evidence IDs to the public-safe checkpoint/QR ID shapes used by the
runtime ledger, so fabricated placeholder evidence IDs do not satisfy closure.

## Handoff

This run is `NON_AUTONOMOUS`. The task branch may be pushed after verification,
but detected default branch `main` must not be merged or pushed without an
explicit owner command.

A future independent task may try to solve the rail focus/input blocker only
with a new approved targeting oracle or owner-approved runtime scope. It must
not treat TASK-027R no-op evidence as destination coverage.
