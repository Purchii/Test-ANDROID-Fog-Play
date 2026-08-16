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
| TASK-029 | REST schema and fixture contract harness | BOUNDED_AUTONOMOUS; PROD_SAFE_OFFLINE_WITH_LOCAL_QUARANTINE_INPUT | qa/task-029-rest-schema-fixture-contracts | implemented; offline REST schema/fixture harness validates 132 REST matrix rows, 71 REST contract rows, 17 REST schemas and local-pack public-safety boundaries; live REST/backend/runtime remains not_run |
| TASK-030 | REST negative, cache and state-sequence contract tests | BOUNDED_AUTONOMOUS for offline mocked transport only | qa/task-030-rest-negative-cache-sequences | completed; offline mocked-transport report validates 73 TASK-030 rows, 51 mocked HTTP rows, 22 mocked sequence rows and 10 cache behavior rows; integrated to `main` |
| TASK-031 | STOMP signaling and device protocol contract tests | BOUNDED_AUTONOMOUS for offline protocol fixtures only | qa/task-031-stomp-protocol-contracts | completed; offline STOMP/device protocol fixture harness verified and integrated to `main` |
| TASK-032 | DataChannel and gamepad protocol contract tests | BOUNDED_AUTONOMOUS for offline protocol fixtures only | qa/task-032-datachannel-gamepad-contracts | completed and integrated to `main` at `3e284b2`; offline DataChannel/gamepad fixture harness validates 26 TASK-032 rows, 25 datachannel rows and 1 gamepad row; live WebRTC/DataChannel/gamepad/runtime remains not_run |
| TASK-033 | API-layer redaction and production-safety guard tests | BOUNDED_AUTONOMOUS for synthetic/local security guard tests only | qa/task-033-api-redaction-prod-safety-guards | completed and integrated to `main` at `5b0bbf5`; task commit `880b5254e9947c22936132e4d535265b9e28246e`; synthetic/static report passes with 10 guard cases and reviews passed |
| TASK-034 | Optional approved staging API execution gate | NON_AUTONOMOUS; PROD_CONDITIONAL only after explicit staging/QA approvals | qa/task-034-staging-api-execution-gate | proposed; blocked until approved backend environment/synthetic user/budget/cleanup/reviews exist |
| TASK-035 | Full static text inventory and coverage audit | BOUNDED_AUTONOMOUS; PROD_SAFE_LOCAL_STATIC_ONLY | qa/task-035-full-static-text-inventory-audit | verified partial-blocked; inventories all 160 available local sanitized sample strings and records exact full-list coverage blocker for the missing 19027 raw values |
| TASK-036 | Exhaustive API-layer test coverage and exploratory evidence intake | BOUNDED_AUTONOMOUS; PROD_SAFE_OFFLINE_STATIC_AND_SYNTHETIC_ONLY | qa/task-036-exhaustive-api-layer-test-coverage | verified partial-blocked; tracked TASK-028 API summary exhaustiveness validated, local quarantine pack absent, live exploration not_run until prerequisites are confirmed |
| TASK-037 | Production bounded API/runtime exploratory coverage with read-only/live safe lane | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_LIVE_READ_ONLY_SAFE_LANE after owner safe-lane passport and reviewer gates | qa/task-037-production-api-runtime-exploratory-coverage | verified partial-blocked; safe-lane preflight and bounded runtime correlation completed, direct live API calls not_run pending public-safe invocation oracle |
| TASK-038 | Evidence schema v2 and authoritative report manifest | BOUNDED_AUTONOMOUS; PROD_SAFE_OFFLINE_STATIC_ONLY | qa/task-038-evidence-schema-v2-report-manifest | completed and integrated to detected `main` at `0770840`; QA-P0-01/F-004/F-005 foundation only, adds v2 envelope schema and public-safe report manifest without release-generator rewrite |
| TASK-039 | Evidence-backed release-readiness generator | BOUNDED_AUTONOMOUS; PROD_SAFE_OFFLINE_STATIC_ONLY | qa/task-039-evidence-backed-release-readiness-generator | completed; merged via `50ef67d`, stabilized and pushed to `origin/main@0a633eb`; product release readiness remains blocked until authoritative external v2 gate evidence exists |
| TASK-040 | Docs checker fail-closed hardening | BOUNDED_AUTONOMOUS; PROD_SAFE_OFFLINE_STATIC_ONLY | qa/task-040-docs-checker-fail-closed-hardening | completed; task commit `c1c8189`, merged and pushed to `origin/main@07efc30`; QA A/QA B/Security/Docs-Scribe final GO; QA-P0-03 exact archive finding ID remains `unknown` because the archive backlog is not tracked/public-readable |

