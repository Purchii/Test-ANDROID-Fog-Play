# TASK-022 - Xbox-like gamepad full screen inventory

## Итог

Статус: `completed_with_boundaries`.

Режим: `NON_AUTONOMOUS`. Ветка задачи:
`qa/task-022-xbox-gamepad-screen-inventory`; detected default branch: `main`.
Default branch integration/push authorized after final TASK-022 report by the
explicit owner command `пушь в мастер`; detected default branch is `main`.

Инвентаризация выполнена на утвержденной Android TV lane с физически
подключенным owner Xbox-like gamepad после первоначальной ADB/gamepad preflight
попытки. Raw evidence, screenshots, XML, QR targets, phone/OTP, device
identifiers, server/tariff/payment values and private component values remain
local-only under ignored evidence roots.

## Ключевые отличия от TASK-020

- Bottom-right gamepad hints confirmed on auth phone screen after owner pressed
  the physical gamepad once: categories `A/select` and `B/back`; TASK-020 D-pad
  inventory did not record these hints.
- Before physical gamepad activation, ADB-emulated `BUTTON_A` reached and then
  stayed on the connect-device gate. After physical gamepad activation,
  selecting a concrete server with gamepad `BUTTON_A` reached a
  payment/session-activation boundary and then payment QR, not the TASK-020
  connect-device gate.
- Payment QR was decoded local-only via the established `jsqr` path; public
  metadata records only target category and `https` scheme category. No external
  navigation, payment or stream/session start occurred.
- `BUTTON_X` was not a safe no-op in the sampled deep catalog state: it activated
  the focused game card and opened game detail. Subsequent `START` reached a
  Steam-account connection boundary. `Y`, `SELECT`, `L1` and `R1` produced no
  additional visible transition on that boundary in the sampled sequence.
- Owner later clarified that the physical gamepad can sleep, causing the
  bottom-right hint block to disappear. TASK-022 therefore records hint
  visibility as conditional on active physical-controller state and treats the
  un-rechecked base screens as matching prior TASK-020 remote/D-pad behavior
  unless a focused TASK-022 checkpoint shows otherwise.
- The owner-requested Settings Gamepad recheck opened the active controller
  configuration screen for `Xbox Wireless Controller`, with button mapping rows
  and the gamepad diagram visible. No reset, remap, assignment or pairing
  mutation was performed.

## Evidence

Local evidence roots:

- `task-022-xbox-gamepad-20260703T110303Z`
- `task-019-20260703T111540Z`

Public-safe machine summary:

- `docs/qa/reports/task022_xbox_gamepad_full_screen_inventory.summary.json`

No raw QR URL/path/query/token, phone/OTP, device identifier, screenshots, XML,
payment amount or server/tariff values are published in this report.

## Closure Ledger

