# TASK-020 XL+ - Post-auth native navigation transitions

## Task

Cover bounded post-auth native navigation transitions, screen states, focus
paths, Back/Home behavior and session persistence on the already approved
`tv-tpv-013` lane.

Current owner goal correction:

- The active runtime goal is full screen inventory, not a partial milestone.
- The run must continue autonomously across safe reachable screens and states
  until a closure ledger exists for every currently reachable approved screen
  family/branch.
- A catalog bottom, QR recurrence, Settings recurrence, session-journal empty
  state, screensaver recovery or boundary checkpoint is not completion by
  itself.
- Completion requires each branch/screen family to be marked with evidence as
  `covered`, `blocked_by_boundary`, `blocked_by_tooling`,
  `blocked_by_external_state`, or `not_run_out_of_scope`.

2026-07-03 status update:

- Full screen inventory on the approved Philips-new lane is closed by the
  public-safe screen-family ledger in
  `docs/qa/reports/task020_full_screen_inventory.summary.json`.
- The ledger uses the zero-audit and zero-reset inventory evidence roots and
  marks every safe reachable approved family as covered, boundary-blocked,
  external-state-blocked, or not-run out of scope.
- Payment/checkout, paid stream/session start, external QR traversal and
  profile/account mutation beyond logout were not executed and remain outside
  approved inventory actions.

## Mode

`NON_AUTONOMOUS`

## Branch

```text
qa/task-020-xl-post-auth-navigation-transitions
```

## Production safety

- `PROD_SAFE`: docs, validators, mocked tests, default fail-closed runner and
  public-safe report validation.
- `PROD_CONDITIONAL`: approved local runtime navigation collection on
  `tv-tpv-013` / `tv-tpv-a12-013` with build alias `task-005-local-apk-001`
  and synthetic user alias `qa-user-phone-001`.
- `PROD_CONDITIONAL` owner-approved exception: logout followed by immediate
  relogin on the same synthetic lane was explicitly approved by the owner on
  2026-07-03 for inventory continuity. This exception covers only the
  logout-confirmation screen, confirming return to auth, and canonical
  TASK-019 relogin; it does not approve profile/account mutation.
- `PROD_FORBIDDEN`: payment, WebView/redirect/browser, stream/WebRTC/media
  playback, network/offline manipulation, profile/account mutation,
  private endpoint extraction, proxy/packet capture/TLS bypass, APK
  decompilation/patching/resigning/modification and raw evidence publication.

## Scope

In scope:

- Phase A source-of-truth, safety and fail-closed tooling gate.
- Session preflight from existing auth state.
- Login only if session is absent, using the TASK-019 on-screen keyboard method
  and local-only `.qa_local/secrets/qa_user.env`.
- Native post-auth screen inventory and safe transition sampling.
- D-pad focus path sampling.
- Back behavior and Back recovery.
- Home/foreground and force-stop/relaunch session checkpoints.
- Natural loading, empty, error or entitlement states if encountered without
  forcing negative conditions.
- Boundary detection for payment, WebView, stream/media, account mutation and
  network/offline controls.
- Local-only raw evidence under `.qa_local/evidence/task-020/` and optional
  public-safe summary under `docs/qa/reports/`.

Mandatory runtime auth-input gate:

- TASK-019 already resolved phone entry for this app. This is not an open
  exploration item for TASK-020 or follow-up zero-state audits.
- When a zero-state or expired-session run reaches the phone auth screen, agents
  must use the TASK-019 helper-backed on-screen keyboard method only. Confirm
  the phone screen first, preserve the visible `+7` prefix, enter only the
  remaining local-only synthetic phone digits through the on-screen numeric
  keypad, then tap the visible `OK` keypad control.
- Raw `adb input text` / generic keyevent input is prohibited for verdicts on
  this phone field unless a future task explicitly revalidates it; TASK-019
  already found it unreliable.
- If the helper-backed phone path is not executed, the next captcha/OTP state is
  not verified. Report `unknown` or `blocked_input_path_not_executed`; do not
  report captcha as confirmed `not_reached`, auth as product `fail`, or any
  product behavior from a failed ad hoc input routine.
- Any runtime report that violates this gate is invalid and must be corrected
  before TASK-020/TASK-021 closure.

