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

TASK-033 API-layer redaction and production-safety guard tests must remain
offline/static and synthetic-only. They may validate tracked TASK-028/TASK-036
public summaries for the 8 known security/redaction rows and may validate only
fabricated synthetic guard specimens. Public reports may contain only aliases,
counts, categories, status values and blockers. The harness must reject raw
endpoints, URLs, headers, payloads, fixture bodies, tokens, cookies, QR
targets, local paths, device/account/payment/session values, protocol payload
bodies, gamepad mapping values, live/runtime/API overclaims, nonzero live
budget counters, unsafe public-safety flags, unknown fields and
pass-with-blockers. Passing TASK-033 validates synthetic/static guard behavior
only; real evidence redaction behavior, live backend/API behavior,
authorization/ACL, Android runtime correlation and payment/order/session
mutation remain `not_run` or `unknown`.

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

## Evidence schema v2 and report manifest gates

TASK-038 report-manifest work is `PROD_SAFE_OFFLINE_STATIC_ONLY`. It may read
tracked public-safe JSON summaries matching `docs/qa/reports/*.json` and
public schemas matching `docs/qa/schemas/*.json` only.

The manifest generator must fail closed when:

- no report records are indexed;
- a report reference is missing or its SHA-256 no longer matches;
- a report uses an unknown or invalid schema;
- more than one v2-valid record is authoritative for the same task/build/target/run;
- a v2 envelope claims pass with non-confirmed evidence or blockers;
- a v2 envelope contains unknown top-level fields, unsafe artifact references,
  URL-like/private/local/raw evidence values, endpoint-like text, secrets or
  ignored `.qa_local` references.

Existing non-v2 public summaries must be explicit
`legacy_migration_blocked` records, not silently ignored and not authoritative.
TASK-038 does not rewrite the release generator and does not approve Android
runtime, APK/device, WebView/payment, stream/session, live API/backend/network
or ignored raw-evidence access.

## Evidence-backed release-readiness gates

TASK-039 release-readiness work is `PROD_SAFE_OFFLINE_STATIC_ONLY`. It may read
the tracked TASK-038 `docs/qa/reports/report-manifest.json`, tracked public-safe
report summaries and tracked public schemas only.

The release-readiness generator must fail closed when:

- the manifest is missing, malformed, stale, hash-mismatched, invalid or has no
  records;
- the manifest path is not the exact tracked public-safe manifest inside the
  repository root;
- an authoritative source envelope fails fresh v2 validation, its internal
  artifact hash drifts, or manifest provenance/mirrored fields disagree with
  the source envelope;
- there are no authoritative v2 evidence records for required R0/R1 gates;
- a candidate record is legacy, non-authoritative, not v2-valid, non-confirmed,
  blocked, partial/not-run/unknown, has `release_effect` other than
  `candidate_evidence`, or lacks required reviewer approval;
- evidence storage or cleanup/rollback prerequisites are absent or not
  confirmed;
- public output would include raw/private-like values, ignored local paths,
  endpoint-like text or absolute local paths.

The current repository release readiness is expected to remain `blocked`
because no external authoritative v2 gate-evidence record exists. The
authoritative TASK-039 report cannot satisfy its own release gates, while the
remaining existing product/task reports are legacy migration blockers.
TASK-039 does not migrate all historical reports and does not approve Android
runtime, APK/device, WebView/payment, stream/session, live API/backend/network
or ignored raw-evidence access.

## Docs checker fail-closed gates

TASK-040 docs-checker work is `PROD_SAFE_OFFLINE_STATIC_ONLY`. It may scan only
validated repository-contained tracked/public Markdown files and must never
crawl external links or read ignored local evidence.

The checker must fail closed when:

- Git tracked-file discovery is unavailable, returns nonzero or emits invalid
  UTF-8 path data;
- discovery yields zero eligible validated Markdown files;
- any scan input is absolute, traversal/ambiguous, scheme/query/fragment-like,
  control-bearing, forbidden-prefix, non-Markdown, missing, nonregular,
  symlinked or outside the selected root;
- root/path metadata or Markdown reads fail.

Path sets are validated as a whole before content I/O. `scanned_files` counts
eligible validated Markdown only. Git stderr, exception text, unsafe input
values and absolute roots must not appear in output; controlled reason codes
and fixed placeholders are required. The checker assumes a trusted
single-writer offline worktree and does not claim an atomic snapshot against
concurrent path replacement; overlapping scans must be discarded and rerun.
Passing TASK-040 does not confirm Android/runtime/product/API behavior.

## TASK-041 official-export and epic-integration gates

TASK-041 uses canonical `PROD_SAFE` with a repository-only static QA qualifier;
Android, ADB, APK, device/AVD, runtime, network and raw-evidence activity is not
part of this gate.

Archive intake must confirm, before tracked integration:

- the archive root and every member are contained, non-absolute and free of
  traversal or normalized-path collisions;
- `MANIFEST.json` file sizes/hashes and `SHA256SUMS.txt` hashes match;
- only `PUBLIC_SAFE_QA_OVERLAY/` enters tracked paths;
- staging/export uses a fresh ignored location and rejects unsafe symlinks;
- existing repository authority wins collisions, with only an additive root
  README link.

The tracked epic authority must fail closed unless it contains exactly 15 task
records, 15 scenario catalogs, 307 unique scenario rows, the canonical
dependency DAG, explicit next-task links and valid repository-relative links to
every task spec and catalog. TASK-041 scenario rows must use exact `PROD_SAFE`
classification and static evidence; later tasks keep their own conditional
runtime classifications and gates.

The official export authority must be a deterministic machine-readable
`official-export-index-v1` containing normalized repository-relative paths,
sizes and SHA-256 values. Validation must reject a missing, unreadable,
malformed or stale index; extra or missing files; unsorted, duplicate or
normalization-colliding paths; absolute/traversal/control/scheme-like paths;
index self-entry; forbidden/private content; nonregular entries and unsafe
symlinks. Archive validation must not depend on `.git`.

Required positive gates:

```text
python automation/quality/official_export_index.py validate-epic --root .
python automation/quality/official_export_index.py check-preservation --root . --base-ref 50dca155e5deb5d97e72780e81792c3e8abadffb
python -m pytest -q tests/test_official_export_index.py
python -m compileall -q automation tests
python -m pytest -q
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

Before completion, create and validate an official ZIP in a fresh ignored
temporary location, unpack it without `.git`, then rerun the relevant epic,
docs, hygiene and public-safety checks from that exported tree. Record the exact
machine-resolved temporary location only in local evidence. The export output
must be a newly created OS temporary directory outside the repository because
the official-export CLI rejects an output path inside the indexed root.

`QA-041-018` cannot be `observed_pass` until the verified task is integrated
and pushed to the detected default branch and exactly one fresh TASK-042 thread
is visibly accepted with the required title/model/reasoning profile. Pending,
failed or duplicate handles do not satisfy the gate. No TASK-041 check proves
product runtime or release readiness.

## TASK-042 local runtime preflight gates

TASK-042 is `PROD_CONDITIONAL`. The static `--validate-only` lane must not read
`.qa_local` or launch subprocesses. The `--preflight` lane may classify only
canonical repo-relative presence. `--execute` is allowed only after the
Security/Prod-safety gate and requires explicit APK-metadata, ADB-inventory and
ignored evidence-root flags.

The execute lane must fail closed unless:

- exactly the five APK contract entries are direct regular, non-reparse,
  non-empty files; missing/extra entries are separate classifications;
- raw hashes and APK metadata stay local-only;
- Android tools resolve only from configured deterministic SDK authority;
- one or two connected ADB identities are allowed only when every identity has
  a unique canonical tracked-reviewed public-safe alias before any per-device
  call;
- stale ignored aliases are non-authoritative;
- AVD results are labelled tooling-only and cannot assert compatibility;
- the launcher contour and actual FogPlay Stick selector remain separate from
  the five APK bundle and cannot use a generic substitute.

A signature parser/tool failure is `tooling_defect`, never PASS. An unmapped
connected identity blocks device inventory without blocking independent static
and tooling lanes. APK install/launch, AVD runtime, UI input, logs, screenshots,
app navigation, payment, account, network mutation and production actions are
outside TASK-042.

Required checks:

```text
python automation/runtime_preflight/task042_local_runtime_preflight.py --validate-only
python automation/runtime_preflight/task042_local_runtime_preflight.py --preflight
python automation/runtime_preflight/task042_local_runtime_preflight.py --validate-report docs/qa/reports/task042_local_runtime_preflight.summary.json
python -m pytest -q tests/test_task042_local_runtime_preflight.py
python -m compileall -q automation tests
python -m pytest -q
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

Completion accepts lane-scoped blockers only when all 18 scenario rows are
terminal, every PASS has the required evidence, the report/ledger/matrix agree,
and no reviewer leaves an R0/R1 finding unresolved. The current public-safe
candidate is 6 `observed_pass`, 8 blocked and 4 `tooling_defect`; configured SDK
access blocks fresh APK content-integrity plus Android tooling evidence and makes
no release or product-runtime claim. TASK-043 may start only in a fresh thread
after verified TASK-042 default-branch integration/push.

The final one-to-two-device, explicit-provenance and report-consistency
remediation passed 55 targeted
tests. A stale-manifest fail-closed full-suite result was recorded immediately;
after regeneration the final sequential suite passed 993 tests with 2 skips.
Final QA A, QA B, Security/Prod-safety and Docs/Scribe re-reviews returned `GO`.
Task commit `76faacc` was fast-forwarded to `main` and pushed with remote SHA
alignment. The same commit has independent 55-targeted and 993/2 full pytest
evidence. The post-integration pytest repeat was attempted and is explicitly
`blocked_by_tooling` because the sandbox denied the ignored pytest bundle;
post-integration report/manifest/hygiene/public-safety/docs/export gates passed.

## TASK-043 sanitized surface registry and selector gates

TASK-043 is `PROD_SAFE_OFFLINE_STATIC_ONLY`. Its fixed CLI modes may read only
tracked public-safe contracts; Android runtime, APK, ADB, device/network access,
ignored `.qa_local` evidence and raw or machine values are outside scope.

The TASK-043 bundle fails closed unless:

- exactly 55 opaque surfaces reconcile in both directions with 33 R0 and 22 R1;
- all 307 epic scenarios have valid surface mappings and every surface has
  downstream scenario traceability;
- all 18 TASK-043 rows are `observed_pass` only from `static_contract` evidence;
- prior TASK-019…040 evidence is projected from the validated manifest without
  upgrading missing, legacy or build-compatibility-unproven records to current
  runtime authority;
- the gap matrix has 13 device/tooling lanes plus a distinct launcher contour,
  and the launcher row maps exactly 24 surfaces, 15 R0 and 9 R1;
- the TASK-044 selection contains 32 `selected_not_run` rows, 29 P0 and 3 P1;
- all outputs validate together in memory before atomic publication and then
  pass cross-file/hash validation from their fixed tracked paths;
- the v2 report makes no product-runtime or release-readiness claim and the
  report manifest remains valid.

Required commands:

```text
python automation/regression/task043_surface_registry_selector.py --validate-only
python automation/regression/task043_surface_registry_selector.py --preflight
python automation/regression/task043_surface_registry_selector.py --execute
python automation/regression/task043_surface_registry_selector.py --validate-report
python automation/reporting/generate_report_manifest.py --output docs/qa/reports/report-manifest.json
python automation/reporting/generate_report_manifest.py --validate-only --manifest docs/qa/reports/report-manifest.json
python -m pytest -q tests/test_task043_surface_registry_selector.py tests/test_report_manifest.py
python -m pytest -q
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

Current pre-integration evidence is 102 targeted passes with 1 skip, 1095 full
passes with 3 skips, docs scan 170/0, public-safety scan 337/0 and a valid
27-record manifest with 4 authoritative v2 and 23 legacy non-authoritative
records. Initial QA/Security R0/R1 blockers were remediated and final QA A and
QA B reviews are `GO`; final Security/Prod-safety and Docs/Scribe reviews of the
completed documentation/diff are also `GO` with no open R0/R1/P2.

TASK-043 quality state is `completed_integrated`. Task commit `9e12a13` was
pushed on the task branch and fast-forwarded into clean `main`;
post-integration TASK-043 CLI, targeted/full pytest, manifest, compile, epic,
docs, hygiene and public-safety gates passed. Integration checkpoint `b4a6d82`
was pushed and local/remote default alignment was confirmed before the final
docs-only lifecycle closure. These static gates do not authorize TASK-044
runtime; its separate conditional preflight and review gates still apply.

## TASK-044 TPV13 physical reference-lane gates

TASK-044 physical runtime is `PROD_CONDITIONAL_BOUNDED_RUNTIME` and is accepted
only for the exact `tv-tpv-013` / `tv-tpv-a12-013` Television Full lane. A
connected phone is inventory-only and cannot satisfy, corroborate or recover a
television result.

The TASK-044 bundle fails closed unless:

- all 32 catalog rows have a terminal canonical status and reconcile by
  scenario id, priority and opaque surface mapping;
- each physical attempt has a visually inspected screenshot, UI tree and
  runner-log reference, with screenshot/tree mismatches retained explicitly;
- checkpoint rows are attempt-scoped and cannot collapse first failure,
  retry, recovery or recurrence into one clean observation;
- loader timeout, Search keyboard trap, Settings→logout accidental route,
  payment-boundary Back no-op and connection-error recurrence remain visible in
  scenario/anomaly evidence with their recovery recorded separately;
- payment/session start, QR/browser traversal, logout/account/profile mutation,
  network shaping, destructive actions, APK modification and security bypass
  remain unexecuted;
- QR targets, screenshots, UI trees, logs, machine/device/build/package/hash and
  account-like values remain local-only; tracked output is category-level;
- final cleanup confirms target-app force-stop, Home restoration and preserved
  session;
- `fail`, any `blocked_*`, any unresolved oracle, retry/recovery or stale/cross-
  lane evidence prevents product/release PASS;
- QA A, QA B, Security/Prod-safety and Docs/Scribe leave no R0/R1 finding open.

Required public-safe runner and repository checks:

```text
python automation/native_regression/task044_tpv13_reference_lane.py --validate-only
python automation/native_regression/task044_tpv13_reference_lane.py --preflight --adapter-input .qa_local/evidence/task-044/runtime-adapter.local.json
python automation/native_regression/task044_tpv13_reference_lane.py --execute --adapter-input .qa_local/evidence/task-044/runtime-adapter.local.json --allow-prod-conditional-ingest
python automation/native_regression/task044_tpv13_reference_lane.py --validate-report
python -m pytest -q tests/test_task044_tpv13_reference_lane.py tests/test_task042_local_runtime_preflight.py
python -m compileall -q automation tests
python -m pytest -q
python automation/reporting/generate_report_manifest.py --output docs/qa/reports/report-manifest.json
python automation/reporting/generate_report_manifest.py --validate-only --manifest docs/qa/reports/report-manifest.json
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
git diff --check
git status --short --branch
```

The hardened bundle is terminal and release-blocking: 32 rows (29 P0/3 P1), 16
`observed_pass`, 2 `confirmed_defect`, 11 `observed_fail` and 3
`blocked_by_oracle`; execution is `fail`, coverage is `partial_blocked`, and
the release gate is `blocks_release`. Independent QA R1 findings on
report/checkpoint/anomaly/blocker semantics were remediated before regeneration.
The physical TV is no longer available, so any repeat/additional reference-lane
runtime is `blocked_by_device`. The remaining phone-full phone is inventory-only
and cannot be used by TASK-044. Phone runtime requires a fresh task after
TASK-044 closure and integration.

Final Builder, QA Reviewer A, QA Reviewer B, Security/Prod-safety and
Docs/Scribe reviews returned `GO` with no open R0/R1. This permits integration
of the `blocks_release` evidence bundle only; it is not a release approval and
does not authorize phone or TASK-045 runtime in this thread.

## TASK-045 paired TV plus phone virtual-gamepad gates

TASK-045 paired physical runtime is `PROD_CONDITIONAL_PAIRED_RUNTIME`. A
task-local owner-selected mapped phone may execute only independently
authorized disconnected phone inventory when the TV is absent; it cannot
substitute for the Television Full member, primary/fallback phone lane, paired
timeline or canonical-build compatibility evidence.

The TASK-045 bundle must fail closed unless:

- all 22 catalog scenarios reconcile by id, priority, surface and terminal
  status, with all paired/connected/cross-device rows blocked when the TV is
  unavailable;
- every currently reachable approved phone screen/state/navigation branch is
  terminally classified as `covered`, `blocked_by_boundary`,
  `blocked_by_tooling`, `blocked_by_external_state` or
  `not_run_out_of_scope`, with evidence ids for every observed row;
- every runtime checkpoint has a visually inspected screenshot, UI tree and
  runner-log modality; a sanitized helper-gap marker may document the immediate
  force-stop state but must classify that branch as tooling-blocked rather than
  PASS;
- screenshot/UI-tree mismatches, first failures, retries, recoveries and
  recurrences remain separate; recovery never rewrites the first failure;
- a category scan that finds no connected-success label is not enough to pass
  the no-TV row, and a history/gamepad-shaped tab is not a virtual-gamepad
  oracle; QA-045-006 and QA-045-009 remain blocked without their explicit safe
  product state;
- ordinary install/update downgrade rejection remains an external-state
  blocker; uninstall, data clear, downgrade override, APK modification or
  bypass is not used, and an owner-confirmed installed-newer build keeps
  canonical compatibility `unknown_not_verified`;
- payment/session start, account/profile mutation, external QR/browser
  traversal, network mutation outside an approved budget and unsafe lock/unlock
  actions remain unexecuted;
- dynamic titles, prices, quantities, machine/device/build/package/hash/account
  values, raw QR targets, screenshots, UI trees and logs remain local-only;
- cleanup confirms target-app force-stop, Home restoration, preserved existing
  session, no external browser, no payment/session start, no account/network
  mutation and no paired state;
- any `blocked_*`, tooling gap, missing oracle, missing TV, unknown build
  compatibility or paired claim not established keeps coverage
  `partial_blocked` and release effect `blocks_release`;
- QA Reviewer A, QA Reviewer B, Security/Prod-safety and Docs/Scribe leave no
  R0/R1 finding open before integration.

Required public-safe runner and repository checks:

```text
python automation/gamepad/task045_paired_virtual_gamepad.py --validate-only
python automation/gamepad/task045_paired_virtual_gamepad.py --preflight --adapter-input .qa_local/evidence/task-045/runtime-adapter.local.json
python automation/gamepad/task045_paired_virtual_gamepad.py --execute --adapter-input .qa_local/evidence/task-045/runtime-adapter.local.json --allow-prod-conditional-ingest
python automation/gamepad/task045_paired_virtual_gamepad.py --publish-runtime-coverage --allow-prod-conditional-ingest
python automation/gamepad/task045_paired_virtual_gamepad.py --publish-blocked-baseline
python automation/gamepad/task045_paired_virtual_gamepad.py --validate-report
python -m pytest -q tests/test_task045_paired_virtual_gamepad.py
python -m compileall -q automation tests
python -m pytest -q
python automation/reporting/generate_report_manifest.py --output docs/qa/reports/report-manifest.json
python automation/reporting/generate_report_manifest.py --validate-only --manifest docs/qa/reports/report-manifest.json
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
git diff --check
git status --short --branch
```

The final bundle has 26 terminal phone-ledger rows: 23 approved-scope and 21
approved plus declared reachable/discovered. Only 2 rows are `covered`; 10
session-dependent rows are `blocked_by_external_state` because synthetic
session provenance was not verified. QA-045-006 and QA-045-009 are
`blocked_by_oracle`; paired runtime is `blocked_by_device`. The bundle retains
16 anomalies: 11 process/tooling and 5 runtime.

Final acceptance gates passed with 50 focused tests and 1194 full-suite tests
with 3 skipped. Runner/report, compile, manifest, epic, docs, both hygiene
modes, public-safety and diff checks passed; the v2 manifest validates 29
records, including 6 authoritative records. QA Reviewer A, QA Reviewer B and
Security/Prod-safety returned final `GO` with no open R0/R1; Docs/Scribe source
reconciliation is complete. Overall remains `partial_blocked` /
`blocks_release`. The verified bundle was committed, published on the task
branch, fast-forwarded to remote default and aligned at
`origin/main@405300a0ce15da75d62ffa822c68d219cf6ea31d`; TASK-045 is
`inactive_completed`. TASK-046 has not started.

## TASK-045A Phone Full visual transition gates

TASK-045A repository work is `PROD_SAFE`; physical phone work is
`PROD_CONDITIONAL` and remains `BLOCK_RUNTIME` while
`active_session_provenance=unknown_not_verified`. The historical installed-newer
lane is not canonical-build proof, and Television Full evidence cannot satisfy
the distinct Phone Full graph.

The TASK-045A bundle must fail closed unless:

- the exact base is the completed TASK-045 lifecycle closure
  `origin/main@de88d1a3fda251be16bd89a35fd68ef1ae29339f` and work remains on
  `qa/task-045a-phone-full-visual-transition-coverage`;
- all 20 prior PNG, 19 XML and 19 log artifacts remain quarantined
  `audit_only`, cannot count as product coverage, and `cp001` remains
  incomplete rather than inferred complete;
- session-dependent nodes and edges remain `blocked_by_external_state` until a
  task-authoritative synthetic-session passport validates;
- Phone Full aliases, states, layouts and transitions remain separate from all
  Television Full/paired evidence;
- every approved reachable branch is terminally one of `covered`,
  `blocked_by_boundary`, `blocked_by_tooling`, `blocked_by_external_state` or
  `not_run_out_of_scope`, with approved reachable branches forbidden from the
  out-of-scope class;
- each covered checkpoint has its own fresh run-window visually inspected
  screenshot, UI tree and bounded target-app log/marker;
- initial/later long-list segments, expanded/collapsed menus, overlays,
  recurrences, first failures/recoveries, screenshot/XML mismatches and
  anomalies remain explicit graph/ledger records;
- payment or paid/active session start, account/profile/logout mutation,
  QR/browser/external traversal, network shaping, unsafe lock/unlock, unknown
  targets, APK modification/decompile/bypass, uninstall, clear-data and
  downgrade override remain unexecuted;
- runtime budgets remain zero under `BLOCK_RUNTIME`; any later GO-bounded run
  has explicit attempt budgets and the kill switch target-app force-stop,
  Home, preserved session and no external app/payment/session/account/network/
  paired state;
- raw serial/IP/path/hash/account/package/QR/screenshot/XML/log values remain
  ignored/local-only and tracked output is category-only;
- the 33-pass/17-fail clean-worktree baseline anomaly, host script-policy build
  comparison block and abandoned excessive/truncated package-binding precheck
  remain process/tooling evidence only, never product evidence;
- QA Reviewer A, QA Reviewer B, Security/Prod-safety and Docs/Scribe leave no
  R0/R1 finding open before integration.

Exact planned repository checks:

```text
git status --short --branch
git diff --check
python automation/gamepad/task045a_phone_visual_transition_coverage.py --validate-only
python automation/gamepad/task045a_phone_visual_transition_coverage.py --publish-blocked-baseline
python automation/gamepad/task045a_phone_visual_transition_coverage.py --validate-report
python -m pytest -q tests/test_task045a_phone_visual_transition_coverage.py
python -m compileall -q automation tests
python -m pytest -q
python automation/reporting/generate_report_manifest.py --output docs/qa/reports/report-manifest.json
python automation/reporting/generate_report_manifest.py --validate-only --manifest docs/qa/reports/report-manifest.json
python automation/quality/official_export_index.py validate-epic --root .
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```

The following conditional ingest commands are planned but remain `not_run` and
blocked until Security returns GO and the approved lane, build, synthetic
session passport, evidence root and bounded budgets validate:

```text
python automation/gamepad/task045a_phone_visual_transition_coverage.py --preflight --adapter-input .qa_local/evidence/task-045a/runtime-adapter.local.json
python automation/gamepad/task045a_phone_visual_transition_coverage.py --execute --adapter-input .qa_local/evidence/task-045a/runtime-adapter.local.json --session-passport .qa_local/evidence/task-045a/synthetic-session-passport.local.json --allow-prod-conditional-ingest
```

Passing repository/static gates does not prove Phone Full product visual or
transition coverage. At the current checkpoint fresh product coverage is zero,
runtime is blocked/not-run and TASK-046 is not authorized to start.

Final lifecycle result: all repository gates above pass. The
focused TASK-045A plus TASK-045 set is 115 passed/1 skipped; full pytest is 1259
passed/4 skipped. The regenerated manifest validates with 30 records and 7
authoritative records. QA Reviewer A, QA Reviewer B, Security/Prod-safety and
Docs/Scribe returned GO with no open R0/R1 after remediation of identifier,
canonical-path, cleanup, graph/evidence, attempt/recovery, branch-specific,
freshness, CSV-enum and report-parity false-pass routes. Runtime remains
`BLOCK_RUNTIME` and product coverage remains zero. Task commit `96e0888` is
pushed on the task branch and fast-forwarded to remote default; this subsequent
documentation commit closes the inactive lifecycle.

## TASK-057 Phone Full runtime-authority readiness gates

TASK-057 repository work is `PROD_SAFE`. Security may authorize only a bounded
`PROD_CONDITIONAL` read-only metadata contour under
`GO_METADATA_CONDITIONAL / BLOCK_RUNTIME`; this is not `GO_RUNTIME`.

The readiness closure fails closed unless:

- exactly seven unique rows are present and no row infers, duplicates or merges
  another;
- current-phone mapping/authorization and the opening, confirmation and cleanup
  device snapshots are fresh and stable;
- candidate and installed build presence, provenance, integrity, signature,
  version, min/target-SDK and ABI compatibility are independently confirmed;
- historical aliases/build evidence never substitutes for fresh authority;
- ordinary downgrade rejection remains preserved without bypass;
- synthetic-session, non-destructive clean-first-launch and evidence/cleanup
  passports independently validate;
- all seven rows are `observed_pass` and Security returns `GO_RUNTIME`;
- raw identifiers/paths/hashes/signing/account/session values remain
  ignored/local-only; and
- no install, app/UI/navigation, auth, account, payment, session, network or
  external-boundary action occurs.

The 2026-08-15 closure has two `observed_pass` and five blocking rows. Current
phone mapping/authorization and downgrade safety pass. Candidate min-SDK was
not emitted; installed/candidate signing certificates mismatch; synthetic
session, clean-first-launch and evidence/cleanup passports are absent. Other
confirmed candidate metadata, true device/candidate ABI intersection, stable
snapshots and no-mutation cleanup cannot infer the missing rows. Security stays
`BLOCK_RUNTIME`, release effect is `blocks_release`, and TASK-058 remains
blocked.

## TASK-057R authorized reinstall readiness gates

TASK-057R repository validation is `PROD_SAFE`. The exact mapped target-only
uninstall and ordinary selected-candidate install are `PROD_CONDITIONAL` only
under the owner authorization dated 2026-08-16 and the task-local Security plan
gate. The authorization accepts target-app local data/session loss but does not
authorize clear-data, reset, another package, downgrade bypass, APK mutation,
launch/navigation or TASK-058.

The TASK-057R bundle fails closed unless:

- historical TASK-057 spec, runner, tests and report bundle remain unchanged;
- a separate TASK-057R task/report identity and fixed tracked paths are used;
- the action ledger records exact fresh selector/artifact mapping, a distinct
  public-safe pre-action Security plan GO row and a pre-action one-shot
  stop/no-retry contingency before uninstall, one
  authorized uninstall, target absence, one ordinary `main-apk-03` install,
  exact launch-free installed/candidate metadata/signing/hash equivalence, zero
  unrelated-package delta and zero launch/navigation/TASK-058 actions;
- all exact seven TASK-057 authority subjects are present once and in order;
- row 01 has separate category-level evidence for integrity, provenance,
  signing, version, emitted min-SDK, target-SDK, ABI and install compatibility;
  omission of any category blocks the row;
- only rows 01–04 are `observed_pass`; successful reinstall, empty session and
  local action/redaction evidence cannot promote rows 05–07;
- synthetic-session, clean-first-launch and runtime evidence/cleanup passport
  rows remain independent and release-blocking while absent;
- Security remains `BLOCK_RUNTIME`, aggregate readiness is 4 pass/3 blocked,
  and release effect is `blocks_release`;
- target-app local data/session is recorded as owner-authorized lost and not
  restored, with no rollback claim;
- reinstall drift/failure stops without retry; recovery after uninstall/install
  failure requires new owner authority; this contingency is distinct from the
  absent later-runtime kill switch/passport;
- all three pre-mutation process anomalies remain fail-closed, retain the first
  failure, accept no failed output as evidence and state product impact none;
- raw paths, device identifiers, package names, hashes, signing values and
  command output remain ignored/local-only.

The repository-only runner must not read `.qa_local`, invoke Android tooling or
ADB, perform package actions, accept arbitrary path overrides, launch/navigate
the app or execute TASK-058. Passing its report contract proves only the
integrity of the sanitized tracked TASK-057R record, not `GO_RUNTIME`.

Required focused checks:

```text
python automation/runtime_authority/task057r_phone_full_authorized_reinstall_readiness.py --validate-only
python automation/runtime_authority/task057r_phone_full_authorized_reinstall_readiness.py --validate-report
python -m pytest -q tests/test_task057r_phone_full_authorized_reinstall_readiness.py tests/test_task057_phone_full_runtime_authority.py tests/test_report_manifest.py
python automation/reporting/generate_report_manifest.py --validate-only --manifest docs/qa/reports/report-manifest.json
python -m compileall -q automation/runtime_authority tests/test_task057r_phone_full_authorized_reinstall_readiness.py
git diff --check
git status --short --branch
```

## TASK-058 selected-artifact package action and pre-auth gates

The owner's exact ignored/local-only selection is represented only as
`task058-selected-phone-full-001` and supersedes `main-apk-03` for TASK-058's
package action. Repository work is `PROD_SAFE`; package action and runtime are
separate `PROD_CONDITIONAL` phases.

Before mutation require fresh remote/base alignment; exactly one authorized
selector, target and regular non-reparse same-repository APK; exact package/
family mapping; complete integrity, provenance, signing, version,
min/target-SDK, ABI and compatibility oracles; ignored evidence sink; bounded
budget; one-shot stop/no-retry contingency; failure recovery; cleanup; and
Security GO for the exact plan. The budget is one target uninstall, one
ordinary install, zero retries and zero alternate artifacts. Stop on drift,
ambiguity, incomplete oracle, NO_GO, raw spill, unexpected state, failure or
scope expansion.

Launch remains forbidden until the exact seven TASK-057 rows are freshly and
independently `observed_pass` and Security issues `GO_RUNTIME`. Install success,
empty state or accepted target-local data/session loss cannot infer synthetic-
session, clean-first-launch or runtime evidence/cleanup passports, budget, kill
switch or rollback. If only package action is approved, close safely with
runtime `not_run`.

After `GO_RUNTIME`, continue until every approved reachable TASK-058 row has
fresh screenshot visual inspection, UI tree and bounded target-app marker/log
and is terminally classified, or a genuine hard blocker occurs. Credential
entry/authentication, account/payment mutation, paid/media start, network
shaping, external QR/browser traversal, destructive UI and TASK-059+ remain
forbidden.

`TASK058-PROCESS-ANOMALY-001` through `TASK058-PROCESS-ANOMALY-011` remain
confirmed process evidence only. The first three occurred before package
mutation. The fourth stopped the run after one successful uninstall, one
successful ordinary install and package-presence confirmation because native
stderr exposed a raw device-side path; equivalence, unrelated-package delta and
final selector snapshots therefore remain blocked. The fifth and sixth record
corrected repository validator/CLI assumptions. The seventh records an
independent reviewer mistakenly rewriting only the deterministic public-safe
bundle during read-only review; Orchestrator regeneration supersedes it. The
eighth records a guessed nonexistent docs-checker path that failed before
execution and was replaced by the passing canonical checker. The ninth records
a malformed quoted QA search expression rejected before the read-only search
ran. The tenth records a coordination wait after an explicit reviewer stop;
it performed no repository or product action. The eleventh records a rejected
v2 top-level owner-action field, blocked manifest and three focused failures;
owner actions moved to allowed unknown records before the passing rerun. None
supplies product evidence or relaxes any gate, and all have product impact
`none`.

The exact non-inferential readiness authority remains, in order,
`task057-authority-01-canonical-phone-full`,
`task057-authority-02-installed-compatibility`,
`task057-authority-03-current-phone-selector`,
`task057-authority-04-downgrade-safety`,
`task057-authority-05-synthetic-session`,
`task057-authority-06-clean-first-launch` and
`task057-authority-07-evidence-cleanup-security`. The terminal result is two
`observed_pass` and five blocking rows with Security `BLOCK_RUNTIME`.

The inherited crosswalk is losslessly terminal: `phone-coverage-001` and
`phone-coverage-017` are screen/state rows, while `A002` is a transition with
distinct public-safe unobserved from/to checkpoint aliases. All three are
`blocked_by_external_state`; fresh runtime screenshots, UI trees, bounded logs,
covered checkpoints and product transitions remain zero.

## TASK-058A owner-override launch-readiness and pre-auth continuation gates

TASK-058A repository work is `PROD_SAFE`. Its one-shot launch-free collector
and bounded pre-auth run are `PROD_CONDITIONAL`. Historical TASK-058 artifacts
are immutable inputs and must not be rewritten.

The launch-free collector gate requires native stdout and stderr to be captured
inside one ignored task/run-bound sink before parsing or public projection. It
allows one execution and zero retry, mutation or launch. The actual execution
failed closed with `artifact_metadata_ambiguous:min_sdk`; ambiguous metadata is
not evidence and the collector must not be retried under current authority.

The owner subsequently confirmed the installed app as the supplied same build,
authorized testing the installed app, waived selector and unrelated-package-
delta revalidation verbatim and accepted drift risk. Security may bind that
exact statement to `GO_RUNTIME_OWNER_OVERRIDE` only for this run. The override
gate must enforce all of the following:

- it is hash-bound to the reviewed authority/evidence state;
- it is not labeled or treated as the legacy exact-seven-row `GO_RUNTIME`;
- readiness row 03 stays `blocked_by_external_state` with
  `evidence_status=unknown` with owner-override reason/status metadata;
- aggregate readiness is six `observed_pass` and one owner-override blocker;
- no missing selector/delta evidence is manufactured or inferred;
- collector retry, reinstall, uninstall, clear-data and reset remain zero;
- the override cannot authorize TASK-059 or a later independent run.

The runtime budget is exactly one launch, at most 20 safe pre-auth UI actions
and zero credential, authentication, account/payment, media/session, network,
external, QR, destructive or TASK-059 actions. Before launch and before every
UI action, screenshot visual inspection, UI tree and bounded target marker/log
are required. A missing modality hard-stops and blocks release.

The actual bounded run passes its runtime-budget and safety gates only if:

- prelaunch evidence shows Home and no visible target foreground;
- launch count is exactly one;
- postlaunch evidence contains all three modalities and is classified without
  entering data or authentication;
- `phone-coverage-001`, `phone-coverage-017` and `A002` retain distinct fresh
  covered evidence, including distinct transition endpoints;
- the discovered pre-auth login surface is terminal
  `blocked_by_boundary`, not entered and not treated as TASK-059 coverage;
- the partial green left-edge screenshot-only overlay is recorded as a
  first-class anomaly and XML/visual mismatch, with system/tooling cause no
  stronger than `likely` and product cause `unknown`;
- target force-stop, Home and capture shutdown each have confirmed cleanup
  evidence;
- final counters are launch `1`, safe pre-auth UI actions `0`, forbidden
  actions `0`, checkpoints `2` and cleanup `1`; and
- cleanup explicitly states that the clean-first-launch fixture was consumed,
  is unrecoverable under the approved scope and was not rolled back.

The three inherited coverage rows may be `covered` while overall release
remains `blocks_release`: row 03 is still unknown under owner override. TASK-059
therefore remains blocked. Public artifacts may contain only aliases,
categories, counts, status values and evidence ids; raw screenshot/XML/log,
device, package, hash, signing and command-output values remain ignored and
local-only.

Final task closure additionally requires focused tests, report/manifest
validation, compile, epic, hygiene, public-safety, docs consistency, diff and
Git-state checks plus final independent QA A, QA B, Security and Docs/Scribe
verdicts. These gates pass for the reviewed repository candidate: runner modes
PASS; 161 focused tests PASS; supplementary suite 1392 passed/4 skipped with
only the Security-forbidden TASK-045 test excluded; compile PASS; manifest
35/12/23; both hygiene modes PASS; public safety 421/0; docs 186/0; diff checks
PASS; QA A and QA B final GO 0/0/0; Security
`GO_REPOSITORY_CLOSURE / NO_NEW_RUNTIME_AUTHORITY` 0/0/0; Docs/Scribe GO.
Lifecycle is `final_reviews_passed_integration_pending` until commit, push and
default integration succeed.

## EPIC-PHONE-001 full mobile application coverage gates

EPIC-PHONE-001 is one `BOUNDED_AUTONOMOUS` epic in one thread and
`qa/epic-phone-001-full-mobile-application-test-coverage`. TASK-059 through
TASK-062 are superseded as internal stages 2 through 5; no gate may require or
create a separate task/thread/branch for those objectives. Historical
TASK-058/TASK-058A artifacts are read-only inputs and must not be rewritten.

### Resumed controller-construction gate

Owner authority now confirms `epic-phone-001-fixture-001` is synthetic/test-
only, non-real-user, limited to the current build/environment/authorized phone
and without billing/payment/subscription/entitlement impact. Its permitted
future scope is session creation/termination, read-only navigation and safe
logout. Payment, subscription, entitlement/profile/account mutation, paid
session and external/QR traversal remain forbidden. This authority is
category-only and is not a Security GO.

Final repository Security status is
`GO_REPOSITORY_COMMIT / NO_GO_C0P_EXECUTION / NO_GO_C1_EXECUTION /
BLOCK_RUNTIME / BLOCK_AUTH_ENTRY / NO_LITERAL_RUNTIME_GO`; C0P local-presence execution is also
blocked without its exact literal token. Before any local C0P execution, the
controller candidate must pass all of these repository gates:

- exact Security-fixed run, contour, target/build/fixture and passport aliases;
- exact source/HEAD/plan-hash binding with independent controller source hash;
- guarded C0P interface requiring both explicit flags, one execution, zero
  retry/resume, no subprocess/ADB/device/app/auth action and fixed contained
  ignored paths only;
- durable plan/token-bound attempt-marker exclusive creation before the sole
  secret-file read, retained across parser/validation/write/interruption failure;
- exact two-field ASCII secret grammar without printing values or hashes;
- public validate/dry-run/preflight projections restricted to category-level
  booleans, enums and counters, with no local path, plan body or full hash;
- current C0P result required and hash-bound before C1 can pass;
- adversarial tests for alias drift, stale/tampered/expired plans/tokens,
  wrong source/HEAD, extra secret fields, unsafe paths/reparse points, repeated
  execution, public-output leakage and read-before-rejection ordering;
- independent QA Reviewer A, QA Reviewer B and Security re-review with no open
  R0/R1 before any C0P plan can be considered for literal GO.

Initial review confirmed four pre-execution defects: stale no-C0P-interface
metadata, verbose dry-run plan/hash/path projection, misleading C1 fixture
status and a late one-shot check after secret read. Further adversarial review
confirmed replay after post-marker failure, missing C1 TTL/future-passport
checks, an interruption traceback and raw `OSError` text projection. These are
process evidence, not product evidence. The committed epic-branch controller
includes regressions for all findings; final QA A, QA B and Security review
counts are 0/0/0 and authorize repository commit only. Commit
`68e8bebd1162fef9aea51d88e603ebf4832d41c4` is pushed/aligned on the epic
branch; `origin/main` intentionally remains
`b268b1f198f595ec835e066169c97cdf839cc05b` until terminal runtime acceptance.
`.qa_local`, secret, device, runtime and auth counters remain exact zero. C0P
still requires the exact committed-source-bound ignored plan/passports and a
fresh literal Security token; C1/runtime/auth remain separately blocked.

`C0P-PREP` resolves only the artifact-creation dependency and is not C0P
execution. Its proposed canonical class is `PROD_SAFE` with scope qualifier
`ZERO_SECRET_ZERO_DEVICE_LOCAL_PREPARATION`, pending Security review of the
exact prep plan. Before approval it must not run. An approved prep may:

- create only the fixed ignored run directory and canonical C0P plan;
- create only the fixture-authority, target-build authorization and evidence-
  cleanup passports;
- validate fixed-root containment, Git-ignore coverage, no-reparse state and
  local evidence-sink control/retention readiness.

It must have exact zero secret-env/serial-map reads, subprocesses, device/app/
network contacts, credential/runtime/auth actions and GO/attempt/result writes.
It cannot inspect whether credential fields exist and cannot issue, derive or
materialize a Security token. Its target-build passport is authorization-only,
not current freshness/installed-state/selector/runtime evidence. The evidence-
cleanup passport is policy/readiness authorization only and passes only with
verified sink containment, control, ignore/no-reparse and retention policy. It
does not prove force-stop/Home/capture-shutdown execution, zero mutation or
successful post-run cleanup. Security blocker
`CURRENT_EPIC_TARGET_BUILD_FRESHNESS_AUTHORITY_ABSENT` remains until separately
authorized C1 launch-free freshness evidence exists.

C0P stays a separate `PROD_CONDITIONAL` one-shot contour requiring its own
committed-source-bound plan/passports and literal token. Any tracked docs commit
changes repository HEAD and invalidates the candidate plan hash prefix `f883`;
recompute after final reviewed docs commit before Security considers a token.

### Owner-local provisioner expiry and renewal gate

The accepted repository-only owner-local provisioner snapshot is bound to
executor SHA-256
`f47d97769ca1501dadd235776ced5f76f8dfa5230e09100d4fa142b8bb224263`,
loader SHA-256
`1cf7ebc750d31c363e21b27622510d0db3e03404ef7025c3b2d1a9cf27503797`
and focused-test SHA-256
`b9c92bf887c276fac0a870dfb89162c5f8551ca39883c0e4d93a8f63fa7c9375`.
Acceptance requires `40` focused passes, the earlier combined EPIC `168`
passes, retained anomalies 056–070 and QA-A/QA-B/Security repository R0/R1
`0/0`. It authorizes repository logic only.

Prepared authority expiry `2026-08-18T05:50:28Z` is terminal for that
generation. Validators and reviewers must reject extension, overwrite,
relabel, rename, replay or reuse. Fixture write, C0P, C1, secret access, device,
auth and runtime remain blocked with exact zero counters and no literal GO.

Renewal must use contour
`ZERO_SECRET_ZERO_DEVICE_CREATE_NEW_VERSIONED_AUTHORITY_RENEWAL`, create-new
versioned artifacts and immutable old artifacts. Exact resolved identities are
`authority-renewal-001`, `c0p-authority-003`, `c0p-prep-003` and
`security-c0p-003`; fixed paths are under
`authority-sets/c0p-authority-003`. Identity/path resolution is not execution
authority. The final provisioner source/HEAD rebind and renewal candidate are
one review/one commit unit; an interim provisioner commit fails the gate.

Rejected discovery/legacy-transform helper/test drafts must remain absent from
the final tracked candidate. Their anomaly records remain immutable. Cleanup
does not grant GO and must not touch `.qa_local`.

The final joint renewal/rebind snapshot passes the repository gate only at the
exact source hashes recorded in `current-state.md` and `active-run.md`.
Anomalies 071–082 are closed at repository level. Required results are core
`144 passed`, named safety suites `public_repo_safety` and
`full_tree_hygiene` `14 passed`, combined `158 passed`, plus compile and diff
PASS. Final independent review counts are QA-A `0/0/1`, QA-B `0/0/0` and
Security `0/0/1`; the sole P2 is the disclosed cooperative-timeout residual.
It requires fresh owner acceptance before later execution but does not create
an R0/R1 repository-commit blocker.

The authoritative environment-independent regression gate is
`python -m pytest -q --ignore=tests/test_task045_paired_virtual_gamepad.py` and
must pass at `1583 passed, 4 skipped`. The unfiltered suite is explicitly
`environment_blocked`, not green: two identical runs produced `1616 passed`,
`4 skipped`, `17 failed`, with every failure confined to the TASK-045 module
whose fixed ignored adapter/coverage source is absent. Under `NO_GO`, the
source must remain uninspected and must not be restored or synthesized.
Anomaly 083 preserves this limitation.

The same final gate requires EPIC validate-only/report PASS; manifest
generation/validation `pass_with_legacy` at `36/13/23`; compileall PASS; both
hygiene modes PASS; public safety `437/0`; docs consistency `187/0`; and both
cached and working-tree diff checks PASS.

`c0p-prep-003 --validate-only` is superseded by renewal and must not be treated
as a pending executable stage or reusable authority. Repository acceptance is
`NO_GO / NO_EXECUTION`: renewal, fixture write, C0P, C1, secret access, device,
auth and runtime counters remain zero for this checkpoint, while all expired
authorities stay immutable and non-replayable. The snapshot must be committed
and pushed once as a unit. Any later candidate/plan must be rebuilt and bound
to the resulting post-commit HEAD and receive fresh owner and Security
authority before execution.

The current repository contour is `PROD_SAFE_REPOSITORY_ONLY`. Its fixed-path
runner may only validate tracked inputs, publish the deterministic blocked
baseline and validate that bundle. It must reject arbitrary path/input
overrides and have no subprocess, device, network, credential or ignored-local
storage interface. A repository `closed_by_ledger` status must never be
promoted to product execution or release PASS.

Historical blocked-baseline and future runtime/auth gating remain fail-closed:

- fixture value availability alone never establishes synthetic authority; the
  current owner classification applies only to the exact current epic alias and
  does not replace C0P/C1/runtime Security GO;
- credential access/entry requires both the confirmed category-only owner
  classification and the exact current contour's literal Security token;
- values remain ignored/local-only and may not be requested, logged or
  published;
- each materially different conditional contour requires a fresh exact
  Security plan and literal epic/contour/run-bound GO;
- no agent, report, harness, plan-only budget or prior TASK-058A override may
  issue, infer or reuse that GO;
- absent classification or GO keeps stages 1 through 5
  `blocked_by_external_state`, auth entry blocked and release blocked.

The terminal coverage bundle passes only if:

- all 43 crosswalk rows appear exactly once in canonical order with no merge,
  omission, duplicate, rename or owner drift;
- exactly the three validated TASK-058A rows remain inherited `covered`, all
  33 other `phone_required` rows remain release-blocking, and seven
  deferred/audit rows preserve their prior status;
- TASK-058A inheritance is bound to its exact immutable task/run identity,
  six-of-seven readiness result, row-03 unknown/override semantics, one launch,
  zero pre-auth actions, consumed clean-first-launch state and exact modality
  evidence; a hash-rebound or internally self-consistent mutation fails;
- row 03 remains `evidence_status=unknown`, the one-run owner override is not
  reusable, and clean-first-launch is not represented as restored;
- summary/result remain `partial_blocked` and `blocks_release` with all
  unexecuted product behavior `unknown`;
- device, application, runtime/UI, authentication-entry, credential-value,
  payment/external/account, network/load, QR-follow, destructive/bypass and
  cleanup-action counters are each exact zero for this epic baseline;
- the v2 report uses canonical task id `EPIC-PHONE-001`, its generation time is
  valid non-future UTC, and manifest authority identifies the epic rather than
  `TASK-UNKNOWN`;
- public artifacts contain only approved aliases, category values, counters,
  timestamps, evidence ids and reason/status codes.

Any future conditional action requires a checkpoint before the action with
screenshot visual inspection, UI tree and bounded target-only log/marker, plus
target/oracle, remaining budget, boundary and risk/hypothesis fields. The same
modalities follow the action. Missing modality, screenshot/XML mismatch,
target ambiguity, raw spill, drift, budget exhaustion or boundary encounter is
recorded immediately and stops or safely recovers before continuation. Raw
evidence stays in a contained ignored run sink. Local-only QR decode never
authorizes follow. The kill switch is target-only force-stop, then Home, then
capture shutdown and post-stop evidence; it never authorizes reinstall,
clear/reset, APK modification/bypass or broad device cleanup.

Final repository acceptance requires runner validate/publish/report parity,
focused adversarial tests, relevant supplementary tests, compile, manifest
generation/validation, hygiene, public-safety, docs consistency, diff/Git state
checks, independent QA Reviewer A and QA Reviewer B GO, final Security GO for
repository closure, Docs/Scribe reconciliation, and a fresh remote drift gate.
The runner, focused/supplementary tests, compile, manifest, hygiene,
public-safety, docs, export-index and diff gates pass. QA Reviewer B, replacement
final QA Reviewer A and final Security returned repository-integration GO; all
non-blocking checkpoint, clock-skew and lifecycle reconciliation notes were
addressed. The fresh remote drift gate passed at exact `origin/main@e1fb05f5`,
implementation commit `55c75ca5cb6f200a44f97ce22677a21e522249f3` was pushed
to the epic branch and fast-forwarded to `main`, and the reviewed closure is
integrated with final branch/default SHA alignment.

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

## TASK-048 repository-only blocked-runtime verified gates

TASK-048 repository work is `PROD_SAFE`; device/APK/system execution is
`PROD_CONDITIONAL` and currently `BLOCK_RUNTIME`. The fixed-path CLI may only
validate tracked public-safe contracts and publish/validate the deterministic
blocked-runtime baseline. It must not read `.qa_local`, inspect APKs, call ADB,
start subprocesses, control a device, invoke components or accept path/runtime
overrides.

Verified invariants:

- exactly 19/19 terminal scenario rows;
- exactly 17 `blocked_by_device` rows;
- QA-048-014 is `blocked_by_product_boundary` and no component invocation was
  attempted;
- QA-048-019 is `observed_pass` with `static_contract` evidence only;
- runtime action count and product coverage count are zero;
- the launcher/system contour remains separate from the five-APK contract;
- execution/coverage remain blocked, release effect remains `blocks_release`,
  and no product or release PASS is claimed;
- generic TV, phone, AVD, historical profile, plan and static-artifact
  substitution fail closed.

Required commands before closure:

```text
python automation/system_lane/task048_aosp_launcher_runtime.py --validate-only
python automation/system_lane/task048_aosp_launcher_runtime.py --preflight
python automation/system_lane/task048_aosp_launcher_runtime.py --execute
python automation/system_lane/task048_aosp_launcher_runtime.py --validate-report
python -m pytest -q tests/test_task048_aosp_launcher_runtime.py
python -m pytest -q
python -m compileall -q automation tests
python automation/reporting/generate_report_manifest.py --output docs/qa/reports/report-manifest.json
python automation/reporting/generate_report_manifest.py --validate-only --manifest docs/qa/reports/report-manifest.json
python automation/quality/official_export_index.py validate-epic --root .
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
git diff --check
git status --short --branch
```

Final lifecycle status is `inactive_completed_blocked_runtime`.
Focused pytest passed 65 tests. The root supplementary suite excluding only
the Security-forbidden environment-coupled TASK-045 paired-runtime module
passed 1274 tests with 4 skipped and must not be described as a full-suite
PASS. The unfiltered suite was attempted and is `environment_blocked` due the
absent ignored TASK-045 runtime source; its latest recorded pre-final-UTF-8
result is 1305 passed, 4 skipped and 17 failed (earlier 1269/4/17). It must not
be rerun or made runnable by reading/restoring the forbidden source.

CLI expected results, compile, manifest (31 records/8 authoritative/23 legacy),
epic, both hygiene modes, public-safety (378/0), docs consistency (176/0) and
cached diff checks passed. QA-A and QA-B returned final GO with no open R0/R1;
Security returned `GO_REPOSITORY_ONLY_CLOSURE` with no open R0/R1 while keeping
`BLOCK_RUNTIME`; Docs/Scribe returned
`GO_REPOSITORY_ONLY_CLOSURE / BLOCK_RUNTIME`. Implementation/verification
commit `f85cf192d66e57d1dedcc7a8084768d2b40179d7` was pushed to the task branch
and fast-forwarded to `main`; the lifecycle docs commit requires the same final
push/alignment check before continuation.
