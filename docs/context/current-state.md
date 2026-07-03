# Current state - MTC Fog Play Android QA

## Project

Repository:

```text
https://github.com/Purchii/Test-ANDROID-Fog-Play
```

Goal: build a safe, evidence-first Android TV QA automation and QA process repository for `MTC Fog Play`.

## Known inputs

The project starts from a sanitized QA reverse-analysis pack for a signed Android TV APK. The pack contains manifest/surface/navigation/network/WebView/SDK/risk/smoke/regression/exploratory recommendations without source code, decompiled code, secrets or raw private endpoints.

## Core QA areas

- Android TV runtime startup;
- D-pad/focus navigation;
- auth/session;
- catalog/search;
- WebRTC/stream lifecycle;
- WebView/hybrid/payment-safe flows;
- exported component guard checks;
- network/offline;
- update/install/backup;
- accessibility/localization;
- privacy/logging/security-oriented QA without bypass.

## Current workflow policy

- Strict multi-agent for every bounded task.
- Fresh Codex thread per independent task.
- One goal per task thread.
- Branch per task from current default branch.
- `NON_AUTONOMOUS`: no merge/push default branch without explicit user command.
- `BOUNDED_AUTONOMOUS`: verified task branch must be merged/pushed to the detected default/trunk branch before starting the next independent task.
- Old completed threads become inactive, not deleted.
- Subagents from inactive threads are closed when no longer needed.

## Bootstrap state

