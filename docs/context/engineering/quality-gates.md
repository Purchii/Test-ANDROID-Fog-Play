# Quality gates

## Universal task gates

A task is done only when:

- fresh thread verified;
- mode declared;
- task branch used;
- strict multi-agent cycle completed;
- acceptance criteria met;
- relevant checks run or blocked with reason;
- diff reviewed;
- docs updated;
- final Russian report produced;
- next task handoff recorded.

If a task adds or changes tests, the same task must debug those tests before
completion. The relevant targeted test set must pass in that task, or the task
must record an explicit blocked verification note with the exact failing
command, failure reason and scope reason it cannot be fixed immediately. Newly
introduced failing tests must not be deferred to a later independent task.

## Docs-only gates

- Markdown files are readable and linked from source-of-truth docs.
- No secrets/private endpoints/PII/payment data introduced.
- No product facts copied from unrelated reference projects.
- Decisions and risks updated when workflow changes.
- Manual screen/focus map templates use public-safe aliases and never claim runtime behavior without approved evidence.

## Automation gates

- Tests handle missing device/APK/config gracefully.
- No hardcoded secrets/endpoints/package private data unless approved and redacted.
- Reports include app version/device/status/evidence_status/risk_level.
- Log/screenshot artifacts are redacted or stored in ignored local evidence paths.
- No destructive runtime or production commands by default.
- Screen/focus map report generators fail closed: absent prerequisites are `blocked`, template-only plans are `not_run`, and runtime facts remain `unknown`.
- Fixture contracts and approval checklists fail closed: absent, expired, revoked or non-confirmed fixture approvals keep dependent runtime tasks `blocked`.
- Payment-like fixture gates require staging-only, non-real-payment approval before execution.
- Network/offline safe runners fail closed: absent or non-confirmed profile, budget, redaction, evidence storage, cleanup or review prerequisites keep dependent tasks `blocked`.
- Compatibility/device matrix report generators fail closed: absent or non-confirmed build, target class, config, fixture, redaction, evidence storage, cleanup or review prerequisites keep compatibility execution `blocked`, and template-only matrix rows remain `not_run`/`unknown`.
- WebView/payment safe report generators fail closed: absent or non-confirmed WebView fixture policy, staging-only non-real-payment policy, synthetic user policy, resource budget, redaction, evidence storage, cleanup or review prerequisites keep dependent tasks `blocked`, and template-only planned checks remain `not_run`/`unknown`.
- CI/nightly smoke report generators fail closed: absent or non-confirmed static CI scope, schedule policy, repository safety policy, resource budget, redaction, evidence storage, artifact retention, dependency policy or review prerequisites keep CI/nightly execution `blocked`, and template-only planned checks remain `not_run`/`unknown`.
- Navigation transition map report generators fail closed: absent or non-confirmed build, target, config, navigation scope, screen alias policy, input event policy, fixture policy, resource budget, redaction, evidence storage, cleanup or review prerequisites keep transition execution `blocked`, and template-only transition rows remain `not_run`/`unknown`.
- Safe task prioritization and approval-dependency maps are planning-only: they may select public-safe docs/static work, but they must keep runtime/device/APK/WebView/WebRTC/payment/network/live CI tasks `blocked` until every required dependency is `present=true`, `evidence_status=confirmed` and reviewed.
- Next-task selection blocker and safe backlog refresh docs must not approve execution: proposed follow-up tasks may be selected only when they are public-safe, bounded, locally verifiable and require no user secrets, private endpoints, APK handling, device execution, real accounts, real payments or production interaction.
- Approval metadata validators must fail closed: missing/malformed/non-object metadata, missing required fields, non-approved or non-confirmed approvals, expired approvals, missing approver role, unsupported approver role, missing build/target aliases, missing structured targets, unsafe device aliases, phone-only TASK-005 target sets, invalid fixture statuses, non-out-of-scope current stream/WebView/payment fixtures, pending/blocked/invalid evidence policy, non-local ignored storage, unsupported runtime scope, forbidden runtime scope, raw phone/OTP, device identifiers, unknown cleanup levels, C5 cleanup without separate approval, and missing/pending reviews keep runtime approval `blocked`. A valid approval report may return only `approved_for_limited_runtime` with `runtime_execution_status=not_run`; it must not claim runtime pass.
- Final approval metadata validators must also block non-actionable P0 TV/STB targets, `adb_available` other than `yes`, heuristic/manual-review-required runtime targets, reserved alias tokens, `phone` outside the first form-factor segment of structured phone aliases, runtime profile alias prefix/index or Android-major mismatch, manual-confirmed TV/STB alias/form-factor mismatch, unsafe build alias tokens, empty or incomplete TASK-005 runtime scope, ambiguous auth mode, scope/evidence mismatch, raw-evidence public report policies, weak APK SHA-256 policy, incomplete APK allowed actions, forbidden build actions in `allowed_actions`, missing critical forbidden build actions and mismatched allowed/structured target categories.
- Final approval metadata validators must block unsafe synthetic QA user path metadata, IP-like approval values, unknown structured device fields, compound reserved build alias tokens and duplicate public approval list values.
- Final approval metadata validators must use exact local path-family checks:
  TASK-005 APKs under `.qa_local/apks/task-005/*.apk`, synthetic secrets under
  `.qa_local/secrets/*.env` and raw evidence under
  `.qa_local/evidence/task-005/`.