## P2A - EPIC-QA-041-055 independent QA-only execution chain

TASK-041 through TASK-045A are completed and integrated. TASK-048 completed its
repository-only blocked-runtime task after Planner selection from the aligned TASK-045A
closure. TASK-045A closed the
distinct Phone Full visual screen/state/transition graph by honest blockers,
without claiming visual coverage. Its final
Security/Prod-safety gate is `BLOCK_RUNTIME` because synthetic session
provenance and current build compatibility are `unknown_not_verified`;
historical TASK-045 artifacts are quarantined audit-only evidence and do not
count as product visual coverage. TASK-044's bounded
physical runtime is terminal by hardened ledger and blocks release. Further TV
runtime is currently unavailable. TASK-045 ran in one accepted fresh thread;
its paired runtime retained the missing-TV blocker, and the connected phone did
not substitute for the TV member of the lane. Its approved independent phone
inventory has 26 terminal ledger rows: 23 approved-scope
and 21 approved plus declared reachable/discovered. Only 2 rows are covered and
10 session-dependent rows are blocked by external state. The two independently
eligible scenario rows remain blocked by missing oracles. Final QA-A, QA-B,
Security and Docs reviews plus all static gates passed; TASK-045 is completed,
integrated and remote-default aligned at `405300a` while its result remains
`partial_blocked` / `blocks_release`.
TASK-044…055 remain governed by their explicit
dependencies; later runtime work also remains subject
to each task's own `PROD_CONDITIONAL` lane-readiness gates. These entries extend
the backlog without replacing TASK-000…040 history.