- GitHub remote was empty during TASK-000 bootstrap; `main` is initialized as the first default branch.
- TASK-000 implementation branch is `qa/task-000-bootstrap-codex-docs`.
- GitHub remote HEAD/default is confirmed as `main`.
- Public source-of-truth excludes `qa_reverse_analysis/raw/`, compiled cache files and the local reverse-analysis zip by default.
- Public reverse-analysis context is summarized in `docs/context/reverse-analysis/`.
- TASK-001 completed the runtime discovery and smoke bootstrap foundation in fresh thread `TASK-001 - Runtime discovery and smoke bootstrap` on branch `qa/task-001-runtime-discovery-smoke-bootstrap` from `main` commit `5a17c0f`.
- TASK-002 completed the exported component guard checks skeleton in fresh thread `TASK-002 - Exported component guard checks skeleton` on branch `qa/task-002-exported-component-guards` from `main` commit `07cad5a`.
- TASK-003 completed the shared reporting, evidence schema and release gate generator foundation in fresh thread `TASK-003 - Reporting, evidence schema and release gate generator` on branch `qa/task-003-evidence-release-gates` from `main` commit `e260b84`.
- TASK-004 completed the manual runtime screen and TV focus map template foundation in fresh thread `TASK-004 - Manual runtime screen and TV focus map templates` on branch `qa/task-004-runtime-screen-focus-map` from `main` commit `3840a00`.
- TASK-006 completed in fresh thread `TASK-006 - Test data and fixtures contract draft` on branch `qa/task-006-test-fixtures-contract` from `main` commit `474d0de`. Planner selected TASK-006 because TASK-005 runtime smoke remains blocked by missing approved build/device/config/fixture prerequisites. TASK-006 default-branch merge/push was authorized by explicit user command in `NON_AUTONOMOUS` mode.
- TASK-007 completed in fresh thread `TASK-007 - Network/offline policy and safe runner` on branch `qa/task-007-network-offline-policy` from `main` commit `46a7e0f`. TASK-007 is scoped to public-safe network/offline policy and local fail-closed report generation only.
- TASK-009 completed in fresh thread `TASK-009 - Compatibility/device matrix and report format` on branch `qa/task-009-device-matrix` from `main` commit `b50fb53`. Planner selected TASK-009 because TASK-005 runtime smoke remains blocked and TASK-008 is `NON_AUTONOMOUS` WebView/payment planning with fixture-sensitive approval boundaries.
- TASK-008 completed in fresh thread `TASK-008 - WebView/payment safe QA plan` on branch `qa/task-008-webview-payment-safe-qa` from `main` commit `d5887ca`. Planner and Security/Prod-safety selected TASK-008 before TASK-010 so CI/nightly planning can inherit an explicit WebView/payment safety boundary. TASK-008 was implemented in `NON_AUTONOMOUS`; default branch merge/push was authorized by explicit user command on 2026-06-06.
- TASK-010 completed in fresh thread `TASK-010 - CI/nightly smoke plan` on branch `qa/task-010-ci-nightly-smoke` from `main` commit `61c8e05`. Planner selected TASK-010 because TASK-005 runtime smoke remains blocked and CI/nightly planning can now inherit the explicit WebView/payment, network/offline and compatibility safety boundaries.
- TASK-011 completed in fresh thread `TASK-011 - Navigation transition map and coverage model` on branch `qa/task-011-navigation-transition-map` from `main` commit `aa3af9a`. Planner and Security/Prod-safety selected TASK-011 as a user-requested, public-safe navigation transition planning layer because it can extend TASK-004 without runtime/device/APK execution.
- TASK-012 completed in fresh thread `TASK-012 - Safe task prioritization and approval-dependency map` on branch `qa/task-012-safe-task-prioritization` from `main` commit `f90c32d`. Planner and Security/Prod-safety selected TASK-012 because runtime/device-dependent work remains blocked and the next safe autonomous step is to map approval dependencies before selecting user-answer-dependent runtime tasks.
- Post-TASK-012 next-task selection confirmed `main` and `origin/main` aligned at `3cee73e441f0fa945ed4632b47d2880cfae9951f`, with completed task branches merged into the detected default branch. No eligible unfinished public-safe backlog task remained; TASK-005 stayed blocked by missing confirmed runtime prerequisites.
- TASK-013 completed in thread `TASK-013 - Next-task selection blocker and safe backlog refresh` on branch `qa/task-013-next-task-selection-safe-backlog-refresh` from `main` commit `3cee73e`. It records the next-task selection blocker and adds proposed public-safe follow-up tasks that do not require user answers, private data, APK handling, device execution or production interaction.
- TASK-015 completed in thread `TASK-015 - Approval Metadata Schema Validator` on branch `qa/task-015-approval-metadata-validator` from `main` commit `a44dba8`. The user explicitly selected TASK-015 after the approval audit context. TASK-015 was kept isolated on its own branch. TASK-015 adds public-safe approval metadata docs, a local fail-closed validator, unit tests, README/pytest onboarding and safety regressions for release reviewer approvals and TASK-002 evidence gating.
- TASK-015A/016 completed in thread `TASK-015A/016 - Approval validator hardening and ADB device/build inventory preflight` on branch `qa/task-015a-016-approval-validator-adb-inventory-preflight`. The user explicitly authorized default/trunk push with `пушь в мастер`, interpreted as detected default branch `main`. The task hardens TASK-015 approval validation against audit false-pass cases and adds TASK-016 inventory-only ADB preflight. Owner-approved local ADB inventory ran with raw outputs under ignored `.qa_local/devices/`; the final run saw no authorized ADB devices, so device collection is blocked while APK install, app launch and runtime smoke remain `not_run`.