- Final approval metadata validators must block unsupported synthetic auth
  scope, incomplete synthetic login scope, incomplete/typo forbidden account
  actions, raw-public phone/OTP flags, unbounded evidence retention and
  incomplete cleanup rollback scope fields.
- ADB device inventory preflight must be inventory-only: default execution makes no ADB calls and returns blocked/not-run; owner-approved `--allow-adb` may run only `adb devices -l`, safe getprop fields, `wm size`, `wm density` and `pm list features`; raw serial/IP data must stay under `.qa_local/devices/`; public-safe inventory must exclude raw identifiers and always report runtime/app statuses as `not_run`.
- ADB device inventory output paths must be validated before any ADB invocation and must remain under `.qa_local/devices/`.
- ADB device inventory must validate existing alias-map entries before using them in public-safe output. Unsafe persisted aliases block public inventory rather than being trusted. Secondary phone inventory aliases may use `phone-*` only when the structured form factor is `phone`; phone-only inventory never satisfies TASK-005 P0 TV/STB runtime readiness.
- TASK-015D/016C has a hard two-phase gate: Phase B inventory-only ADB is blocked until Phase A approval hardening passes. Generated inventory remains heuristic/manual-review-required and cannot satisfy TASK-005 runtime approval without separate owner/QA manual confirmation.
- TASK-015E/017 owner-review inventory export may be committed only when derived
  from public-safe generated inventory with empty findings, true redaction
  guarantees, not-run runtime/APK/app statuses and heuristic/manual-review
  devices. The export must not contain raw `.qa_local` paths or raw identifiers,
  and it must explicitly say it is not approved for TASK-005 until owner/QA
  manual review.
- TASK-015F/017A strict schema polish must block unknown approved-metadata
  fields, broad or nested local path variants, stable device aliases with
  Android-version tokens, Android major/API mismatches, duplicate auxiliary
  approval lists and invalid `runtime_execution.forbidden_scope`.
- TASK-015F/017A owner-review export validation must block malformed aliases,
  stable aliases with Android-version tokens, runtime alias prefix/index/major
  drift, alias/form-factor mismatch, Android major/API mismatch, duplicate
  aliases, `public_device_count` mismatch, unknown public fields and any device
  that is not heuristic/manual-review-required/not-run.
- TASK-015G/017B residual strictness must block unsupported
  `approved_build_apk.forbidden_actions`, missing/unsupported/duplicate
  `approved_targets.forbidden_identifiers`, approval expiration more than 30
  days after validation time, non-exact TASK-005 APK/secret/evidence local
  paths, malformed optional no-auth synthetic policy fields, incomplete
  owner-review redaction guarantees and malformed owner-review public enum
  values.
- TASK-015G/017B owner approval input pack must remain public-safe template
  material only: no APK hash values, secrets, raw device identifiers, raw
  evidence, private endpoints or runtime approval; TASK-005 remains
  `blocked`/`not_run`.
- TASK-005 APK bundle documentation may record only repo-relative ignored paths
  and public-safe APK filenames/device-class mappings. It must not commit APK
  files, raw hashes, absolute user-profile paths or imply runtime approval.
- TASK-015H/017C final polish must block non-exact TASK-005 `scope_version`,
  approval-list values with leading/trailing whitespace, duplicates after
  trimming, TASK-005 build aliases outside `task-005-local-apk-NNN`, and
  malformed generated-inventory metadata before owner-review export including
  raw source, non-redacted device payloads, invalid timestamps, missing or
  mismatched `public_device_count`, and empty device lists.
