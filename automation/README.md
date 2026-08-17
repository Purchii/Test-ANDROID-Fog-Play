# Automation

This directory contains public-safe local QA tooling for the Android TV QA repository.

## EPIC-PHONE-001 full mobile coverage closure

`automation/phone/epic_phone_001_full_mobile_coverage.py` is a fixed-path,
deterministic repository-only validator and blocked-baseline publisher. It
losslessly projects the exact 43-row phone crosswalk once, reuses only three
tracked TASK-058A rows after hash/modality validation, and terminally blocks
all remaining required phone rows while synthetic fixture classification and a
literal runtime GO are absent. It accepts no external input path, reads no
ignored local evidence, starts no subprocess, and performs no device, APK,
application, authentication, credential, QR, payment or network action.

The three modes are `--validate-only`, `--publish-blocked-baseline` and
`--validate-report`. The output includes coverage, readiness, stage,
action-budget, anomaly and cleanup ledgers plus an evidence-envelope-v2 summary
that always preserves
`GO_REPOSITORY_PLAN/BLOCK_RUNTIME/BLOCK_AUTH_ENTRY` and `blocks_release`.

`automation/phone/epic_phone_001_runtime_controller.py` is the separate
repository-safe controller contract for the resumed epic. Its
`--validate-only` and `--dry-run` modes perform no ignored-storage, secret,
subprocess, device, application or credential action. It fixes the approved
aliases, canonical NFC/sorted JSON plan hash, C0P presence-only separation,
C1 plan/passport/token gate, C1-000/C1-999 checkpoint semantics, exact launch-
free C1 budget, anomaly and kill-switch contracts, and sufficient N+1
checkpoint budgets for future C2-C7 contours.

The future guarded command is:

```text
python automation/phone/epic_phone_001_runtime_controller.py --preflight-c1 --allow-prod-conditional-c1
```

It only validates fixed ignored local authority artifacts and still cannot
execute C1. It must not be run until the exact local plans/passports exist and
Security has issued the matching literal token. Secret presence is a separate
C0P contour and cannot be authorized by a C1 token. Its guarded fixed-path
interface is `--preflight-c0p --allow-prod-conditional-c0p`; without its exact
literal token it fails before reading the secret source. After all authority
bindings pass and before the sole bounded secret read, C0P atomically writes a
durable one-shot attempt marker. The marker is never removed on failure, so a
parser, validation, write or interruption failure cannot consume the same
token for a second credential read. C1 uses Security alias
`epic-phone-001-security-c1-001` and remains validation-only with no executor.

The separate `automation/phone/epic_phone_001_c0p_prep.py` preparer supports
`--validate-only` and a future guarded `--execute`. It accepts no path
overrides, starts no child process and has zero secret/device/app/network/auth
budget. Execution requires the exact fixed canonical candidate and prep plan,
plus a fresh `EPIC_PHONE_001_C0P_PREP_GO` literal bound to the plan hash. Before
creating under `.qa_local`, it verifies TTL, current HEAD through bounded Git metadata
reads, controller/preparer/candidate/`.gitignore` hashes, aliases, schemas and
budgets. Shared ignored parents must pre-exist. Exclusive creation of the
task-specific prep-attempt root is the first mutation and durable one-shot
marker; failure leaves it in place and the preparer never cleans up or retries.

The first authorized prep attempt failed before mutation because those shared
parents were absent; its literal GO is consumed and cannot be retried. The
separate `automation/phone/epic_phone_001_shared_parent_provision.py` executor
supports only `--validate-only` and a guarded future `--execute`. It can create,
in fixed order, only `.qa_local` and `.qa_local/evidence`, with create-new
semantics and an exact Security-bound initial-state category. Its canonical
plan and literal GO are accepted only through fixed environment names; there
are no path overrides. It reads no directory contents and creates no files,
starts no child process, and has zero secret/device/app/network/auth/runtime
budget. Execution remains blocked until the committed executor, current HEAD,
source hashes, ignore policy, initial-state attestation, TTL and exact budget
receive a fresh independent literal Security GO. Windows path-based directory
creation cannot atomically exclude a hostile external reparse swap between a
parent lstat and `mkdir`; therefore the exact plan also requires a Security-
attested exclusive workspace with no external path mutator for the bounded
execution window. Without that attestation there is no GO.