- TASK-015B/016A completed in thread `TASK-015B/016A - Final approval validator hardening and ADB inventory rerun/preflight` on branch `qa/task-015b-016a-final-validator-adb-preflight` from detected default branch `main`. The task closes the remaining post TASK-015A/016 approval false-pass cases, adds device alias and ADB inventory policies, and hardens TASK-016A alias-map reuse. Verification passed locally with 104 targeted validator/inventory tests and 204 full pytest tests through both pytest entrypoints, plus compileall. Owner-approved local ADB inventory ran but collected zero public devices because `adb devices -l` failed; APK install, app launch and runtime smoke remain `not_run`. Follow-up audit confirmed merge commit `0832867` is present on `main` and `origin/main`.
- TASK-015C/016B completed in thread `TASK-015C/016B - Approval/device-inventory consistency polish and local ADB inventory readiness` on branch `qa/task-015c-016b-approval-inventory-consistency` from detected default branch `main` commit `0832867`. The task hardens alias, build alias, runtime profile, evidence and auth-mode consistency, restores public-safe `phone-samsung-*` inventory examples for secondary phone targets, and keeps TASK-016B inventory-only ADB readiness separate from app runtime. The user explicitly authorized pushing to the detected default branch with `пушь в мастерэ`, interpreted as `main`; the task was merged and pushed to `main`.
- TASK-015D/016C completed local implementation in thread `TASK-015D/016C - Approval hardening and gated ADB inventory` on branch `qa/task-015d-016c-approval-hardening-adb-inventory`. Phase A passed the required local gate, then Phase B inventory-only ADB ran through the approved allowlist using local Android SDK platform-tools. Public-safe generated inventory contains 9 devices and no public-safety findings; all generated targets remain `classification_confidence: heuristic` and `manual_review_required: true`. APK install, app launch and runtime smoke remain `not_run`.
- TASK-015E/017 completed in thread `TASK-015E/017 - Final approval metadata hardening + public-safe device inventory review package` on branch `qa/task-015e-017-final-metadata-inventory-review` from `main` commit `07018c2`. Phase A hardened exact local path families, synthetic QA user sub-policy, evidence retention, cleanup semantics and full-tree hygiene scanning. Phase B used existing sanitized `.qa_local/devices/device_inventory.public_safe.generated.json` and exported public-safe owner-review inventory only; generated devices remain heuristic/manual-review-required and not approved for TASK-005.
- TASK-015F/017A completed implementation in fresh thread `TASK-015F/017A - Final strict-schema polish + owner target review handoff` on branch `qa/task-015f-017a-final-strict-schema-owner-target-handoff` from detected default branch `main` commit `e4eae81`. The task is `NON_AUTONOMOUS` and PROD_SAFE-only: strict schema/path/alias/API validation, portable full-tree hygiene scanning, owner-review export hardening and manual owner target handoff. Verification passed after QA A remediation. The user explicitly authorized `push to master`; per project policy this is interpreted as detected default branch `main`.
- TASK-015G/017B completed in thread `TASK-015G/017B - Residual approval strictness polish + TASK-005 owner approval input pack` on branch `qa/task-015g-017b-approval-strictness-owner-input-pack` from `main` commit `d308ef0`. The task is `NON_AUTONOMOUS` and PROD_SAFE-only: residual validator/export strictness, regression tests, hygiene fixes and public-safe owner approval input templates. Verification and multi-agent reviews passed. The user explicitly authorized `push to master`, interpreted as detected default branch `main`; the task branch was prepared for default-branch integration. TASK-005 runtime remains blocked/not_run.
- TASK-015H/017C completed in thread `TASK-015H/017C - Final scope-version/normalization polish + TASK-005 owner approval handoff finalization` on branch `qa/task-015h-017c-scope-normalization-owner-handoff` from `main` commit `c3bd70f`. The task is `NON_AUTONOMOUS` and PROD_SAFE-only: exact TASK-005 scope-version validation, approval-list whitespace/duplicate normalization blocking, exact TASK-005 local APK build aliases, strict owner-review export generated-inventory metadata validation and final owner handoff wording. The user explicitly authorized `push to master`, interpreted as detected default branch `main`. APK install, app launch, ADB inventory refresh and TASK-005 runtime smoke remain `not_run`.
- On 2026-07-01, the owner confirmed the expected TASK-005 APK bundle input
  shape: every test run will receive multiple target-specific APK files under
  `.qa_local/apks/task-005/`, with the device mapping documented in
  `docs/approvals/task005_apk_bundle_contract.md`. APK file arrival, hash
  evidence and runtime approval remain pending; no APK was read, installed,
  launched or committed.
- TASK-005 limited runtime smoke executed in thread
  `TASK-005 - Android TV limited runtime smoke on tv-tpv-013` on branch
  `qa/task-005-android-tv-smoke-runtime` from `main` commit `a7d983d`. The task
  is `NON_AUTONOMOUS` and `PROD_CONDITIONAL` for the owner-approved selected
  target/APK only. The selected local APK was present, local-only SHA-256 was
  recorded without publishing the value, ignored local approval metadata
  validated as `approved_for_limited_runtime`, target identity matched public-safe
  aliases `tv-tpv-013` / `tv-tpv-a12-013`, ordinary install/update succeeded,
  launch reached an auth/profile guard first visible state, initial focus and
  minimal D-pad movement were observed, Back/Home, foreground relaunch and
  force-stop/relaunch stayed within scope, and no crash/ANR signal was observed
  in the captured summary. Raw evidence remains ignored under
  `.qa_local/evidence/task-005/`; APK files, raw hashes, raw screenshots, raw
  logs, raw device identifiers and private values are not committed.