- After TASK-015H/017C, broad pre-runtime hardening should stop unless a new
  concrete false-pass is found; the next step is owner/QA approval input and a
  separate TASK-005 limited runtime smoke task.
- Full-tree hygiene must scan tracked text files for trailing whitespace, blank
  line at EOF and missing final newline; a clean `git diff --check` alone is
  not enough for this gate.
- Full-tree hygiene must also support extracted public-safe archive validation:
  default `--mode auto` uses git tracked files in a checkout and falls back to
  `--mode public-safe-tree` outside git while excluding `.git/`, `.qa_local/`,
  caches, build artifacts and binary extensions.
- TASK-014 public repository safety scan must fail closed when tracked paths
  include local-only directories, APK/package artifacts, raw evidence media/logs,
  signing/config/secret filenames or screenshot-like raw evidence names. The
  scanner must report only rule ids, paths and category-level reasons, not file
  contents or matched secret-like values.
- TASK-014 is static/public-safe only. Passing repository path scans does not
  confirm runtime behavior, APK safety, WebView/payment/stream behavior,
  network/offline behavior or compatibility coverage.
- TASK-017 synthetic redaction corpus must use fabricated values only, mark
  every entry as synthetic/public-safe and cover credential-like, token-like,
  URL/endpoint-like, route/deeplink-like, local/APK path-like, hash-like,
  device identifier-like, phone/OTP-like, payment/account-like, QR
  payload-like and raw evidence reference-like classes. Tests and command
  output must report case ids/categories rather than raw specimen values.
- TASK-017 is static/public-safe only. Passing synthetic corpus tests does not
  confirm real evidence redaction, runtime behavior, APK safety, WebView,
  WebRTC, payment, network/offline behavior or compatibility coverage.
- TASK-018 docs consistency/link sanity checks must scan tracked Markdown files
  or explicit test fixtures only, must not crawl external URLs, and must fail
  closed on missing local public targets, missing Markdown anchors, unsafe
  absolute/traversal paths and dereferenceable Markdown links into `.qa_local`,
  raw artifact, package or secret-like target families. Findings must report
  rule ids, source path/line and sanitized target categories, not raw forbidden
  values.
- TASK-018 is static/public-safe only. Passing docs/link checks does not confirm
  runtime behavior, APK safety, real evidence redaction, WebView, WebRTC,
  payment, network/offline behavior or compatibility coverage.
- Release gate reports must require `qa_reviewer_a`, `qa_reviewer_b`, `security_prod_safety_reviewer` and `docs_scribe` to be `approved` or `confirmed` before `release_decision=pass`, even when all R0/R1 gates are otherwise passing.
- Exported component guard reports must block when any required prerequisite has `present != true` or `evidence_status != confirmed`.

## Runtime Android gates

Runtime check can be marked passed only if:

- physical device or approved emulator was available;
- APK/config were available;
- command output was captured;
- screenshots/logs were collected and redacted;
- no crash/ANR evidence appeared;
- report names exact device/app version.

If device/APK/config missing, status is `blocked`, not `pass`.

TASK-005 limited runtime smoke may mark only the executed narrow checks as
`pass`: selected APK install/update, launch/foreground, first visible state,
initial focus, minimal D-pad movement, Back/Home, foreground relaunch,
force-stop/relaunch and crash/ANR observation. Auth/login, phone/OTP entry,
profile/account mutation, WebView, WebRTC, stream/media playback, payment,
network/offline, compatibility matrix and broader device coverage remain
`not_run` / `unknown` unless separately approved and executed.

TASK-019 auth/session smoke may mark only the executed bounded checks as
`pass`: local secret preflight without printing values, selected target/build
preflight, launch to auth/profile guard, bounded synthetic phone/OTP login,
first post-auth shell alias, minimal post-auth focus movement,
Home/foreground session persistence, force-stop/relaunch session persistence
and crash/ANR observation. Logout, broad post-auth navigation, profile/account
mutation, WebView, WebRTC, stream/media playback, payment, network/offline,
compatibility matrix and broader device coverage remain `not_run` / `unknown`
unless separately approved and executed.

