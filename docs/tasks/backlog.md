# Backlog - Android QA Codex bounded tasks

## P0 - workflow/source-of-truth bootstrap

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-000 | Bootstrap Codex docs and source-of-truth | BOUNDED_AUTONOMOUS | qa/task-000-bootstrap-codex-docs | completed |

## P1 - first QA foundation

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-001 | Runtime discovery and smoke bootstrap | BOUNDED_AUTONOMOUS with runtime execution blocked until fixtures approved | qa/task-001-runtime-discovery-smoke-bootstrap | completed |
| TASK-002 | Exported component guard checks skeleton | BOUNDED_AUTONOMOUS if TASK-001 done | qa/task-002-exported-component-guards | completed |
| TASK-003 | Reporting, evidence schema and release gate generator | BOUNDED_AUTONOMOUS if TASK-001 done | qa/task-003-evidence-release-gates | completed |
| TASK-004 | Manual runtime screen and TV focus map templates | BOUNDED_AUTONOMOUS | qa/task-004-runtime-screen-focus-map | completed |
| TASK-005 | Android TV install/launch/focus smoke implementation | NON_AUTONOMOUS runtime task after owner approval | qa/task-005-android-tv-smoke-runtime | limited `tv-tpv-013` smoke executed locally; merged/pushed to `main` by explicit user command |