| # | Screen family / branch | Status | Evidence ids | Notes |
|---|---|---|---|---|
| 1 | Auth phone entry with keyboard | `covered` | `012`, `013` | Physical gamepad press produced bottom-right A/B hints. Auth values stayed local-only. |
| 2 | Onboarding slides | `covered` | `014`-`017` | `BUTTON_A` advanced onboarding and returned to catalog. |
| 3 | Games catalog top / rail states | `covered` | `017`, `018`, `028`, `044`, `046`, `047`, `069` | Expanded/collapsed rail and catalog recurrence captured. Catalog did not show bottom-right hints in sampled states. |
| 4 | Games catalog long grid | `covered` | `050`-`059` | Multiple top/mid/deep scroll samples captured via `DPAD_DOWN`; complete game-title enumeration is out of scope. |
| 5 | Game detail / pricing / server selection | `covered` | `019`-`021`, `060`, `061`, `070`-`073` | Focusable server/tariff/detail states captured. Recheck after owner narrowing again reached payment wait/QR after selecting a server. Raw values not published. |
| 6 | Connect-device gate before physical activation | `covered` | `007`-`010` | Pre-physical-gamepad checkpoint: ADB-emulated `BUTTON_A` did not satisfy physical controller gate. |
| 7 | Payment wait and payment QR | `blocked_by_boundary` | `022`-`028`, `070`-`073`, `qr_decode_024_payment_qr`, `qr_decode_073_payment_qr_recheck` | QR decoded local-only twice; no payment/link/session action. Original `B`/Back did not recover; force-stop/relaunch did. |
| 8 | Session journal empty | `covered` | `029`, `030` | Empty/journal route sampled from rail. |
| 9 | Steam top-up QR | `blocked_by_boundary` | `031`, `032` | Recurrence of TASK-020 QR; raw target not opened or republished. |
| 10 | Feedback QR / question route | `blocked_by_boundary` | `033`, `034` | Route sampled as QR/external boundary; no external navigation. |
| 11 | Settings root | `covered` | `035`, `036` | Root with settings cards/logout area captured. |
| 12 | Settings promo codes | `blocked_by_tooling` | `037`, `038`, `043`, `044` | Intended gamepad subflow opened logout confirmation instead; `No` selected, no account mutation. |
| 13 | Settings gamepad setup | `covered` | `040`-`042`, `075`-`083` | Focus ambiguity was remediated by targeted navigation: `DPAD_UP` to promo card, `DPAD_RIGHT` to Gamepad card, then `A`. Active gamepad configuration screen was captured; reset/remap/pairing mutation not executed. |
| 14 | Logout confirmation boundary | `blocked_by_boundary` | `037`, `038`, `043`, `044` | Logout was not confirmed; safe `No` path returned to catalog. |
| 15 | Search entry / keyboard | `blocked_by_tooling` | `045`, `046`, `048`, `049` | In this Xbox/gamepad state, `nav_games` stayed focused and `nav_search` was not focusable in XML; TASK-020 D-pad Search coverage remains separate prior evidence. |
| 16 | Steam-account connection boundary | `blocked_by_boundary` | `062`-`069` | No visible QR on sampled boundary; no external Steam action. `B`/Back did not recover; force-stop/relaunch returned to catalog. |
| 17 | How-to-Steam instruction QR | `not_run_out_of_scope` | `owner_scope_update`, `TASK-020` | Not rechecked after owner narrowed TASK-022; prior TASK-020 local-only QR decode remains baseline. |
| 18 | Own-Steam toggle warning | `not_run_out_of_scope` | `owner_scope_update`, `TASK-020` | Not rechecked after owner narrowed TASK-022; no account or Steam mutation. |
| 19 | Virtual gamepad QR | `not_run_out_of_scope` | `owner_scope_update`, `TASK-020` | Initial pre-physical path reached the connect-device gate, but this QR branch was not re-entered after owner narrowed scope. |
| 20 | Buy-gamepad purchase boundary | `not_run_out_of_scope` | `owner_scope_update`, `TASK-020` | Purchase boundary was not rechecked; no purchase or external navigation attempted. |
| 21 | Search no-results | `not_run_out_of_scope` | `owner_scope_update`, `TASK-020` | Search entry was blocked in TASK-022 before a query; TASK-020 D-pad evidence remains prior baseline only. |
| 22 | Search results and result-to-detail | `not_run_out_of_scope` | `owner_scope_update`, `TASK-020` | Search entry was blocked in TASK-022 before results; TASK-020 D-pad evidence remains prior baseline only. |
| 23 | External TV screensaver | `not_run_out_of_scope` | `owner_scope_update`, `TASK-020` | Not observed or intentionally triggered in TASK-022 after owner narrowed scope. |
| 24 | Gamepad hint sleep visibility | `covered` | `013`, `070`, `075`, `079`, `080` | Owner confirmed the physical gamepad can sleep and hints can disappear; hints are conditional on active gamepad state. |
| 25 | Payment completion / paid stream session | `not_run_out_of_scope` | `022`, `024`, `073`, `qr_decode_024_payment_qr`, `qr_decode_073_payment_qr_recheck` | Forbidden without approved fixture; no payment or stream/session start. |
| 26 | External QR/browser/WebView traversal | `not_run_out_of_scope` | `032`, `034`, `024`, `073` | QR targets were decoded/referenced local-only and not opened. |

Screens/branches counted: 26.

## Anomalies

- Initial redacted metadata accidentally included an account-like visible label;
  the local redacted metadata was overwritten with category-only text and the
  remediation was recorded.
- Generic package alias resolve failed; the prior confirmed explicit relaunch
  path was used locally.
- ADB target selection became ambiguous because an offline ADB-over-network
  endpoint was listed; subsequent commands used an explicit authorized device
  alias.
- Payment QR and Steam-account boundary did not recover with `B` or Android
  Back; force-stop plus explicit relaunch recovered safely.
- On the repeated server-selection QR checkpoint, recovery used force-stop
  directly because the original `B`/Back failure pattern was already confirmed.
- Search could not be opened from the sampled Xbox/gamepad rail state because
  focus stayed on Games and Search was not focusable in XML.
- Settings subflow probing had focus-target ambiguity and unexpectedly reached
  logout confirmation; logout was declined.
- Active gamepad settings screen did not exit with `B` or Android Back in the
  sampled state. A UI-tree-derived tap on the safe `Close` control returned
  without reset/remap.

## Risks And Unknowns

- Search no-results/results were not re-covered in TASK-022 because Xbox/gamepad
  focus acquisition to Search was blocked. TASK-020 D-pad coverage remains prior
  evidence, not proof of Xbox Search coverage.
- Settings promo-code subflow remains blocked for Xbox/gamepad focus targeting.
  The Gamepad setup screen itself is covered, but mutating assignment/reset/
  remap/pairing paths were intentionally not executed.
- Complete game-title data enumeration is out of scope. The catalog grid was
  sampled across multiple segments only.
- Payment, checkout completion, external QR traversal and paid stream/session
  start remain forbidden without a separate approved fixture.

## Handoff

Next work should either add a safer focus oracle/helper for Xbox Search and
Settings subflow targeting, or treat those rows as known controller-navigation
blockers for product regression tracking. Any future payment/session work needs
separate staging/non-real-payment approval.
