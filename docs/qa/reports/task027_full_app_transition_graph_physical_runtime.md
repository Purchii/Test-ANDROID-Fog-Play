# TASK-027 full app transition graph physical runtime

Mode: `NON_AUTONOMOUS`

Current status: `blocked`

TASK-027 is the fresh selected-lane task for full reachable approved transition
graph coverage. It starts from TASK-025B as a partial baseline only. TASK-025B
does not count as full transition graph closure.

Public-safe machine-readable report:
`docs/qa/reports/task027_full_app_transition_graph_physical_runtime.summary.json`

## Scope

TASK-027 may cover safe reachable native transition branches on the approved
selected Android TV lane:

- launch, foreground and recovery transitions;
- catalog rail, focus and long-list behavior;
- Search input, no-results and recovery;
- Settings root, promo and Gamepad safe-entry branches;
- game card focus-to-detail and server-list sampling;
- QR, payment-like, account-like and stream/session boundaries as terminal
  guarded graph nodes;
- Home and foreground, force-stop plus relaunch, and external ambient recovery.

## Not A Value Inventory

Game and server screens can change over time. TASK-027 must assert stable
screen categories, transition outcomes, focus/scroll behavior, redaction and
boundary handling. It must not assert fixed game titles, server counts, server
aliases, prices, hardware strings, ping values or complete row enumeration.

## Boundary Rules

Real payment, paid session start, stream/WebRTC/media playback, external
QR/WebView/browser traversal, Steam/account connection, profile/account
mutation and network/offline manipulation remain forbidden unless a later
separate task explicitly approves them. Visible QR targets may be decoded only
into local-only evidence and must not be opened or followed.

## Preflight

TASK-027 redaction-safe preflight is confirmed for this thread: the physical
target is available and authorized, selected aliases are refreshed, the
Television Full APK family is present, the APK hash was recorded local-only,
the synthetic QA env exists, ignored local evidence storage is prepared and
cleanup/recovery policy is explicit.

Physical app runtime is still blocked pending a new QA and Security approval
for APK install/launch and graph navigation. Raw APK paths/hashes, phone/OTP
values, device identifiers, screenshots, XML, logs, videos, QR targets, private
routes/endpoints, account-like values and payment/session data remain
local-only and are not committed.