## P2 - fixtures-dependent QA

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-006 | Test data and fixtures contract draft | NON_AUTONOMOUS | qa/task-006-test-fixtures-contract | completed |
| TASK-007 | Network/offline policy and safe runner | BOUNDED_AUTONOMOUS after policy | qa/task-007-network-offline-policy | completed |
| TASK-008 | WebView/payment safe QA plan | NON_AUTONOMOUS | qa/task-008-webview-payment-safe-qa | completed |
| TASK-009 | Compatibility/device matrix and report format | BOUNDED_AUTONOMOUS | qa/task-009-device-matrix | completed |
| TASK-010 | CI/nightly smoke plan | BOUNDED_AUTONOMOUS for public-safe local planning only | qa/task-010-ci-nightly-smoke | completed |
| TASK-011 | Navigation transition map and coverage model | BOUNDED_AUTONOMOUS for public-safe local planning only | qa/task-011-navigation-transition-map | completed |
| TASK-019 | Android TV auth/session smoke on tv-tpv-013 | NON_AUTONOMOUS runtime task after owner auth data approval | qa/task-019-android-tv-auth-session-smoke | bounded auth/session smoke passed locally on selected TASK-005 lane; integrated to `main` |
| TASK-020 | Post-auth native navigation transitions, states and session persistence coverage | NON_AUTONOMOUS runtime task after TASK-019 selected-lane approval | qa/task-020-xl-post-auth-navigation-transitions | full screen-inventory ledger executed locally on approved lane; integrated to `main` before TASK-024 |
| TASK-021 | Network/offline runtime probe | NON_AUTONOMOUS runtime task after TASK-020 selected-lane context | qa/task-021-network-offline-runtime-check | reversible DNS offline-like probe confirmed; true Wi-Fi-off verdict remains unknown; integrated to `main` before TASK-024 |
| TASK-022 | Xbox-like gamepad full screen inventory | NON_AUTONOMOUS runtime task after TASK-020/TASK-021 selected-lane context | qa/task-022-xbox-gamepad-screen-inventory | Completed with boundaries; final review/verification passed; default push completed by explicit owner command |
| TASK-023 | Full data screen inventory | NON_AUTONOMOUS runtime/data-inventory task after TASK-022 selected-lane context | qa/task-023-full-data-screen-inventory | full public-safe data inventory completed with dynamic game/server list limits; integrated to `main` before TASK-024 |
| TASK-024 | Native post-auth regression pack + selected-lane runtime regression | BOUNDED_AUTONOMOUS after owner authorization in TASK-024 thread | qa/task-024-native-post-auth-regression-pack | completed; Phase A/B passed, Phase C blocked before runtime pending approved collector/input, default integration completed |
| TASK-025A | No-device selected-lane native regression harness and report hardening | BOUNDED_AUTONOMOUS; PROD_SAFE no-device docs/schemas/validators/synthetic tests only | qa/task-025a-no-device-native-regression-harness | completed; physical runtime was deferred in TASK-025A because no device was available in that historical thread |
| TASK-026A | XL+ no-device TASK-025B readiness and regression coverage | BOUNDED_AUTONOMOUS; PROD_SAFE no-device tests/docs/validators only | qa/task-026a-xl-no-device-task025b-readiness-coverage | completed; expands local TASK-025B readiness contract coverage without runtime/device/APK actions; integrated to `main` |
| TASK-026B | No-device implementation of TASK-025B physical runtime tests | BOUNDED_AUTONOMOUS; PROD_SAFE no-device scenario/contracts/synthetic tests only | qa/task-026b-no-device-task025b-runtime-tests | completed; implements future TASK-025B physical runtime scenarios behind gates without runtime/device/APK actions; integrated to `main` |
| TASK-025B | Selected-lane physical native regression runtime | NON_AUTONOMOUS runtime task after refreshed owner approvals | qa/task-025b-selected-lane-physical-native-regression | closed `partial`; selected-lane runtime executed but did not close full transition graph, Search recovery, Settings Gamepad safe entry or `NR-008` game-detail/server-list path |
| TASK-027 | Full app transition graph physical runtime coverage | NON_AUTONOMOUS runtime task after refreshed TASK-027 preflight and reviewer approvals | qa/task-027r-full-graph-closure-final | TASK-027R closed by terminal ledger classification; rail-route branches are explicit `blocked_by_tooling` transition rows after confirmed catalog no-op evidence, not destination coverage; validator overclaim guard hardened |
| TASK-028 | API-layer contract coverage from quarantined audit pack | NON_AUTONOMOUS; offline local quarantine intake only | qa/task-028-api-layer-contract-coverage | implemented and verified on task branch; offline pack intake validator and public-safe coverage ledger added; no live API/backend/runtime execution |
| TASK-029 | REST schema and fixture contract harness | BOUNDED_AUTONOMOUS for offline fixture/schema tests only | qa/task-029-rest-schema-fixture-contracts | proposed after TASK-028 |
| TASK-030 | REST negative, cache and state-sequence contract tests | BOUNDED_AUTONOMOUS for offline mocked transport only | qa/task-030-rest-negative-cache-sequences | proposed after TASK-029 |
| TASK-031 | STOMP signaling and device protocol contract tests | BOUNDED_AUTONOMOUS for offline protocol fixtures only | qa/task-031-stomp-protocol-contracts | proposed after TASK-028 |
| TASK-032 | DataChannel and gamepad protocol contract tests | BOUNDED_AUTONOMOUS for offline protocol fixtures only | qa/task-032-datachannel-gamepad-contracts | proposed after TASK-028 |
| TASK-033 | API-layer redaction and production-safety guard tests | BOUNDED_AUTONOMOUS for synthetic/local security guard tests only | qa/task-033-api-redaction-prod-safety-guards | proposed after TASK-028 |
| TASK-034 | Optional approved staging API execution gate | NON_AUTONOMOUS; PROD_CONDITIONAL only after explicit staging/QA approvals | qa/task-034-staging-api-execution-gate | proposed; blocked until approved backend environment/synthetic user/budget/cleanup/reviews exist |
| TASK-035 | Full static text inventory and coverage audit | BOUNDED_AUTONOMOUS; PROD_SAFE_LOCAL_STATIC_ONLY | qa/task-035-full-static-text-inventory-audit | verified partial-blocked; inventories all 160 available local sanitized sample strings and records exact full-list coverage blocker for the missing 19027 raw values |
| TASK-036 | Exhaustive API-layer test coverage and exploratory evidence intake | BOUNDED_AUTONOMOUS; PROD_SAFE_OFFLINE_STATIC_AND_SYNTHETIC_ONLY | qa/task-036-exhaustive-api-layer-test-coverage | verified partial-blocked; tracked TASK-028 API summary exhaustiveness validated, local quarantine pack absent, live exploration not_run until prerequisites are confirmed |
| TASK-037 | Production bounded API/runtime exploratory coverage with read-only/live safe lane | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_LIVE_READ_ONLY_SAFE_LANE after owner safe-lane passport and reviewer gates | qa/task-037-production-api-runtime-exploratory-coverage | verified partial-blocked; safe-lane preflight and bounded runtime correlation completed, direct live API calls not_run pending public-safe invocation oracle |