TASK-020 post-auth navigation may mark only the executed bounded native
navigation checks as `pass` or `partial`: screen aliases observed, safe native
transition edges, focus path samples, Back/Home behavior, selected session
checkpoints, natural states and boundary detection that was actually observed
on the selected `tv-tpv-013` lane. Default Phase A tooling must make no ADB or
runtime call and return `blocked`/`not_run`. Boundary transitions for payment,
WebView/redirect, stream/WebRTC/media playback, profile/account mutation or
network/offline manipulation must be `blocked_by_boundary`, not `pass`.
TASK-020 must never claim exhaustive navigation proof.

TASK-021 network/offline runtime reports may mark only the recorded reversible
DNS offline-like checks as `pass`/`covered`: offline error screen, focused
Refresh activation by `DPAD_CENTER`, loader evidence and documented recovery
routes. True Wi-Fi-off product verdict remains `unknown` unless a future
approved task captures it without external/ambient interruption. Public reports
must omit raw network/auth/device values, packet captures, proxy details,
private endpoints and raw screenshots/videos/XML.

TASK-024 native regression pack must derive public-safe oracles only from
TASK-020/TASK-021/TASK-022/TASK-023 summaries and explicit runtime evidence.
It must not assert fixed game titles, game counts, server rows, server aliases,
ping values, GPU/CPU strings, prices, QR targets or account-like labels. Public
validators must fail closed on raw paths/values, boundary entries marked as
pass, exhaustive coverage claims, payment/stream coverage claims and missing
case result/reason fields. Default TASK-024 runner execution must return
`overall_status=blocked` and `runtime_execution_status=not_run` without ADB or
runtime calls.

TASK-025A no-device native regression readiness must keep physical runtime
deferred. Default runner execution must return `run_status=blocked`,
`runtime_execution_status=not_run`, `physical_device_status=unavailable`,
`apk_install_status=not_run`, `app_launch_status=not_run` and
`task025b_runtime_status=deferred` without ADB, subprocess-for-ADB, APK
install/read, app launch, UIAutomator traversal, logcat, screenshots,
screenrecord, raw evidence capture or local secret reads. TASK-025A fake or
synthetic contract checks must use
`execution_mode=no_device_synthetic_contract_test`, keep runtime `not_run` and
never count as runtime evidence. TASK-025 report validation must reject weak
pass reports including empty session checkpoints, missing confirmed boundary
evidence for `NR-008`/`NR-009`, duplicate evidence IDs, malformed anomaly
entries, inconsistent Phase C/runtime status, fake pass as runtime pass, unsafe
coverage claims and raw public values/paths/artifact references.

TASK-026A XL+ no-device readiness coverage must remain local/static only. It
may strengthen TASK-025 runner/report/validator contracts and use
synthetic/fake fixtures, but it must not run ADB, inspect `.qa_local`, read or
hash APKs, launch the app, collect logcat/screenshots/XML/video, decode real QR
targets, read secrets or interact with payment/WebView/stream/profile/network
flows. TASK-026A validation must keep no-device reports blocked/not-run with
empty runtime evidence IDs and `task025b_preflight.preflight_status` set to
`deferred_no_device`. Future TASK-025B pass fixtures are schema contracts only:
they must require refreshed owner approvals, confirmed physical-device
preflight, non-empty top-level runtime evidence IDs, physical runtime execution
mode on every passed case, specific boundary-ledger links for `NR-008`/`NR-009`
and the full forbidden boundary category allowlist.

TASK-026B no-device TASK-025B physical runtime test implementation must remain
local/static only. It may define future physical runtime scenarios, validate
scenario/report contracts and run in-memory fake sequencing. It must not run
ADB, inspect `.qa_local`, read/hash/install APKs, launch the app, collect
logcat/screenshots/XML/video, decode real QR targets, read secrets or interact
with payment/WebView/stream/profile/network flows. Default execution must
return blocked/not-run/deferred with
`task025b_preflight.preflight_status=deferred_no_device` and empty runtime
evidence IDs. Synthetic sequencing must use
`execution_mode=no_device_synthetic_contract_test`,
`counts_as_runtime_evidence=false` and empty runtime evidence IDs. Boundary
scenarios may classify guarded categories only; they must not open, follow,
enter, pay, stream, mutate profile/account state or manipulate network state.