## TASK-057 Phone Full readiness authority

`automation/runtime_authority/task057_phone_full_runtime_authority.py` is a
repository-only fail-closed generator and validator for the seven independent
Phone Full readiness rows. It does not read local APK/device evidence, invoke
Android tools or ADB, or navigate the app; sanitized metadata observations are
supplied by the bounded Orchestrator workflow. Individual non-security rows may
close under `GO_METADATA_CONDITIONAL`, while the tracked aggregate remains
`BLOCK_RUNTIME` unless all seven rows and the separate cleanup passport are
fresh, confirmed and non-expired, and row 7 plus cleanup have Security
`GO_RUNTIME`. Missing, duplicate, merged, stale, unsafe or partially passing
rows block release.

## TASK-057R Phone Full authorized reinstall revalidation

`automation/runtime_authority/task057r_phone_full_authorized_reinstall_readiness.py`
is the separate repository-only validator for the sanitized TASK-057R result.
It validates fixed TASK-057R readiness, reinstall-action and cleanup ledgers;
it never reads local APK/device evidence, invokes Android tooling/ADB, performs
package actions or navigates the app. The tracked result records one authorized
target-only uninstall and one ordinary candidate install as `observed_pass`,
while readiness remains `BLOCK_RUNTIME` because synthetic-session,
clean-first-launch and runtime evidence/cleanup passports are independently
absent. Successful reinstall cannot infer any of those rows or Security
`GO_RUNTIME`.

## TASK-058 Phone Full first-launch and pre-auth coverage

`automation/phone/task058_phone_first_launch_pre_auth_coverage.py` is the
repository-only generator and validator for the public-safe blocked TASK-058
closure. It preserves the exact seven TASK-057 readiness authorities, the
one-shot package-action ledger, the three inherited screen/transition rows and
all process anomalies. It never reads ignored local evidence, invokes Android
tools or ADB, controls a device, launches the app or performs runtime coverage.
Its baseline remains `BLOCK_RUNTIME`, `blocks_release`, with product runtime
`not_run` until all independent passports and Security `GO_RUNTIME` exist.

## TASK-048 AOSP/launcher system-lane authority

`automation/system_lane/task048_aosp_launcher_runtime.py` implements the
repository-only authority allowed by the current
`GO_REPOSITORY_ONLY / BLOCK_RUNTIME` Security decision. Its fixed
`--validate-only`, `--preflight`, `--execute`, and `--validate-report` modes do
not read ignored local storage or APKs, start subprocesses, contact ADB, or
control a device. The approved exact FogPlay Stick mapping is missing while
physical availability remains unknown, generic TV/phone/AVD substitution is
forbidden, and the launcher/system cluster remains separate from the five-APK
contract.

The published baseline terminally classifies all 19 catalog rows while keeping
runtime and product coverage at zero. QA-048-014 stops at the unauthorized
component boundary. QA-048-019 passes only static terminal-ledger
reconciliation; it is not a product or release PASS.

## TASK-045A Phone visual transition coverage

The TASK-045A Phone visual transition runner is a static-only typed-adapter
validator and public-safe bundle publisher. It never
controls an Android device or application. Historical TASK-045 media remains
ignored and audit-only; fresh session-dependent coverage is rejected unless a
task-authoritative synthetic-session passport is supplied to the guarded
ingest mode. The repository baseline is intentionally blocked while Security
holds runtime at `BLOCK_RUNTIME`.

## Runtime Smoke Bootstrap

`automation/runtime_smoke_bootstrap/` contains the TASK-001 blocked-report generator. It is a local dry-run utility and does not interact with an Android device, app binary, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- complete metadata still does not execute runtime checks in TASK-001.

## Exported Component Guards

`automation/exported_component_guards/` contains the TASK-002 exported component guard skeleton generator. It is a local dry-run utility and does not interact with an Android device, app binary, network service, exported component or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing approved guard scope metadata -> `blocked`;
- complete metadata produces a `not_run` plan only and still does not execute runtime checks in TASK-002.

## Reporting and Release Gates

`automation/reporting/` contains the TASK-003 release gate report generator. It is a local dry-run utility and does not interact with an Android device, app binary, network service, WebView, WebRTC session or production environment.

The generator is designed to fail closed:

- missing release metadata -> `blocked`;
- malformed metadata -> `blocked`;
- runtime-dependent R0/R1 gates require `status=pass` and `evidence_status=confirmed`;
- blocked, failed, not-run or non-confirmed R0/R1 gates keep the release decision blocked;
- notes and artifact references are redacted before output.

TASK-038 adds `automation/reporting/generate_report_manifest.py`, an
offline/static report manifest generator and validator. It indexes only
tracked public-safe JSON reports matching `docs/qa/reports/*.json`, computes SHA-256
values, validates v2 evidence envelopes, records legacy migration blockers and
fails closed on duplicate authority, missing/stale references, hash drift,
unknown schemas, unsafe artifact refs and raw/private-looking values. It does
not read ignored `.qa_local` evidence, APKs, Android devices, runtime logs,
network/API material or private endpoints.

TASK-039 adds `automation/reporting/generate_release_readiness_report.py`, an
offline/static release-readiness generator backed by the TASK-038 manifest. It
does not accept free-form gate assertions as release evidence: R0/R1 gates can
pass only from authoritative v2 manifest records with confirmed evidence,
reviewer approval, valid hashes and confirmed evidence storage plus
cleanup/rollback prerequisites. The current repository output is intentionally
`blocked` while no external authoritative v2 gate evidence exists. Before any
content read, production use accepts only the exact relative, Git-tracked
`docs/qa/reports/report-manifest.json`; synthetic temp-repo manifests require
an in-test mock of the Git-index probe; production code exposes no bypass.

## Manual Runtime Maps

`automation/manual_runtime_maps/` contains the TASK-004 manual runtime screen/focus map report generator. It is a local dry-run utility and does not interact with an Android device, app binary, network service, WebView, WebRTC session or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing synthetic fixture policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- complete metadata produces `not_run` screen/focus map templates only and never claims runtime behavior passed in TASK-004;
- notes and artifact references are redacted before output.

## Network/Offline Safe Runner

`automation/network_offline_safe_runner/` contains the TASK-007 network/offline policy report generator. It is a local dry-run utility and does not interact with an Android device, app binary, backend, proxy, packet capture, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing network profile policy metadata -> `blocked`;
- missing resource budget metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` network/offline plan only and never claims runtime behavior passed in TASK-007;
- notes and artifact references are redacted before output.

## WebView/Payment Safe Runner

`automation/webview_payment_safe_runner/` contains the TASK-008 WebView/payment safe QA plan report generator. It is a local dry-run utility and does not interact with an Android device, app binary, WebView, browser, redirect target, payment flow, backend, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing WebView fixture policy metadata -> `blocked`;
- missing staging-only non-real-payment policy metadata -> `blocked`;
- missing synthetic user policy metadata -> `blocked`;
- missing resource budget metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` WebView/payment plan only and never claims runtime or payment behavior passed in TASK-008;
- notes, flow aliases and artifact references are redacted before output.

## Compatibility/Device Matrix

`automation/compatibility_device_matrix/` contains the TASK-009 compatibility/device matrix report generator. It is a local dry-run utility and does not interact with an Android device, app binary, WebView, WebRTC session, payment flow, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved device matrix policy metadata -> `blocked`;
- missing approved target class metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing synthetic fixture policy metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` compatibility matrix only and never claims runtime behavior passed in TASK-009;
- notes and artifact references are redacted before output.

## CI/Nightly Smoke

`automation/ci_nightly_smoke/` contains the TASK-010 CI/nightly smoke plan report generator. It is a local dry-run utility and does not create live CI schedules, access CI secrets, upload artifacts, install private dependencies, or interact with an Android device, app binary, WebView, WebRTC session, payment flow, network service or production environment.

The generator is designed to fail closed:

- missing approved static CI scope metadata -> `blocked`;
- missing approved schedule policy metadata -> `blocked`;
- missing repository safety policy metadata -> `blocked`;
- missing resource budget metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing artifact retention policy metadata -> `blocked`;
- missing dependency policy metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` CI/nightly plan only and never claims live CI, runtime or device behavior passed in TASK-010;
- notes, CI job aliases and artifact references are redacted before output.

## Navigation Transition Map