## P3 - safe autonomous planning before user-answer-dependent runtime work

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-012 | Safe task prioritization and approval-dependency map | BOUNDED_AUTONOMOUS for public-safe docs only | qa/task-012-safe-task-prioritization | completed |

## P4 - safe autonomous work without new user approvals

| ID | Title | Mode default | Branch | Status |
|---|---|---|---|---|
| TASK-013 | Next-task selection blocker and safe backlog refresh | BOUNDED_AUTONOMOUS for public-safe docs only | qa/task-013-next-task-selection-safe-backlog-refresh | completed |
| TASK-014 | Public repository safety scan checklist and local guard plan | BOUNDED_AUTONOMOUS for public-safe docs/static checks only | qa/task-014-public-repo-safety-scan | completed; verification and multi-agent reviews passed, merged/pushed to detected `main` |
| TASK-015 | Approval metadata schema validator | BOUNDED_AUTONOMOUS for local fail-closed validation only | qa/task-015-approval-metadata-validator | completed |
| TASK-015A/016 | Approval validator hardening and ADB device/build inventory preflight | NON_AUTONOMOUS; validator/docs/tests are PROD_SAFE; local ADB inventory is owner-approved PROD_CONDITIONAL | qa/task-015a-016-approval-validator-adb-inventory-preflight | completed |
| TASK-015B/016A | Final approval validator hardening and ADB inventory rerun/preflight | NON_AUTONOMOUS; validator/docs/tests are PROD_SAFE; local ADB inventory is owner-approved PROD_CONDITIONAL | qa/task-015b-016a-final-validator-adb-preflight | completed; merged to main/origin/main at 0832867 |
| TASK-015C/016B | Approval/device-inventory consistency polish and local ADB inventory readiness | NON_AUTONOMOUS; validator/docs/tests are PROD_SAFE; local ADB inventory is owner-approved PROD_CONDITIONAL only when `adb` and devices are available | qa/task-015c-016b-approval-inventory-consistency | completed; merged/pushed to detected `main` |
| TASK-015D/016C | Approval hardening and gated ADB inventory | NON_AUTONOMOUS; Phase A docs/validator hardening is PROD_SAFE; Phase B inventory-only ADB is PROD_CONDITIONAL after Phase A gate and owner approval | qa/task-015d-016c-approval-hardening-adb-inventory | completed; merged/pushed to detected `main` by user command |
| TASK-015E/017 | Final metadata hardening and public-safe inventory review package | BOUNDED_AUTONOMOUS; Phase A docs/validator/hygiene hardening is PROD_SAFE; Phase B reads existing sanitized inventory or inventory-only ADB refresh after Phase A only | qa/task-015e-017-final-metadata-inventory-review | completed; merged/pushed to detected `main` |
| TASK-015F/017A | Final strict-schema polish and owner target review handoff | NON_AUTONOMOUS; docs/validators/tests/hygiene/public-safe review export only; no runtime or ADB | qa/task-015f-017a-final-strict-schema-owner-target-handoff | completed; default push authorized by explicit user command |
| TASK-015G/017B | Residual approval strictness polish and TASK-005 owner approval input pack | NON_AUTONOMOUS; docs/validators/tests/hygiene/public-safe owner input templates only; no runtime or ADB | qa/task-015g-017b-approval-strictness-owner-input-pack | completed; default push authorized by explicit user command |
| TASK-015H/017C | Final scope-version/normalization polish + TASK-005 owner approval handoff finalization | NON_AUTONOMOUS; docs/validators/tests/hygiene/public-safe owner handoff only; no runtime, no ADB refresh | qa/task-015h-017c-scope-normalization-owner-handoff | completed; default push authorized by explicit user command |
| TASK-016 | Device/build inventory and runtime preflight draft | BOUNDED_AUTONOMOUS for public-safe docs/local validation only; runtime execution blocked | qa/task-016-device-build-runtime-preflight | superseded by completed TASK-015A/016 |
| TASK-017 | Synthetic redaction policy test corpus | BOUNDED_AUTONOMOUS for synthetic local tests only | qa/task-017-redaction-policy-test-corpus | completed; synthetic-only corpus, redaction tests and WebView/payment account-id redaction passed review |
| TASK-018 | Docs consistency and link sanity checks | BOUNDED_AUTONOMOUS for public-safe docs/static checks only | qa/task-018-docs-consistency-link-sanity | completed; merged/pushed to detected `main` |