TASK-027 full app transition graph coverage must separate preparation/preflight
from physical app runtime. Public-safe preparation may create the graph
contract, validator and report template, and redaction-safe physical preflight
may confirm only device availability, selected aliases, APK presence,
local-only hash recording, synthetic QA env existence, ignored evidence storage
and cleanup policy. APK install, app launch, screenshots, XML, logs, video, QR
decode and app navigation require a later post-preflight QA/Security runtime
approval. Full graph closure requires a directed transition ledger and
screen-family ledger where every currently reachable approved node/branch is
terminally classified as `covered`, `blocked_by_boundary`,
`blocked_by_tooling`, `blocked_by_external_state` or `not_run_out_of_scope`,
with confirmed evidence IDs for covered runtime rows. Every checkpoint must
include screenshot/visual inspection and XML where available; XML-only
classification is insufficient. Known TASK-025B anomalies must be rechecked or
explicitly carried. Boundary rows must keep `entered=false`,
`navigation_followed=false` and `external_action=not_performed`. TASK-027 must
not claim fixed game titles, server rows, server aliases, prices, hardware
rows, ping values or complete dynamic value enumeration. The inherited
`task-005-local-apk-television-full` alias is a TASK-025B family alias only; if
a future runtime step needs a strict `task-005-local-apk-NNN` build alias, it
must record a refreshed public-safe mapping without publishing raw APK names,
paths or hashes.

TASK-028 API-layer contract coverage must remain offline and local-only. The
validator may read the owner-provided API audit pack only from ignored local
quarantine storage and may commit only public-safe aliases, counts,
categories, status values and follow-up task decomposition. It must not
publish raw endpoints, URLs, headers, payloads, fixture bodies, tokens,
phone/OTP/captcha values, payment values, device identifiers, local paths or
executable API recipes. Passing TASK-028 validates matrix/fixture/schema
coverage only; live REST, WebSocket, STOMP, DataChannel, payment/order/session
mutation, backend authorization and Android runtime correlation remain
`not_run` or `unknown` until separate approved tasks.

TASK-029 REST schema/fixture contract harness must remain offline/local only.
It may validate tracked TASK-028/TASK-036 public summaries and read the ignored
local API quarantine pack for REST matrix rows, REST fixture references, REST
fixture JSON readability and REST schema shape. Public reports may contain only
aliases, counts, categories, status values and blockers. Missing local pack
must produce controlled `partial_blocked`/`blocked_missing_local_quarantine_pack`.
The harness must reject raw endpoints, URLs, headers, payloads, fixture bodies,
tokens, cookies, local paths, device/account/payment values and any live or
runtime overclaim. Live REST/backend behavior, real authz/ACL, payment/order/
session mutation, Android runtime correlation and real network/cache behavior
remain `not_run` or `unknown`.

TASK-030 REST negative/cache/state-sequence contract tests must remain
offline/local only. They may validate tracked TASK-028/TASK-029/TASK-036 public
summaries and read the ignored local API quarantine pack for mocked REST
negative rows, cache behavior rows and state-sequence fixtures. Public reports
may contain only aliases, counts, categories, status values and blockers.
Missing local pack must produce controlled `partial_blocked`/
`blocked_missing_local_quarantine_pack`. The harness must reject raw endpoints,
URLs, headers, payloads, fixture bodies, tokens, cookies, local paths,
device/account/payment values, live network/backend claims and runtime
overclaims. Live REST/backend behavior, real authorization/ACL,
payment/order/session mutation, Android runtime correlation and real backend
cache/state behavior remain `not_run` or `unknown`.

TASK-031 STOMP signaling and device protocol contract tests must remain
offline/local only. They may validate tracked TASK-028/TASK-030/TASK-036 public
summaries and read the ignored local API quarantine pack for `stomp_signaling`
and `stomp_device` protocol fixture references and JSON shape only. Public
reports may contain only aliases, counts, categories, status values and
blockers. Missing local pack must produce controlled `partial_blocked`/
`blocked_missing_local_quarantine_pack`. The harness must reject raw endpoints,
URLs, STOMP destinations, headers, payloads, fixture bodies, tokens, cookies,
local paths, device/account/payment values, live WebSocket/STOMP/backend
claims, DataChannel/WebRTC execution claims and Android runtime overclaims.
DataChannel/gamepad protocol rows must remain explicit TASK-032 out-of-scope
rows, not counted as TASK-031 coverage. Live STOMP/WebSocket behavior, backend
subscription routing/delivery, real device pairing behavior, backend
authorization/ACL and Android runtime correlation remain `not_run` or
`unknown`.

