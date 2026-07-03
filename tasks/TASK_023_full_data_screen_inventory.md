# TASK-023 - Full data screen inventory

## Mode

`NON_AUTONOMOUS`.

Default branch merge/push is forbidden without an explicit owner command.

## Goal

Create a public-safe full data inventory for all safe reachable approved screen
families and navigation branches on the existing approved MTC Fog Play Android
TV lane, using TASK-020 full screen-family inventory, TASK-021 offline/runtime
finding and TASK-022 gamepad findings as baseline evidence.

TASK-023 focuses on data/state/content categories, not only navigation. It must
separate:

- screen-family coverage;
- visible data categories;
- dynamic vs static content classification;
- list/grid segment samples;
- empty/error/loading/auth/legal/payment/QR/boundary states;
- focus/action metadata;
- recurrence and prior evidence links;
- redaction class and collection policy.

## Approved Lane

Runtime work is `PROD_CONDITIONAL` and may use only the already approved lane:

- `device_alias`: `tv-tpv-013`;
- `runtime_profile_alias`: `tv-tpv-a12-013`;
- `build_alias`: `task-005-local-apk-001`;
- `synthetic_user_alias`: `qa-user-phone-001`.

All raw screenshots, XML, videos, logs, QR targets, phone/OTP values, device
identifiers, server/tariff/payment values and private component values must
remain ignored under `.qa_local/evidence/task-023/`.

## Public-Safe Data Inventory Schema

Each inventory row must include:

- `screen_alias`;
- `screen_family`;
- `state_category`;
- `coverage_status`: one of `covered`, `blocked_by_boundary`,
  `blocked_by_tooling`, `blocked_by_external_state`, `not_run_out_of_scope`;
- `evidence_status`;
- `evidence_ids`;
- `prior_evidence_refs`;
- `data_categories_visible`;
- `data_dynamics`;
- `list_or_grid_sampling`;
- `focus_action_metadata`;
- `redaction_class`: `public_safe`, `local_only`, `forbidden` or
  `not_collected`;
- `public_safe_summary`;
- `local_only_data_classes`;
- `forbidden_data_classes`;
- `boundary_policy`;
- `risk_or_hypothesis`;
- `test_design_implication`.

## Scope

In scope:

- derive a public-safe data inventory from TASK-020, TASK-021 and TASK-022
  confirmed runtime evidence;
- add TASK-023 runtime checkpoints only after this scope/gate document exists;
- treat every newly encountered or recurring screen/state as a checkpoint
  before continuing navigation;
- inspect screenshots/visual evidence in addition to UIAutomator XML;
- record list/grid samples and truncation/lazy-load behavior at category level;
- classify dynamic lists such as games catalog and game-specific server rows by
  public-safe data model, field categories, variability, focus/scroll behavior
  and sampled segments rather than by publishing or requiring complete value
  dumps;
- decode new QR targets only into local-only artifacts with the established
  `jsqr` path, and never open them;
- recover safely from boundaries by Back/B when confirmed safe or force-stop
  plus approved explicit relaunch when navigation recovery fails.

Out of scope / forbidden:

- real payment, checkout completion, subscription or billing;
- paid stream/session/game start;
- external QR/browser/WebView traversal;
- captcha solving, bypass or challenge-internal inspection;
- profile/account mutation beyond separately approved synthetic auth/logout
  boundaries;
- APK source, decompile, smali, patching, resigning or modification;
- TLS/pinning bypass, proxying, packet capture or private endpoint extraction;
- publishing raw user-like values, endpoints, device identifiers, screenshots,
  XML, logs, QR targets, payment/server/tariff values or APK hashes.
- complete public enumeration of dynamic game titles, server aliases, ping
  values, GPU/CPU strings, launcher badges or tariff/price values.

## Runtime Budget

- `max_runtime_duration_minutes`: 120;
- `max_screen_checkpoints`: 120;
- `max_actions_total`: 450;
- `max_focus_moves_per_screen`: 24;
- `max_selects_per_screen`: 4;
- `max_boundary_recovery_attempts`: 4;
- `max_revisits_per_screen_family`: 3.

Budget exhaustion is partial coverage, not completion. Closure requires a
ledger where every currently safe reachable approved screen family/branch is
classified with an allowed terminal status and evidence ids.

## Acceptance Criteria

- Public-safe TASK-023 report exists under `docs/qa/reports/`.
- Public-safe machine-readable TASK-023 summary/ledger JSON exists under
  `docs/qa/reports/`.
- The schema above is implemented in the machine-readable summary.
- Every TASK-020/TASK-022 baseline screen family is mapped to data categories or
  an explicit terminal status.
- Catalog data inventory reaches a recorded bottom/no-change condition or
  explicitly records why complete value enumeration is not collected.
- Game-specific server list inventory records representative segments, field
  categories and dynamic-list policy; complete server row/value enumeration is
  explicitly terminally classified rather than silently omitted.
- TASK-023 runtime preflight is recorded without raw ADB/device output in git.
- Raw evidence remains under ignored `.qa_local/evidence/task-023/`.
- Multi-agent Planner, Builder, QA Reviewer A, QA Reviewer B,
  Security/Prod-safety Reviewer and Docs/Scribe outputs are recorded.
- Verification includes JSON sanity, docs/schema sanity, `git diff --check`,
  hygiene/public-safe scans, diff review and relevant tests if scripts/tests are
  added.

## Stop Conditions

Stop or recover if a path requires unclear Select/confirm targeting, real
payment, paid session start, external traversal, account mutation, captcha
solving, private endpoint/secret/source access, raw value publication,
unrecoverable focus trap, repeated crash/ANR, failed cleanup/relaunch or missing
approved runtime prerequisites.