## Selection rule

Planner selects the next task based on:

1. R0/R1 risk reduction;
2. dependency readiness;
3. ability to verify;
4. smallest useful rollback-sized branch;
5. no production safety blocker.

## Safe autonomous priority policy

Until approved runtime prerequisites are recorded with `evidence_status=confirmed`, autonomous continuation should prioritize public-safe planning, templates, local fail-closed generators, redaction tests, release-gate wiring and documentation tasks that do not require user secrets, private endpoints, APK handling, device execution, real accounts, real payments or production interaction.

Tasks that require user answers, approvals or external fixtures must stay blocked or proposed until those answers are recorded. This includes runtime smoke, real transition observation, WebView/payment execution, network/offline execution, compatibility execution, live CI scheduling and any task needing approved build/device/config/fixture metadata.

After TASK-015H/017C, broad pre-runtime infrastructure hardening should stop
unless a new concrete false-pass is found. On 2026-07-02, a separate
NON_AUTONOMOUS TASK-005 run executed a limited `tv-tpv-013` smoke on the selected
public-safe target alias `tv-tpv-013` / `tv-tpv-a12-013` with the selected
local APK. This confirms only install/update, launch to auth/profile guard,
first focus, minimal D-pad, Back/Home, foreground relaunch,
force-stop/relaunch and crash/ANR observation for that one target/build. Future
work should not treat this as broad compatibility, auth, WebView, WebRTC,
stream/media playback, payment, network/offline or production-flow coverage.

On 2026-07-02, TASK-019 then executed one bounded auth/session smoke on the same
selected lane. It confirms only login to the first post-auth shell, minimal
post-auth focus movement, Home/foreground session persistence,
force-stop/relaunch session persistence and crash/ANR summary. It does not
confirm broad post-auth navigation, stream/WebRTC/media playback, WebView,
payment, network/offline or compatibility coverage.

TASK-020 is the next selected NON_AUTONOMOUS task. It must keep automation
focused on functional post-auth native navigation transitions, states, focus,
Back/Home and session persistence on the same selected lane. TASK-020 must not
enter payment, WebView/redirect, stream/WebRTC/media playback, profile/account
mutation or network/offline manipulation. Phase A fail-closed tooling and docs
are public-safe; any runtime Phase B/C remains `PROD_CONDITIONAL` and must run
only after Phase A gates pass.

The 2026-07-02 TASK-020 run produced partial bounded coverage only: 8 screen
aliases, 4 D-pad focus transitions, `post_auth_shell` state, root
Home/foreground and force-stop/relaunch session persistence passed, and no
crash/ANR signal was observed. Select transitions were not entered because
controls were not semantically safe enough for unattended selection. This is
not exhaustive navigation proof.