TASK-032 DataChannel and gamepad protocol contract tests must remain
offline/local only. They may validate tracked TASK-028/TASK-031/TASK-036 public
summaries and read the ignored local API quarantine pack for `datachannel` and
`gamepad` protocol fixture references and JSON shape only. Public reports may
contain only aliases, counts, categories, status values and blockers. Missing
local pack must produce controlled `partial_blocked`/
`blocked_missing_local_quarantine_pack`. The harness must reject raw endpoints,
URLs, headers, payloads, fixture bodies, tokens, cookies, local paths,
device/account/payment values, live WebRTC/DataChannel/backend claims, live
gamepad/input claims and Android runtime overclaims. Passing TASK-032 validates
offline fixture contracts only; live DataChannel/WebRTC behavior, controller
pairing/input behavior, backend authorization/ACL and Android runtime
correlation remain `not_run` or `unknown`.

TASK-036 API-layer exhaustive coverage guard must remain offline/static and
synthetic-only unless a separate approved execution task is opened. The
validator may consume tracked public-safe TASK-028 summaries and may optionally
cross-check the ignored local quarantine pack through TASK-028 validation when
the pack exists. Public reports may contain only aliases, counts, categories,
status values and blockers. Missing local pack material must produce
`blocked_missing_local_quarantine_pack`, not product evidence. Live REST,
STOMP/WebSocket, DataChannel/WebRTC, backend ACL/authz, Android runtime
correlation, payment/order/session mutation and endpoint publication remain
`not_run` or `unknown` until TASK-034-style `PROD_CONDITIONAL` prerequisites
and reviewer approvals are confirmed.

TASK-037 production bounded API/runtime exploratory coverage may run only inside
the owner-approved read-only safe lane recorded in `active-run.md`. Public
reports must use the TASK-037 validator and contain only aliases, counts,
categories, status values, evidence ids and blockers. They must fail closed on
raw endpoints, URLs, headers, payloads, cookies, tokens, QR targets, device
identifiers, local paths, secrets, real user data, mutation overclaims, boundary
actions performed, unsupported categories, concurrency above `1`, retry count
above `3` or missing preflight fields. Stream start, order, payment, profile or
account mutation, device binding mutation, destructive/revoke/update/delete
actions, APK modification/decompilation and security bypass remain forbidden.

TASK-035 static text inventory must remain local/static only. The builder may
read the ignored sanitized reverse-analysis JSON and write raw string inventory
only under ignored `.qa_local/static_text_inventory/`. Public reports may
contain only source aliases, counts, hash prefixes, category counts,
redaction-class counts, length buckets and status values. Public reports must
fail closed on raw text values, raw URL/domain/path-like values, full SHA-256
hashes, raw local paths, runtime/API/APK status drift or raw-public flags. If
the source-reported likely UI string count is larger than the available raw
sample list, the report must use `partial_blocked` with
`blocked_by_missing_full_static_text_values_source`; it must not infer,
reconstruct, decompile, patch or extract APK/source material to fill the gap.
Runtime visibility, translation quality, accessibility behavior, Android
runtime, live backend/API, payment/order/session and stream behavior remain
`not_run` or `unknown`.

## TASK-020 post-auth navigation gates

Phase A may pass only when:

- default runner returns `overall_status=blocked` and
  `runtime_execution_status=not_run` without ADB/device/APK calls;
- runtime requires explicit `--allow-runtime`;
- raw output paths are constrained to `.qa_local/evidence/task-020/`;
- public summaries are constrained to `docs/qa/reports/*.json`;
- public report validation rejects raw phone/OTP, raw account identifiers, raw
  device identifiers, raw UI dumps, raw screenshots/logs/videos, raw APK
  paths/hashes, private URLs/deeplinks/endpoints/routes/headers/payloads and
  raw `.qa_local` paths;
- mocked tests cover boundary detection, alias safety, session checkpoints and
  budget/frontier semantics.

Phase B/C runtime may start only after Phase A passes and selected-lane
prerequisites for `tv-tpv-013`, `tv-tpv-a12-013`, `task-005-local-apk-001` and
`qa-user-phone-001` remain confirmed and safe. Runtime must stop before
payment, WebView/redirect, stream/media, profile/account mutation or
network/offline surfaces.

## Fixture gates