| ID | Title | Mode default / safety | Dependencies | Branch | Status |
|---|---|---|---|---|---|
| TASK-041 | QA-only epic integration, sanitized risk bridge and portable official export | BOUNDED_AUTONOMOUS; PROD_SAFE repository-only static QA scope | none | qa/task-041-qa-only-epic-integration-portable-export | completed_integrated; 18 observed_pass; main/origin aligned at a34d075; fresh TASK-042 accepted |
| TASK-042 | Local APK, launcher, AVD and device runtime preflight | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL bounded read-only metadata/inventory | TASK-041 | qa/task-042-local-runtime-preflight | completed_integrated at task commit `76faacc`; final QA A/QA B/Security/Docs GO; 18 terminal rows: 6 observed_pass, 8 blocked, 4 tooling_defect; current SDK/content-integrity access blocker; no product-runtime claim |
| TASK-043 | Sanitized source-informed runtime surface registry and regression selector | BOUNDED_AUTONOMOUS; PROD_SAFE_OFFLINE_STATIC_ONLY | TASK-041, TASK-042 | qa/task-043-source-informed-runtime-coverage-map | completed_integrated; task commit `9e12a13`; integration checkpoint `b4a6d82` pushed and aligned; 18/18 static scenarios observed_pass; manifest v2 authoritative/no release claim; fresh TASK-044 accepted |
| TASK-044 | Television Full reference-lane oracle closure on TPV13 | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_BOUNDED_RUNTIME | TASK-042, TASK-043 | qa/task-044-tpv13-reference-lane-oracle-closure | inactive_completed; task commit `bcf1f37` published on task branch and remote default; hardened 32/32 terminal (29 P0/3 P1): 16 observed_pass, 2 confirmed_defect, 11 observed_fail, 3 blocked_by_oracle; fail/partial_blocked/blocks_release; final Builder/QA-A/QA-B/Security/Docs GO with no open R0/R1; additional TV runtime blocked_by_device; phone-full phone never substituted |
| TASK-045 | Paired Television Full plus Phone Full virtual-gamepad E2E | BOUNDED_AUTONOMOUS; paired runtime blocked, `PROD_CONDITIONAL_PHONE_INDEPENDENT` executed | TASK-044 | qa/task-045-paired-tv-phone-virtual-gamepad-e2e | inactive_completed and integrated at `origin/main@405300a`; accepted fresh thread used exact base `db574915`; 26 terminal phone-ledger rows (23 approved-scope, 21 approved plus declared reachable/discovered), only 2 covered and 10 session-dependent blocked external; 16 anomalies (11 process/5 runtime); QA-045-006/009 blocked_by_oracle, 19 paired rows blocked_by_device, static QA-045-022 ledger closure only; 50 focused and 1194 full/3 skipped; manifest 29/6; final QA-A/QA-B/Security/Docs GO with no open R0/R1; partial_blocked/blocks_release; TASK-046 not started |
| TASK-045A | Phone Full visual screen and transition coverage | BOUNDED_AUTONOMOUS; repository `PROD_SAFE`, runtime `PROD_CONDITIONAL` with `BLOCK_RUNTIME` | completed TASK-045 lifecycle closure | qa/task-045a-phone-full-visual-transition-coverage | inactive_completed_blocked_runtime; exact base `origin/main@de88d1a3`, task commit `96e0888` pushed on task branch and remote default; 17/17 terminal branches with 0 covered, full visual coverage false; 115 focused/1 skipped and 1259 full/4 skipped; manifest 30/7; final QA-A/QA-B/Security/Docs GO, no R0/R1; session/build provenance unknown and TV absent; TASK-046 not started |
| TASK-046 | Television Steam / YandexTV representative runtime lane | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_BOUNDED_RUNTIME | TASK-044 | qa/task-046-yandextv-representative-lane | planned_blocked_by_dependency |
| TASK-047 | Television Sber / SberBox representative runtime lane | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_BOUNDED_RUNTIME | TASK-044 | qa/task-047-sberbox-representative-lane | planned_blocked_by_dependency |
| TASK-048 | AOSP FogPlay Stick and launcher system-cluster runtime lane | BOUNDED_AUTONOMOUS; repository `PROD_SAFE`, system runtime `PROD_CONDITIONAL` with `BLOCK_RUNTIME` | TASK-042, TASK-043 | qa/task-048-aosp-launcher-system-cluster-runtime | inactive_completed_blocked_runtime; implementation commit `f85cf192d66e57d1dedcc7a8084768d2b40179d7` pushed to task branch and main; 19/19 terminal: 17 blocked_by_device, QA-048-014 blocked_by_product_boundary, QA-048-019 static_contract observed_pass only; runtime/product coverage 0; QA-A/QA-B/Security/Docs GO with no open R0/R1; unfiltered suite environment_blocked, supplementary suite 1274 passed/4 skipped |
| TASK-049 | Cross-family non-payment transition and state graph closure | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_MULTI_LANE_RUNTIME | TASK-044, TASK-045, TASK-046, TASK-047 | qa/task-049-cross-family-transition-state-closure | planned_blocked_by_dependency; TASK-048 evidence is optional for non-AOSP subclaims only |
| TASK-050 | Install, update, persistence, process-death and recovery matrix | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_STATEFUL_RUNTIME | TASK-044, TASK-046, TASK-047 | qa/task-050-install-update-persistence-recovery-matrix | planned_blocked_by_dependency |
| TASK-051 | Network, offline, cache, API/STOMP reconnect and fault-runtime coverage | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_NETWORK_RUNTIME | TASK-044, TASK-045, TASK-049 | qa/task-051-network-api-transport-runtime | planned_blocked_by_dependency |
| TASK-052 | Remote, keyboard, physical/virtual gamepad and input lifecycle coverage | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_INPUT_RUNTIME | TASK-044, TASK-045, TASK-049 | qa/task-052-input-gamepad-lifecycle-coverage | planned_blocked_by_dependency |
| TASK-053 | Device equivalence, OS/OEM/display/localization usability matrix | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_COMPATIBILITY_RUNTIME | TASK-046, TASK-047, TASK-049, TASK-052 | qa/task-053-device-equivalence-compatibility-usability | planned_blocked_by_dependency |
| TASK-054 | Crash, ANR, startup, resource, performance and soak qualification | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_BOUNDED_STABILITY_RUNTIME | TASK-044, TASK-045, TASK-049, TASK-051, TASK-052, TASK-053 | qa/task-054-stability-performance-soak | planned_blocked_by_dependency |
| TASK-055 | Unified five-APK plus launcher regression selector and QA release gate | BOUNDED_AUTONOMOUS; PROD_SAFE_EVIDENCE_AGGREGATION_WITH_OPTIONAL_LOCAL_SELECTION | TASK-043, TASK-044, TASK-045, TASK-046, TASK-047, TASK-049, TASK-050, TASK-051, TASK-052, TASK-053, TASK-054 | qa/task-055-unified-multi-apk-release-gate | planned_blocked_by_dependency; AOSP/launcher claim remains blocked without TASK-048 physical evidence |