- TASK-019 auth/session smoke executed in thread
  `TASK-019 - Android TV auth/session smoke on tv-tpv-013` on branch
  `qa/task-019-android-tv-auth-session-smoke` from `main` commit
  `92d05a2275e612c89228a35ca329875c6ed83b37`. The task is
  `NON_AUTONOMOUS` and `PROD_CONDITIONAL` for the owner-approved selected
  target/APK/auth lane only. Phase A repository checks and local secret
  preflight passed without printing raw values. Phase B used local-only phone
  and OTP values from `.qa_local/secrets/qa_user.env`, reached the first
  post-auth shell alias `post_auth_home_unknown`, observed minimal post-auth
  focus movement, Home/foreground session persistence, force-stop/relaunch
  session persistence and no crash/ANR signal in the captured summary. Raw
  evidence remains ignored under `.qa_local/evidence/task-019/`; phone/OTP
  values, APK files, raw logs, raw screenshots, raw device identifiers and
  private values are not committed.
- TASK-020 started from `main` commit
  `ac2e11a2643c7cd4b4834e056b70c3a18fc0f7ad` on branch
  `qa/task-020-xl-post-auth-navigation-transitions`. The task is
  `NON_AUTONOMOUS`. Phase A added fail-closed post-auth navigation docs,
  validators and mocked tests. Phase B/C then executed bounded partial runtime
  coverage on the selected TASK-005/TASK-019 lane: 8 screen aliases, 4 D-pad
  focus transitions, root Home/foreground session persistence and root
  force-stop/relaunch session persistence passed; no crash/ANR signal was
  observed. Select transitions were not entered because controls were not
  semantically safe enough for unattended selection.

## Runtime readiness

- Approved APK/build for the TASK-005 `tv-tpv-013` limited smoke:
  `confirmed` for local-only selected APK presence and local-only hash record
  in the 2026-07-02 run. Broader runtime automation builds remain `unknown`.
- APK bundle directory and target-specific filename mapping for future test
  runs: `confirmed` from owner message on 2026-07-01, with APK arrival still
  `pending` for future independent runs.
- Approved Android TV device/emulator/config: `confirmed` for the single
  selected TASK-005 target represented by `tv-tpv-013` /
  `tv-tpv-a12-013`; other targets remain `unknown` or manual-review-only.