Future runtime, auth/session, stream, WebView, payment, network and offline tasks may use fixtures only when:

- fixture approval is recorded with `evidence_status=confirmed`;
- owner roles, scope, allowed/disallowed flows, resource budget, redaction, evidence storage and cleanup/rollback are documented;
- credentials, private endpoints, real accounts, real payment data and raw evidence remain outside public source control;
- Security/Prod-safety and QA reviewers approve the fixture boundary;
- real payments, security bypasses and production mutation without cleanup remain forbidden.

## Network/offline gates

Future network/offline tasks may execute only when:

- approved build, Android TV target and runtime configuration are recorded with `evidence_status=confirmed`;
- network profile policy is approved using public-safe category aliases only;
- resource budget covers duration, retry, traffic, account and stream limits;
- Security/Prod-safety and QA reviewers approve the boundary before execution;
- evidence storage and redaction are approved before capture;
- cleanup or rollback restores normal connectivity and any mutable fixture state;
- public reports exclude endpoint values, packet captures, proxy setup, TLS bypass details, raw traffic/log evidence and executable device/network recipes.

TASK-007 local report generation is `PROD_SAFE`; real network/offline execution remains `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## Compatibility/device matrix gates

Future compatibility/device matrix execution may run only when:

- approved build, Android TV target class and runtime configuration are recorded with `evidence_status=confirmed`;
- approved device matrix policy uses public-safe category aliases only, never real serials or private lab identifiers;
- WebView, WebRTC, payment, network/offline and auth/session rows have confirmed fixture approvals before execution;
- Security/Prod-safety and QA reviewers approve the boundary before execution;
- evidence storage and redaction are approved before capture;
- cleanup or rollback is documented for any mutable fixture state;
- public reports exclude raw screenshots, logs, videos, APK paths, endpoint values, account identifiers and executable Android/device/runtime recipes.

TASK-009 local report generation is `PROD_SAFE`; real compatibility execution remains `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## WebView/payment gates

Future WebView/payment execution may run only when:

- approved build, Android TV target and runtime configuration are recorded with `evidence_status=confirmed`;
- approved WebView fixture policy uses public-safe aliases only, never private URLs, redirect chains, headers, payloads, cookies or endpoints;
- approved payment staging policy is staging-only, non-real-payment and excludes card, wallet, bank, billing token and receipt data from public reports;
- synthetic user/session boundaries are approved when account-bound WebView or payment-like paths are in scope;
- resource budget covers duration, retries, redirects, accounts and staging transaction attempts;
- Security/Prod-safety and QA reviewers approve the boundary before execution;
- evidence storage and redaction are approved before capture;
- cleanup or rollback is documented for sessions and staging transaction state;
- public reports exclude raw WebView logs, private redirect data, payment data, raw screenshots, APK paths, endpoint values and executable Android/device/runtime/network recipes.

TASK-008 local report generation is `PROD_SAFE`; real WebView/payment execution remains `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## CI/nightly smoke gates

Future CI/nightly execution may run only when:

- approved static CI scope, schedule policy and repository safety policy are recorded with `evidence_status=confirmed`;
- resource budget covers timeout, retry, concurrency, branch scope and runner limits;
- dependency policy excludes secret-backed private services unless separately approved and redacted;
- evidence storage and artifact retention are approved before any public artifact is published;
- Security/Prod-safety and QA reviewers approve the boundary before live scheduling;
- runtime/device/APK/WebView/WebRTC/payment/network lanes remain disabled unless their own approved prerequisites are confirmed;
- public reports exclude CI secrets, private runner credentials, raw logs, raw screenshots, APK paths, endpoint values, account identifiers, payment values and executable Android/device/runtime recipes.

TASK-010 local report generation is `PROD_SAFE`; live CI scheduling and runtime lanes remain `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## Navigation transition gates

Future navigation transition execution may run only when:

- approved build, Android TV target and runtime configuration are recorded with `evidence_status=confirmed`;
- transition scope uses public-safe screen and action category aliases only, never private routes, deeplinks, package/class names or endpoint values;
- resource budget covers duration, retry, account/session, stream and Back/Home traversal limits;
- Security/Prod-safety and QA reviewers approve the boundary before execution;
- evidence storage and redaction are approved before capture;
- cleanup or rollback is documented for any mutable session, stream, WebView or account state;
- public reports exclude raw screenshots, logs, videos, APK paths, endpoint values, account identifiers, payment values, raw route/deeplink values and executable Android/device/runtime recipes.