Default continuation is sequential: TASK-041 → TASK-042 → … → TASK-055. Each
independent task requires a fresh accepted thread, its own branch and strict
multi-agent cycle. Parallel work is forbidden unless the Orchestrator records
separate worktrees, no shared mutable device/session/evidence state, no shared
device control and an explicit merge order.

Current handoff is fail-closed. The fresh post-TASK-048 selection from exact
`origin/main@c75a4bf41470da8dc2649a8f77473141f7aeb7f9` returned
`NO_ELIGIBLE_TASK`. TASK-046 and TASK-047 remain runtime-blocked because
current YandexTV/SberBox physical availability, compatible build binding and
task-authoritative fixture readiness are unknown. Tracked TASK-042 authority
keeps these physical lanes `UNKNOWN` / `blocked_by_device`; stale heuristic
inventory is non-authoritative. TASK-049 depends on both tasks, and TASK-050
through TASK-055 are transitively blocked. TASK-034 remains approval-blocked.
No existing task row status is changed by this selection checkpoint.

## P2B - owner-prioritized Phone Full end-to-end program

Owner resource policy dated 2026-08-15 supersedes the blocked next-task
selection for prioritization only. The single available physical phone is now
the exclusive near-term program lane. This policy does not alter the historical
status of TASK-041 through TASK-055 and does not make any runtime evidence
fresh.

While this overlay is active, the old sequential TASK-041→055 continuation
selector is historical and suspended. Fresh task selection is restricted to
TASK-057→063 in dependency order; no deferred TASK-046→055 runtime task may be
selected until the owner explicitly restores its exact resources and lifts the
overlay.

TASK-046 through TASK-055 remain exactly as recorded above and additionally
carry the overlay `deferred_by_owner_resource_policy_2026-08-15` wherever their
claim requires YandexTV, SberBox, AOSP FogPlay Stick, generic TV, Television
Full, another APK/device family or cross-family/five-APK evidence. They are
deferred, not completed. Phone evidence cannot satisfy or unblock those claims.