`automation/navigation_transition_map/` contains the TASK-011 navigation transition map report generator. It is a local dry-run utility and does not interact with an Android device, app binary, WebView, WebRTC session, payment flow, network service or production environment.

The generator is designed to fail closed:

- missing approved build metadata -> `blocked`;
- missing approved target metadata -> `blocked`;
- missing approved configuration metadata -> `blocked`;
- missing transition scope metadata -> `blocked`;
- missing screen alias policy metadata -> `blocked`;
- missing input event policy metadata -> `blocked`;
- missing fixture policy metadata -> `blocked`;
- missing resource budget metadata -> `blocked`;
- missing redaction policy metadata -> `blocked`;
- missing evidence storage metadata -> `blocked`;
- missing cleanup and rollback metadata -> `blocked`;
- missing Security or QA review metadata -> `blocked`;
- complete metadata produces a `not_run` navigation transition plan only and never claims runtime transition behavior passed in TASK-011;
- notes, transition aliases and artifact references are redacted before output.

## Quality Guards

`automation/quality/` contains local static repository hygiene and public-safety
guards. These tools do not interact with Android devices, APKs, WebView,
WebRTC, payment flows, network services or production systems.

- `full_tree_hygiene_scan.py` scans tracked/public-safe text trees for
  whitespace, EOF and JSON BOM hygiene.
- `docs_consistency_link_sanity.py` scans tracked Markdown files for broken
  local links, missing anchors and unsafe dereferenceable local/raw targets. It
  does not crawl external links or read ignored `.qa_local` evidence. TASK-040
  makes discovery and input handling fail closed: Git errors and zero eligible
  Markdown inputs are blocked, all scan paths are validated before content I/O,
  and path/read diagnostics use fixed sanitized reason codes.
- `public_repo_safety_scan.py` scans tracked/public-repository paths for
  forbidden raw artifact families such as APKs, raw evidence, signing material,
  local config and local-only artifact directories. It reports only rule ids,
  paths and category-level reasons, never matched file contents.
- `synthetic_redaction_corpus.py` defines fabricated public-safe redaction test
  specimens for TASK-017. It is local/static only and must not be populated
  from real evidence, APKs, endpoints, QR targets, credentials or device data.

## API-layer Contract Coverage

`automation/api_layer_contract/` contains the TASK-028 through TASK-033 offline
API-layer contract validators. They read an owner-provided API audit pack only
after the pack has been extracted into ignored local quarantine storage and emit
public-safe summaries with aliases, counts, categories, statuses and blockers
only.

The validators do not make live REST, WebSocket, STOMP, DataChannel, gamepad,
Android runtime, APK, payment, stream/session or production calls. They validate
matrix shape, fixture/sequence references, fixture JSON readability, schema JSON
readability and offline protocol fixture boundaries, then record live API and
runtime execution as `not_run`. TASK-033 is stricter: it is synthetic/static
only, does not read ignored API pack raw values, and validates fabricated
redaction/production-safety guard specimens plus tracked public-summary counts.

## Static Text Inventory

`automation/static_text_inventory/` contains the TASK-035 static text inventory
builder. It reads the ignored local sanitized static artifact, writes raw string
records only to ignored `.qa_local/static_text_inventory/`, and emits a
public-safe report with counts, hash prefixes, categories, redaction classes
and explicit blockers when the full raw static string list is unavailable.

The builder does not run Android runtime, ADB, APK install/launch,
decompilation, smali inspection, live backend/API/network, payment, stream or
account actions. Runtime text visibility and translation/accessibility behavior
remain `not_run` or `unknown` until a separate approved runtime task.

## Local Runtime Preflight

`automation/runtime_preflight/` contains the TASK-042 fail-closed local APK,
launcher, Android SDK/ADB/AVD and device readiness preflight. Its
`--validate-only` lane is tracked/static and does not read `.qa_local` or start
subprocesses. `--preflight` is canonical presence-only. `--execute` requires all
explicit allow flags and a repo-relative ignored evidence root before it may
perform the Security-approved read-only metadata and inventory actions.

The conditional lane is deliberately bounded:

- exactly five APK contract entries are classified; extra entries never join
  the main bundle;
- raw hashes, package/version/signature output and machine identities remain
  local-only;
- ADB permits one or two simultaneously connected targets only when every
  identity has a unique canonical reviewed public-safe mapping; otherwise it
  stops before all per-device calls;