- Approved QA accounts, stream fixtures and staging payment fixtures: `unknown`.
- TASK-001 created blocked-report tooling and public-safe discovery templates; TASK-002 created exported component guard skeleton tooling. Runtime/device execution remains blocked until a future task satisfies safety gates.
- TASK-003 created shared evidence schema, release gate template and local fail-closed release gate generator. Release gate generation remains local/public-safe and does not perform runtime/device execution; runtime-dependent gates remain blocked/not_run until approved evidence exists.
- TASK-004 added public-safe manual runtime screen/focus map templates and local fail-closed map report generation. Runtime screen/focus observation remains blocked until a future task records approved build/device/config/fixture/redaction/storage/cleanup prerequisites.
- TASK-006 drafted the public-safe fixture approval contract and checklist for synthetic users, auth/session, stream, WebView, payment staging, network/offline, redaction, evidence storage and cleanup/rollback. This does not approve any real fixture values and does not execute runtime/device checks.
- TASK-007 adds a public-safe network/offline policy and local safe runner. This does not approve any real network profile, does not execute device/network/backend/proxy/packet checks and does not confirm runtime behavior.
- TASK-009 adds a public-safe compatibility/device matrix, report template and local fail-closed report generator. This does not approve any real device class, does not execute Android/device/APK/WebView/WebRTC/payment/network checks and does not confirm compatibility behavior.
- TASK-008 adds a public-safe WebView/payment QA plan, report template and local fail-closed report generator. This does not approve any real WebView fixture, payment staging fixture, account, redirect, endpoint or payment flow; it does not execute Android/device/APK/WebView/browser/payment/network checks and does not confirm runtime behavior.
- TASK-010 adds a public-safe CI/nightly smoke plan, report template and local fail-closed report generator. This does not approve live CI scheduling, CI secrets, private runners, artifact uploads, Android/device/APK/WebView/WebRTC/payment/network checks or production interaction; it does not confirm live CI or runtime behavior.
- TASK-011 adds a public-safe navigation transition map, report template and local fail-closed report generator. This follows official Android TV navigation guidance at category level: efficient, predictable and intuitive navigation, 4-way D-pad traversal, Back/Home semantics, clear paths to focusable controls and axis-based hierarchy. This does not approve Android/device/APK execution, private route/deeplink capture, raw evidence, WebView/WebRTC/payment/network checks or production interaction; it does not confirm transition behavior.
- TASK-012 adds a public-safe prioritization and approval-dependency map. This does not approve any build, target, config, fixture, runtime execution, WebView/WebRTC/payment/network/live CI action or production interaction; it only records category-level gates that must be confirmed before future conditional work can be selected.
- TASK-013 adds no runtime capability. It refreshes backlog/source-of-truth state so future autonomous work can select only public-safe docs/static/fail-closed tasks until runtime prerequisites are confirmed.
- TASK-015 adds no runtime capability. It validates approval metadata only and always reports `runtime_execution_status=not_run`; pending example metadata is `blocked`, while fully confirmed synthetic approval metadata can only become `approved_for_limited_runtime` for a future separate TASK-005 run. Runtime/device/APK/WebView/WebRTC/payment/network/live CI execution remains blocked until explicit confirmed approvals and reviews exist.
- TASK-015A adds no runtime capability. It hardens validator allowlists for approver role, fixtures, evidence capture, runtime scope, cleanup levels, structured targets and synthetic user approval.
- TASK-016 adds inventory-only local ADB capability after owner approval. It attempted collection into ignored `.qa_local/devices/` artifacts; the final run saw no authorized ADB devices and generated an empty public-safe inventory with no forbidden identifier regex findings. It does not approve APK install, app launch, runtime smoke, WebView, WebRTC, payment, account mutation, logcat, screenshots or videos.
- TASK-015B/016A adds no runtime capability. It makes TASK-005 approval stricter: runtime approval requires an actionable manually confirmed P0 Android TV/STB D-pad target, strict APK metadata, complete TASK-005 scope, redacted-summary-only evidence policy, matching target categories and safe aliases. TASK-016A rerun remains inventory-only; the public-safe output had no devices and no public safety findings.
- TASK-015C/016B adds no runtime capability. It blocks runtime alias prefix/index or Android-major mismatch, manual-confirmed TV/STB alias/form-factor mismatch, unsafe build alias tokens, logcat evidence disabled while crash/ANR observation is in scope, missing visual evidence for first-visible/focus/D-pad scope and ambiguous auth mode. TASK-016B local ADB inventory was not run in this environment because `adb` was not available in PATH; app runtime remains `not_run`.
- TASK-015D/016C adds no runtime capability. It hardens approval validation for synthetic QA user paths, IP-like metadata values, strict approved-target device fields, unsafe compound build aliases, duplicate approval lists and TASK-016C output path validation before ADB. Phase B collected inventory only; generated aliases are heuristic/manual-review-required and cannot approve TASK-005 without separate owner/QA review. APK install, app launch, logcat, screenshots, videos, WebView, WebRTC, payment and TASK-005 runtime smoke remain `not_run`/blocked.
- TASK-015E/017 adds no runtime capability. It blocks wrong local path families for APK/secrets/evidence, unsupported synthetic auth scope, incomplete forbidden account actions, raw-public phone/OTP flags, unbounded evidence retention and incomplete cleanup scope. It adds a full-tree hygiene scan and a public-safe owner-review export from existing sanitized inventory. The review export contains 11 devices from local generated inventory, all still `classification_confidence: heuristic`, `manual_review_required: true` and runtime/APK/app statuses `not_run`; TASK-005 remains blocked until separate owner/QA manual review and approvals.
- TASK-015F/017A adds no runtime capability. It closes final validator false-pass cases for strict schema allowlists, exact path families, stable alias Android-version tokens, Android major/API sanity, duplicate approval lists and `runtime_execution.forbidden_scope`. It also hardens public-safe owner-review inventory validation and adds a manual owner review guide listing 6 P0 TV/STB candidates. APK install, app launch, logcat, screenshots, videos, WebView, WebRTC, payment and TASK-005 runtime smoke remain `not_run`/blocked.
- TASK-015G/017B adds no runtime capability. It bounds approval expiration to 30 days, requires exact TASK-005 local paths, exact APK forbidden-action policy, required forbidden target identifier policy, optional no-auth synthetic policy validation, exact owner-review redaction guarantees and public enum validation. It also adds public-safe TASK-005 owner approval input templates. APK install, app launch, logcat, screenshots, videos, WebView, WebRTC, payment and TASK-005 runtime smoke remain `not_run`/blocked.
- TASK-015H/017C adds no runtime capability. It closes final concrete post-audit false-pass cases for exact `scope_version`, whitespace-normalized approval-list duplicates, TASK-005 build alias pattern and malformed owner-review export generated-inventory metadata. After this final pre-runtime polish, broad infrastructure hardening should stop unless a new concrete false-pass is found; the next step is owner/QA approval input and a separate TASK-005 limited runtime smoke preparation/run. APK install, app launch, ADB inventory refresh, logcat, screenshots, videos, WebView, WebRTC, payment and TASK-005 runtime smoke remain `not_run`/blocked.
- TASK-005 now has one limited runtime smoke data point for `tv-tpv-013`. This
  confirms only install/update, launch to auth/profile guard, first focus,
  minimal directional D-pad movement, Back/Home, foreground relaunch,
  force-stop/relaunch and crash/ANR observation on `tv-tpv-013` /
  `tv-tpv-a12-013` with the selected local APK. Synthetic login, phone/OTP
  entry, profile/account mutation, WebView, WebRTC, stream/media playback,
  payment, network/offline, compatibility matrix coverage and broader device
  coverage remain `not_run` / `unknown`.