| ID | Title | Mode default / safety | Dependencies | Branch | Status |
|---|---|---|---|---|---|
| TASK-056 | Phone-only end-to-end QA roadmap reprioritization | BOUNDED_AUTONOMOUS; PROD_SAFE_DOCS_ONLY; runtime BLOCK_RUNTIME | owner direction; TASK-042/TASK-045/TASK-045A authority | qa/task-056-phone-only-e2e-roadmap-reprioritization | inactive_completed_docs_only; implementation `1cb85c53f5b191c739bbd4128e8097688a1b3c06` pushed to task branch and fast-forwarded to main; no runtime executed |
| TASK-057 | Phone Full runtime authority and fixture readiness gate | BOUNDED_AUTONOMOUS; repository PROD_SAFE; bounded metadata PROD_CONDITIONAL after Security GO | TASK-056; TASK-042/TASK-045/TASK-045A public authority | qa/task-057-phone-full-runtime-authority-gate | inactive_completed_blocked_runtime; exact base `146a390e`; exactly 7 rows: 2 observed_pass/5 blocking; candidate min-SDK metadata not emitted, signing mismatch and three missing fixture/security passports; BLOCK_RUNTIME/blocks_release; no product runtime |
| TASK-057R | Phone Full authorized reinstall and readiness revalidation | BOUNDED_AUTONOMOUS; repository PROD_SAFE; exact target-only uninstall/install PROD_CONDITIONAL after owner authorization and Security plan GO | completed TASK-057; owner authorization dated 2026-08-16 | qa/task-057r-phone-full-authorized-reinstall-readiness-revalidation | inactive_completed_blocked_runtime; implementation `d9d51383e1c0ef132108f35cc31635229f363280` pushed to task branch and fast-forwarded to `main`; bounded reinstall observed_pass; exact 7 rows 4 observed_pass/3 blocked_by_fixture; BLOCK_RUNTIME/blocks_release; no app launch/navigation/TASK-058 |
| TASK-058 | Phone Full first-launch and pre-auth coverage | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_BOUNDED_PACKAGE_ACTION; runtime BLOCK_RUNTIME | latest TASK-057 readiness revalidation GO_RUNTIME and approved non-destructive first-launch fixture | qa/task-058-phone-first-launch-pre-auth-coverage | inactive_completed_blocked_runtime; implementation `d877eaf6386e28b1c9d0c1603d85a3f247f47444`, reviewed closure `233277a233ae206c491593c6696ec375e3b380c1` pushed to task branch and fast-forwarded to `main`; one uninstall/one ordinary install succeeded with zero retry, post-install raw-spill hard stop left readiness 2 pass/5 blocked, exact 3 inherited rows terminal-blocked, product runtime not_run, blocks_release |
| TASK-058A | Phone Full launch-readiness and pre-auth continuation | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_OWNER_OVERRIDE_BOUNDED_PRE_AUTH | completed blocked TASK-058; owner authority and hash-bound Security override dated 2026-08-16 | qa/task-058a-phone-launch-readiness-pre-auth-continuation | inactive_completed_release_blocked; implementation `65b9b9e07515ee77e2aa27f9b5f21b4b5f0840ff` and reviewed closure `3b7e8b12e15989b791363d2be9a216fc38d2633f` pushed to task branch; reviewed closure fast-forwarded to remote `main`; exact base `adc601ed`; collector failed closed once on ambiguous min-SDK with no retry; owner waived selector/delta revalidation; readiness 6 pass/1 `evidence_status=unknown` with owner-override reason; one launch/zero UI actions; inherited three rows covered; discovered auth boundary blocked_by_boundary; cleanup confirmed; blocks_release; TASK-059 blocked; runner/check suites PASS including 161 focused, supplementary 1392/4, manifest 35/12/23, public 421/0, docs 186/0; QA A/QA B GO 0/0/0; Security repository-closure GO/no-new-runtime-authority 0/0/0 |
| TASK-059 | Phone Full synthetic-session and core navigation coverage | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_BOUNDED_RUNTIME | Internal stage 2 of EPIC-PHONE-001; not an independent task/thread/branch | qa/epic-phone-001-full-mobile-application-test-coverage | superseded_by_epic_phone_001_internal_stage_blocked_by_external_state |
| TASK-060 | Phone Full exhaustive screen, state and transition inventory | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_BOUNDED_RUNTIME | Internal stage 3 of EPIC-PHONE-001; not an independent task/thread/branch | qa/epic-phone-001-full-mobile-application-test-coverage | superseded_by_epic_phone_001_internal_stage_blocked_by_external_state |
| TASK-061 | Phone Full input, lifecycle and safe recovery coverage | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_BOUNDED_RUNTIME | Internal stage 4 of EPIC-PHONE-001; not an independent task/thread/branch | qa/epic-phone-001-full-mobile-application-test-coverage | superseded_by_epic_phone_001_internal_stage_blocked_by_external_state |
| TASK-062 | Phone Full boundary classification and safe recovery | BOUNDED_AUTONOMOUS; PROD_CONDITIONAL_BOUNDED_RUNTIME | Internal stage 5 of EPIC-PHONE-001; not an independent task/thread/branch | qa/epic-phone-001-full-mobile-application-test-coverage | superseded_by_epic_phone_001_internal_stage_blocked_by_external_state |
| EPIC-PHONE-001 | Full mobile application test coverage | BOUNDED_AUTONOMOUS; repository work PROD_SAFE, runtime/auth PROD_CONDITIONAL currently blocked | Owner direction 2026-08-16; TASK-058A inherited authority is limited to exact validated rows | qa/epic-phone-001-full-mobile-application-test-coverage | active_repository_only_terminal_blocked_baseline; stages 1-5 blocked by absent synthetic fixture classification and no literal runtime GO; blocks_release |
| TASK-063 | Phone-only evidence aggregation and QA release gate | BOUNDED_AUTONOMOUS; PROD_SAFE_OFFLINE_STATIC_ONLY | TASK-057 through TASK-062; blocked terminal inputs aggregate only to blocks_release | qa/task-063-phone-only-release-gate | planned_blocked_by_dependency |