TASK-011 local report generation is `PROD_SAFE`; real navigation transition execution remains `PROD_CONDITIONAL` and blocked until these gates are satisfied.

## Safe task prioritization gates

Future autonomous task selection may proceed only when:

- the candidate task is in `docs/tasks/backlog.md` or explicitly requested by the user;
- scope, branch, acceptance criteria and verification are bounded;
- the task is public-safe docs/static/fail-closed work, or all conditional execution dependencies are confirmed;
- approval dependencies are category-level only and exclude private values, raw evidence, APK paths, endpoints, credentials, account identifiers, payment values and executable runtime recipes;
- strict multi-agent Planner, QA and Security review is available;
- no R0/R1 blocker remains.

TASK-012 documentation is `PROD_SAFE`; it does not approve runtime/device/APK/WebView/WebRTC/payment/network/live CI execution.

## Safe backlog refresh gates

Future autonomous selection from refreshed backlog entries may proceed only when:

- the candidate task is explicitly listed as `proposed` in `docs/tasks/backlog.md` or explicitly requested by the user;
- the task specification can be created using public-safe category-level content only;
- the task is docs/static/local-only or fail-closed local tooling;
- no approved build, APK, target, runtime configuration, fixture, secret, private endpoint, account, payment data, raw evidence or live CI access is required;
- strict multi-agent Planner, QA, Security/Prod-safety and Docs/Scribe review is available;
- TASK-005 and runtime-dependent tasks remain blocked unless their approval dependencies are confirmed.

TASK-013 documentation is `PROD_SAFE`; it only records a selection blocker and proposed public-safe backlog. It does not approve runtime/device/APK/WebView/WebRTC/payment/network/live CI execution.

## Approval metadata gates

Future TASK-005 limited runtime smoke may be considered only after:

- approval metadata validates as `approved_for_limited_runtime`;
- approval evidence is `confirmed` and unexpired;
- approved build is represented by a public-safe alias and local ignored `.qa_local/` path pattern;
- approved targets use public-safe aliases only;
- approved runtime targets include at least one manually confirmed P0 Android TV/STB D-pad target with ADB available and manual review no longer required;
- evidence capture policy is explicit and non-pending;
- raw storage policy is local ignored storage;
- cleanup/rollback levels exclude C5 unless separately approved;
- stream, WebView and payment fixtures remain out of scope unless separately approved;
- required QA, Security/Prod-safety and Docs reviews are approved or confirmed.

TASK-015 validation is `PROD_SAFE`; Android runtime execution remains `PROD_CONDITIONAL` and blocked until a separate task executes under confirmed approvals.

## ADB device inventory preflight gates

For TASK-015D/016C, Phase B inventory-only ADB is additionally blocked until
the Phase A approval-hardening gate passes.

TASK-016 local ADB inventory may run only after owner approval and only through
the preflight allowlist. It must not install, launch, start activities, use
monkey, collect logcat, capture screenshots/videos, run WebView/WebRTC/payment
flows, mutate accounts/profiles or modify APKs.

Generated local raw files must remain ignored under `.qa_local/devices/`:

```text
.qa_local/devices/raw_adb_devices.json
.qa_local/devices/serial_alias_map.json
.qa_local/devices/preflight_report.json
```

Generated public-safe inventory remains ignored until manually reviewed:

```text
.qa_local/devices/device_inventory.public_safe.generated.json
```

TASK-016 inventory evidence can confirm only device/build inventory collection,
alias generation and redaction. It cannot confirm APK install, app launch,
runtime smoke, WebView, WebRTC, payment or navigation behavior.

## Merge gates

To merge/push default branch in `BOUNDED_AUTONOMOUS`:

- all relevant checks pass;
- QA Reviewer A approves;
- QA Reviewer B approves;
- Security/Prod-safety Reviewer approves;
- Docs/Scribe confirms docs updated;
- no R0/R1 blocker remains;
- git status clean except intended changes;
- no force-push needed.

Before starting the next independent task in autonomous continuation:

- the completed task branch must be merged into the detected default/trunk branch;
- the detected default/trunk branch must be pushed to origin;
- post-push verification must confirm local HEAD and `origin/<default-branch>` are aligned;
- if this cannot be verified, record a blocker and do not start the next task.