- TASK-019 now has one bounded auth/session smoke data point for
  `tv-tpv-013`. This confirms only login to the first post-auth shell alias,
  minimal post-auth focus movement, Home/foreground session persistence,
  force-stop/relaunch session persistence and crash/ANR observation for the
  same selected target/build lane. Logout, broad post-auth navigation, WebView,
  WebRTC, stream/media playback, payment, network/offline, compatibility matrix
  coverage and broader device coverage remain `not_run` / `unknown`.
- TASK-020 now has one partial bounded post-auth navigation data point for
  `tv-tpv-013`. This confirms only sampled D-pad focus transitions, root
  Home/foreground session persistence, root force-stop/relaunch session
  persistence and crash/ANR summary on the selected lane. It does not cover all
  screens or all transitions. Safe Select transitions, broad native screen
  inventory, payment/WebView/stream/profile boundaries, network/offline
  behavior, compatibility and full Experience QA remain `not_run` / `unknown`.
- TASK-020 also has a 2026-07-03 full screen-inventory closure ledger for the
  approved Philips-new lane:
  `docs/qa/reports/task020_full_screen_inventory.summary.json`. This confirms
  screen-family coverage for first-run auth/legal/OTP/captcha/onboarding,
  post-auth catalog/search/session/QR/settings/detail/device-gate families and
  external screensaver recovery. It does not claim complete game-title data
  enumeration, real payment/checkout/payment-QR traversal, stream/session
  start, external QR opening, network/offline behavior, profile mutation beyond
  logout or compatibility coverage.
- TASK-021 has a 2026-07-03 network/offline runtime data point for the approved
  Philips-new lane:
  `docs/qa/reports/task021_network_offline_probe.summary.json`. It confirms the
  offline error screen under a reversible DNS offline-like condition and
  focused `DPAD_CENTER` refresh recovery after network restoration for
  unauthenticated, authenticated/onboarding-incomplete and
  authenticated/onboarding-complete states. Refresh shows the
  `Проверка интернет-соединения` loader, then routes respectively to phone
  input, first onboarding about PC rental, or `Игры`. True Wi-Fi-off product
  verdict remains unknown because the Wi-Fi-ADB probe hit an external TV
  screensaver-like interruption; reversible DNS offline-like probing supplied
  the confirmed app evidence.