At the completed TASK-057 checkpoint, TASK-058 remained
`planned_blocked_by_dependency`: TASK-057 did not produce
`GO_RUNTIME`: current phone mapping/authorization and downgrade safety passed,
but candidate min-SDK was not emitted, installed/candidate signing certificates
mismatch, and current synthetic-session, clean-first-launch and
evidence/cleanup passports are absent. A future fresh readiness attempt must
revalidate all seven rows; partial metadata and historical evidence cannot be
carried forward by assumption.

TASK-057R is that fresh independent revalidation after the owner explicitly
authorized loss of the exact target application's local data/session. A
public-safe pre-action Security plan GO and one-shot stop/no-retry contingency
preceded the bounded target-only uninstall and ordinary `main-apk-03` install;
recovery after uninstall/install failure would require new owner authority.
The action succeeded, and row 01 has complete category-level integrity,
provenance, signing, version, emitted min-SDK, target-SDK, ABI and install-
compatibility evidence, so the first four authority rows pass. The remaining
three independent passport rows still block: absence of a post-uninstall
session is not a
synthetic-session passport, successful reinstall is not clean-first-launch
fixture authority, and task-local action/redaction evidence is not the runtime
evidence/cleanup passport, runtime budget, kill switch, rollback or Security
`GO_RUNTIME`. At that historical TASK-057R checkpoint, TASK-058 runtime remained
blocked and was not executed. TASK-058 has since executed only its newly
authorized package-action contour and closed `inactive_completed_blocked_runtime`;
product launch/navigation coverage remains `not_run`.