## Current selection note

After TASK-012 integration, a next-task selection checkpoint confirmed that no eligible unfinished public-safe task remained in the backlog. TASK-005 was later unblocked for one owner-approved 2026-07-02 limited smoke on `tv-tpv-013`. Remaining runtime-dependent work beyond that narrow smoke remains blocked until its own approved build/APK, Android TV target, runtime configuration, fixture approvals, redaction policy, evidence storage, cleanup/rollback, QA review and Security/Prod-safety review are confirmed.

Planner may continue autonomously with proposed P4 tasks only when the selected task is public-safe, bounded, verifiable locally and does not require user secrets, private endpoints, APK handling, device execution, real accounts, real payments or production interaction. Runtime/device/APK/WebView/WebRTC/payment/network/live CI execution remains blocked until approved prerequisites are recorded with `evidence_status=confirmed`.

TASK-017 completed after TASK-014. It is limited to a public-safe synthetic
redaction corpus, static validators/redactors and local tests. It did not
inspect `.qa_local`, APKs, runtime evidence, real secrets, private endpoints,
real QR targets, real phone/OTP values, device identifiers, account data or
payment data.

TASK-018 completed after TASK-017. It adds tracked-docs Markdown link and
public repo-relative reference sanity checks only. It did not read ignored
`.qa_local` evidence, inspect APKs, run ADB/runtime/WebView/WebRTC/payment/
network checks, crawl external links or claim runtime/product behavior.

TASK-025A completed as a no-device audit task. TASK-025 physical-device runtime
execution was deferred in that historical thread because no physical Android
TV/STB device was available then. TASK-025A is limited to no-device automation
readiness, schema/report hardening and fake/synthetic tests. TASK-025B may
execute selected-lane physical runtime only after a device is confirmed
connected/authorized and owner approvals are refreshed in the TASK-025B thread.

Post-TASK-025A continuation selection from `main@863d00e` found no eligible
unfinished `PROD_SAFE` bounded task ready for autonomous execution. TASK-025B
later ran in a fresh 2026-07-06 thread and closed as `partial`, not pass. The
fresh TASK-027 thread supersedes the remaining transition-graph gap, but
runtime/device/APK/WebView/WebRTC/payment/network/live CI work remains blocked
until TASK-027 prerequisites are recorded with `evidence_status=confirmed`.

Allowed next action is owner input or an explicit new bounded public-safe task;
do not invent additional broad hardening unless a concrete false-pass or
source-of-truth defect is identified.

TASK-027S adds a concrete follow-up candidate after final verification:
implement or specify a reliable runtime detector for
`app_shell_loader_after_launcher_entry` with a 120-second timeout and local-only
diagnostic collection, then design a new safe state/focus/targeting oracle for
session journal, Steam/top-up QR and feedback QR routes. The route retry must
not repeat old coordinate/key/D-pad no-op attempts without that new oracle, and
must preserve the same production-safety boundaries: no payment/session start,
external QR/browser traversal, stream/media playback, Steam/account mutation,
profile mutation, network/offline manipulation or APK modification.

TASK-027T confirms a practical continuation pattern: restore/reconfirm the same
ignored local-only selected lane before runtime, then prove a loaded actionable
catalog state before rail destination assertions. Direct rail D-pad and
UI-tree-derived tap attempts remained no-op, but the TASK-020/TASK-023-style
deep-catalog/grid-focus plus lateral rail recovery oracle visually reached the
blank session journal, Steam/top-up QR and feedback QR destinations. Both QR
targets were decoded local-only at category level and were not followed.

For the audit chain, owner authorization persists in repository source of
truth: each independent audit task must start in a fresh thread, verified
completed audit tasks may be pushed/merged to the detected default branch
(`master` wording means `main` while remote default remains `main`), and the
completed task thread creates exactly one fresh continuation thread for the
next audit task or selection handoff.