- TASK-022 has a 2026-07-03 Xbox-like/gamepad full screen-family inventory
  report for the same approved lane:
  `docs/qa/reports/task022_xbox_gamepad_full_screen_inventory.md` and
  `docs/qa/reports/task022_xbox_gamepad_full_screen_inventory.summary.json`.
  The run confirmed bottom-right A/B gamepad hints on auth after the owner
  pressed the connected physical gamepad, confirmed that server selection with
  the physical gamepad active reached a payment/session-activation QR boundary
  instead of the prior TASK-020 connect-device gate, decoded the payment QR
  local-only, and recovered safely without payment, external navigation or
  stream/session start. After the owner clarified that the physical gamepad can
  sleep and hide hints, TASK-022 narrowed practical closure to the gamepad hint
  block plus focused rechecks for post-server-selection behavior and the
  Settings Gamepad section, treating unrechecked base screens as TASK-020
  baseline unless TASK-022 evidence shows otherwise. It also recorded sampled
  long catalog scrolling, session/Steam/feedback/settings recurrences, Search
  and Settings focus blockers for Xbox/gamepad input, a Steam-account connection
  boundary reached by non-A face-button sampling, and the active gamepad
  configuration screen for an Xbox Wireless Controller. Payment completion,
  paid session start, external QR/WebView traversal, complete game-title
  enumeration and mutating controller setup/reset/remap/pairing remain not
  executed.
- TASK-023 has a 2026-07-03 full public-safe data inventory for all approved
  safe reachable screen families/branches on the same lane:
  `docs/qa/reports/task023_full_data_screen_inventory.md` and
  `docs/qa/reports/task023_full_data_screen_inventory.summary.json`. It maps
  TASK-020/TASK-021/TASK-022 baseline screen-family evidence plus fresh
  TASK-023 checkpoints into data categories, redaction classes, boundary
  policies and automation implications. Fresh TASK-023 evidence captured auth,
  onboarding, catalog top/grid, catalog bottom/no-change, Search no-results and
  recovery trap, rail route no-ops, game detail entry and 40 sampled server-list
  segments. The owner clarified that both game catalog content and server rows
  are dynamic by quantity/content; server rows can depend on game and exceed
  250. TASK-023 therefore covers the visible data model, dynamic/static
  classification, focus/scroll behavior, boundaries and anomalies, but does not
  claim or publish complete game-title or complete server-row value
  enumeration. Payment completion, paid session start, external QR/WebView
  traversal, account/purchase actions and controller reset/remap/pairing remain
  blocked or not-run out of scope.
- TASK-021 source-of-truth has been restored in
  `tasks/TASK_021_network_offline_runtime_probe.md`. Its confirmed finding is
  the reversible DNS offline-like app error and refresh recovery behavior; true
  Wi-Fi-off product verdict remains `unknown` because the Wi-Fi-off probe hit an
  external TV screensaver-like interruption with ADB disconnect limitations.
- TASK-024 completed on branch
  `qa/task-024-native-post-auth-regression-pack` and was merged/pushed to
  `main` at `10565a50681c3c9de51f6cd2c61898e8aded4894` after a final
  status-memory remediation commit. It adds the native post-auth regression
  model, suite, fail-closed runner and validator. Phase A/B passed; Phase C
  blocked before runtime because no approved TASK-024 runtime collector/input
  report existed. TASK-024 does not claim exhaustive app navigation,
  payment/WebView, stream/session, broad compatibility or complete dynamic
  game/server value inventory.
- TASK-014 completed on branch
  `qa/task-014-public-repo-safety-scan` from `main` commit `10565a5`. It is
  `BOUNDED_AUTONOMOUS` and `PROD_SAFE` only: public repository safety checklist,
  local tracked-path guard and static tests. It does not read ignored
  `.qa_local` raw evidence, inspect APKs, run ADB, launch the app, execute
  WebView/WebRTC/payment/network flows or confirm runtime behavior. Verification
  and multi-agent reviews passed; the task was merged/pushed to detected
  `main`. A scanner pass confirms only tracked-path repository hygiene at
  command time.

## Evidence status policy

All facts use:

- `confirmed`;
- `likely`;
- `hypothesis`;
- `unknown`.

Do not treat static names or guesses as confirmed runtime behavior.