TASK-058A is the fresh corrective continuation after the completed blocked
TASK-058. Its one authorized collector execution failed closed on ambiguous
min-SDK metadata and was not retried. The owner then confirmed the installed
app as the supplied same build, authorized that installed app and explicitly
waived selector/unrelated-package-delta revalidation while accepting drift
risk. Security issued a hash-bound `GO_RUNTIME_OWNER_OVERRIDE` for this run
only. One launch reached the pre-auth login/authentication boundary; no UI or
forbidden action occurred, and force-stop/Home/capture cleanup succeeded. The
three TASK-058 inherited coverage rows are covered, but readiness row 03 remains
`evidence_status=unknown` with owner-override reason metadata, so the overall
result still blocks release and cannot
satisfy TASK-059 dependency authority.

The authoritative decomposition and common gates are in
`tasks/TASK_056_phone_only_e2e_roadmap_reprioritization.md`; each future task
also has its own task specification. TASK-057 is not runtime-eligible today:
neutral current-phone selector binding to a freshly mapped/authorized
public-safe alias, canonical Phone Full build
integrity and compatibility, synthetic-session passport, non-destructive clean
first-launch fixture, evidence/cleanup authority and Security `GO_RUNTIME` are
not jointly confirmed. The owner must approve those items through public-safe
aliases and ignored local contracts before a fresh TASK-057 thread performs any
device action.

The lossless authority crosswalk is
`docs/qa/phone/phone_only_roadmap_crosswalk.csv`: all 26 TASK-045 phone coverage
rows and all 17 TASK-045A branch rows remain separately owned and append-only.
TASK-063 rejects missing, duplicate or merged required rows. Approved and
reachable phone rows cannot use `not_run_out_of_scope`; they are either freshly
`covered` or release-blocking `blocked_*`.

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

Post-TASK-048 selection in fresh thread
`NEXT_TASK_SELECTION_FROM_main@c75a4bf` on branch
`qa/next-task-selection-main-c75a4bf-blocked` is
`inactive_blocked_no_eligible_backlog_task`. Mode is `BOUNDED_AUTONOMOUS` and
classification is `PROD_SAFE_DOCS_ONLY_SELECTION_CHECKPOINT`. Planner returned
`NO_ELIGIBLE_TASK`. QA Reviewer A returned final `GO` with zero R0/R1/P2 after
remediation of two R1 findings. QA Reviewer B and Security/Prod-safety each
returned final `GO_REPOSITORY_ONLY_SELECTION_CHECKPOINT / BLOCK_RUNTIME` with
zero R0/R1/P2. Docs/Scribe returned final `GO` with zero open R0/R1. Final
static gates passed: Git diff check, epic validation, both hygiene modes,
public repository safety `378/0`, and docs consistency/link sanity `176/0`.
No runtime, APK, ADB, `.qa_local`, account, payment, network or QR action
occurred.

`SELECTION-PROCESS-ANOMALY-001` is `confirmed`: a read-only search referenced
two guessed TASK-043 report CSV paths that do not exist. No evidence was
accepted from those paths; tracked TASK-042 authority and the epic dependency
matrix supplied the correct selection basis. Product/runtime impact is none.
The complete canonical anomaly record is in
`docs/context/handoff/active-run.md`.
The next allowed action is fresh authoritative YandexTV/SberBox lane state,
complete TASK-034 approvals, or an explicit new bounded public-safe task.

Historical selection note follows.

Post-TASK-033 next-task selection from `main@5b0bbf5` found no eligible
unfinished bounded task ready for autonomous execution in `docs/tasks/backlog.md`.
TASK-033 is already merged and pushed to detected default branch `main` at
`5b0bbf5`; the task commit is
`880b5254e9947c22936132e4d535265b9e28246e`. TASK-034 is the only explicit
API-layer follow-up candidate in this backlog, but it remains `proposed` and
blocked until explicit approved backend/staging environment, synthetic user,
budget/rate limits, cleanup/rollback, audit trail, redaction, QA review and
Security/Prod-safety review exist. TASK-035, TASK-036 and TASK-037 are already
verified. The next allowed action is owner input with TASK-034 approvals or an
explicit new bounded public-safe task.

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