Mandatory screen checkpoint gate:

- Every newly encountered runtime screen/state must stop navigation until it is
  recorded as a screen checkpoint.
- A checkpoint requires local-only raw evidence, a public-safe screen alias,
  state category, evidence status, focus/action category summary, and a brief
  risk or hypothesis note before any next key/tap/select action.
- Loader, error, captcha, legal WebView, auth, retry, empty/entitlement and
  boundary-like screens must not be skipped as incidental transitions. They are
  first-class inventory items because they can explain user-path mismatches.
- If a screen is transient, record it as `transient_loader`,
  `transient_error`, or another category-level alias with the available
  evidence and the timing/trigger category. Do not convert it into a later
  screen's result.
- If a screen/state has already appeared earlier in the same run or a prior
  evidence run, record the recurrence as its own checkpoint. Reference the
  prior public-safe alias/evidence id, record what matched, record what changed
  if anything, and record the trigger/path that returned to it. Repeated screens
  are evidence for loops, recovery, session persistence and user-path mismatch;
  do not collapse them into the first observation.
- Long scrollable lists, paged lists, lazy-loaded grids and collapsible or
  expandable menus require explicit inventory notes. A single viewport only
  confirms the visible segment. Safe D-pad/scroll samples must record visible
  segment, item-count/truncation evidence where available, lazy-load behavior,
  focus recovery and the current menu state. If a menu can collapse and expand,
  capture both states when safely reachable.
- For the games catalog, screen-level inventory is not the same as a complete
  game-title data audit. Deep D-pad samples may confirm lazy-loaded grid
  behavior, focus movement, title wrapping/truncation, placeholder-like poster
  fallback and right-edge clipping, but they must not be reported as complete
  enumeration unless the list bottom/end condition is actually reached and
  recorded.
- Visible QR codes are part of the screen inventory. They may be decoded into
  local-only raw evidence for QA mapping, but automation must not follow the
  target, open external/browser/payment surfaces, authenticate, or perform any
  transaction. Public outputs must redact raw QR URLs, paths, query strings,
  tokens and payloads; use category-level target metadata plus hash/local
  reference instead.
- QR decoding is a solved local TASK-020 workflow. Before declaring a QR
  `not_decoded`, check whether the same recurring QR already has a local-only
  artifact in the current run, then use the established `jsqr` path under
  `.qa_local/tools/qrdecode/` for new QR surfaces. Absence of `cv2`, `pyzbar` or
  `zxingcpp`, or failure of an improvised decoder script, must be logged as a
  tooling/process anomaly and must not be used as product evidence that the QR
  was unreadable.
- Payment screens are not terminal stop points for full screen inventory. If a
  payment or payment-QR screen appears, capture it, decode visible QR targets
  into local-only evidence, record no payment/navigation/external action, then
  try safe navigation recovery to the previous screen. If navigation cannot
  recover, force-stop/relaunch and continue inventory. Real payment completion
  and real paid session start remain forbidden without an explicitly approved
  fixture.
- If tariff/server selection reaches a device-connection gate before payment or
  streaming, inventory that gate as a first-class pre-session screen. Record
  gamepad/virtual-gamepad options, QR surfaces, focus order, Back recovery and
  force-stop/relaunch recovery. Do not claim payment or stream coverage from a
  device gate alone. On Philips-new, the approved explicit app relaunch helper
  is the observed reliable app recovery path; generic package launch may land
  on Android TV launcher.
- Android TV ambient/screensaver surfaces are external/system interruptions,
  not app screens. If a full-screen scenic, photo, weather-like, launcher-like
  or idle/wake surface appears without app navigation/content, record it as
  possible TV/Android screensaver evidence, note the idle/wake trigger if
  known, recover app foreground, and continue inventory. Do not classify it as
  app crash, blank app screen, completed navigation, or product screen.

Owner-confirmed captcha frontier:

- Product logic normally gives the user three OTP entry attempts and then moves
  to captcha.
- The external authorization service may move to captcha earlier if it detects
  suspicious behavior, before the third wrong OTP attempt.
- The OTP/code entry screen is therefore the pre-captcha frontier for this
  first-run/auth inventory.