- AVD discovery is tooling-only and cannot assert product compatibility;
- the launcher contour and actual FogPlay Stick selector remain separate and
  fail closed when their mappings are absent;
- APK install/launch, UI input, logs, screenshots, payment, account, network
  mutation and production actions are outside this runner.

The tracked public-safe authority is the v2 summary plus scenario ledger and
readiness matrix under `docs/qa/reports/`. After the owner changed the connected
device set, the current tooling-restricted rerun terminally classifies all 18
scenarios as 6 `observed_pass`, 8 blocked and 4 `tooling_defect`; configured SDK
access prevented fresh APK content-integrity, ADB and AVD evidence, so the exact
five-entry bundle is presence-confirmed but integrity-blocked. No release or
product-runtime claim is made.

## Offline Regression Surface Selector

`automation/regression/task043_surface_registry_selector.py` implements the
TASK-043 fail-closed surface registry and selector. It reads only a fixed set of
tracked public-safe epic catalogs, matrices and report-manifest projections.
Its production CLI has no path overrides and never reads `.qa_local`, APKs,
SDK/ADB/AVD, devices or runtime evidence, and never starts a child process or
network action.

The four modes are `--validate-only` (constants only), `--preflight` (fixed
read-only contracts), `--execute` (deterministic offline static output
generation) and `--validate-report` (fixed hash/count reconciliation). Legacy
TASK-019…040 records remain historical, stale and non-authoritative. The
selector distinguishes physical, paired physical, AVD, synthetic, static and
mapped-only evidence, rejects cross-family substitution, preserves an initial
failure after retry/recovery and emits TASK-044 rows as selection-only
`not_run` work. A passing TASK-043 static contract does not claim product
runtime coverage or release readiness.

## TASK-044 TPV13 Reference-lane Evidence Adapter

`automation/native_regression/task044_tpv13_reference_lane.py` is a fail-closed
adapter for the Television Full physical reference lane. It never controls a
device. Instead, it validates and ingests a typed, ignored local-only runtime
adapter whose evidence was collected under the separately approved bounded
runtime procedure.

Run the four modes in this order:

```text
python automation/native_regression/task044_tpv13_reference_lane.py --validate-only
python automation/native_regression/task044_tpv13_reference_lane.py --preflight --adapter-input .qa_local/evidence/task-044/runtime-adapter.local.json
python automation/native_regression/task044_tpv13_reference_lane.py --execute --adapter-input .qa_local/evidence/task-044/runtime-adapter.local.json --allow-prod-conditional-ingest
python automation/native_regression/task044_tpv13_reference_lane.py --validate-report
```

The adapter path must resolve to a regular, non-link JSON file under the exact
ignored `.qa_local/evidence/task-044/` root. External, symlinked/reparse or
non-canonical paths fail closed. `--allow-prod-conditional-ingest` authorizes
ingest only; it does not authorize ADB, APK install/launch, UI input, logs,
screenshots, network activity or any other device action.

The public bundle consists of the v2 summary plus scenario, checkpoint and
anomaly ledgers under `docs/qa/reports/`. Every scenario is terminally
classified, every runtime attempt carries screenshot, UI-tree and runner-log
references, and retry/recovery cannot erase an initial failure. The phone is
inventory-only and cannot satisfy the TV lane. Payment/session start,
QR/browser traversal, logout/account mutation and raw device/build/account/QR
publication are forbidden. The current runtime result blocks release pending
oracle closure: 32 terminal rows (29 P0/3 P1), comprising 16
`observed_pass`, 2 `confirmed_defect`, 11 `observed_fail` and 3
`blocked_by_oracle`; execution is `fail` and coverage is `partial_blocked`.
The physical TV is no longer available for a repeat run, so additional TV
runtime is `blocked_by_device`. The remaining phone-full phone is out of this
runner's scope and received no TASK-044 runtime action.

## Safety Rules

Automation in this repository must not request or store:

- source or decompiled application code;
- secrets, tokens, cookies, sessions or credentials;
- private endpoint inventories;
- APK, AAB, DEX, native or signing artifacts;
- raw logs, screenshots or videos;
- real user data or real payment data.

Runtime/device execution belongs to a future approved task after prerequisites, redaction and review gates are satisfied.