- A captcha verdict is valid when runtime evidence confirms the captcha screen,
  even if fewer than three visible wrong OTP attempts were observed. In that
  case, record the observed attempt count and whether early service-side
  escalation is `likely`, `hypothesis`, or `confirmed_by_owner_statement`.
- A captcha absence verdict is invalid unless the relevant OTP/captcha trigger
  path was deliberately executed under approved `PROD_CONDITIONAL` controls.
- If this trigger path is executed, checkpoint after each wrong OTP attempt,
  stop at captcha, and never solve, bypass, inspect challenge internals, or
  publish raw challenge data.
- Wrong-OTP errors may appear as transient bottom snackbar/popup overlays that
  are visible in screenshots but absent from UIAutomator XML. Each wrong OTP
  attempt must include immediate screenshot inspection; XML-only classification
  cannot close the checkpoint.
- Record anomalies immediately. Unexpected navigation outcomes, repeated-screen
  loops, delayed WebView accessibility, focus traps, failed Back/exit actions,
  transient overlays and classifier/screenshot mismatches must become explicit
  anomaly checkpoints with trigger/action, expected result, observed result,
  evidence status, likely/hypothesis cause and test-design implication.

Out of scope:

- Payment, subscription, purchase, billing, checkout, card, wallet or bank.
- WebView, redirect, browser, custom tab or external URL traversal.
- Stream, WebRTC, media playback, player or game-session launch.
- Network/offline manipulation.
- Logout except for the narrow owner-approved 2026-07-03 continuity exception;
  profile/account edit/delete/mutation.
- Private endpoint, deeplink, route, header or payload extraction.
- Proxy, packet capture, TLS/security bypass.
- APK decompilation, patching, resigning or modification.
- Broad compatibility matrix and full Experience QA/craft audit.

## Runtime budget

```text
max_runtime_duration_minutes: 90
max_screens: 40
max_transition_edges: 160
max_actions_total: 500
max_depth_from_post_auth_root: 6
max_focus_moves_per_screen: 24
max_selects_per_screen: 8
max_back_recovery_attempts_per_screen: 4
max_session_checkpoint_screens: 6
max_revisits_per_screen_alias: 3
```

Budget exhaustion is `partial_budget_limited_coverage`, not exhaustive proof
and not a failure by itself.

## Acceptance criteria

- Default runner blocks with `runtime_execution_status=not_run` and makes no
  ADB/device calls.
- Runtime requires explicit `--allow-runtime`.
- Raw output paths stay under `.qa_local/evidence/task-020/`.
- Public summaries stay under `docs/qa/reports/*.json`.
- Boundary keyword/action detection blocks payment, WebView, stream/media,
  account mutation and network/offline manipulation.
- Public aliases reject URLs, raw paths, phone/OTP, device identifiers, private
  endpoint or internal route values.
- Public report validator rejects raw phone/OTP, raw local paths, raw
  screenshots/logs/videos, raw ADB identifiers and private URL/deeplink values.
- Session checkpoint report includes Home/foreground and force-stop/relaunch
  results or explicit `not_run` reasons.
- Boundary transitions use `blocked_by_boundary`, not `pass`.
- Runtime results never claim exhaustive app coverage.

## Verification

```text
git status --short --branch
git diff --check
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python -m pytest -q tests/test_post_auth_navigation_probe.py tests/test_post_auth_navigation_report_validator.py
python -m pytest -q
python -m compileall -q automation tests
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.example.json
python automation/approvals/validate_approval_metadata.py --metadata docs/approvals/approval_metadata.task005.draft.json
python automation/post_auth_navigation/run_post_auth_navigation_probe.py
```

If a public-safe runtime summary is generated:

```text
python automation/post_auth_navigation/validate_post_auth_navigation_report.py --report docs/qa/reports/task020_post_auth_navigation_transition.summary.json
```

## Stop conditions

Stop before selecting or entering any payment, WebView, stream/media,
profile/account mutation or network/offline surface. Stop if raw evidence,
phone/OTP, device identifiers, private endpoints/routes, APK internals or
security bypass details would enter public output. Stop at captcha by recording
category-only evidence; captcha bypass, challenge extraction and automated
captcha solving are forbidden.
