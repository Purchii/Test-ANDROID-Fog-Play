# TASK-058 — Phone Full first-launch and pre-auth coverage

## Contract

- Mode: `BOUNDED_AUTONOMOUS`; runtime is `PROD_CONDITIONAL`.
- Owner artifact selection dated 2026-08-16: the exact ignored/local-only,
  same-repository candidate is represented publicly only as
  `task058-selected-phone-full-001`; it supersedes `main-apk-03` for the
  TASK-058 package action only.
- Owner package-action authority: uninstall only the freshly mapped installed
  Phone Full target, accepting loss of only that target application's local
  data/session; then perform exactly one ordinary install of
  `task058-selected-phone-full-001`. Retry count is zero.
- Dependencies before package action: fresh remote/base alignment; one
  unambiguous authorized device selector; one regular non-reparse selected APK
  with confirmed same-repository provenance; exact package/family/target
  mapping; integrity, signing, version, min/target-SDK, ABI and compatibility
  oracles; ignored evidence sink; bounded action budget; one-shot stop/no-retry
  contingency; failure recovery and cleanup contract; and pre-action Security
  GO for this exact plan.
- Dependencies before launch or navigation: all exact seven TASK-057 authority
  rows must be freshly revalidated and `observed_pass`, including independent
  synthetic-session, clean-first-launch and runtime evidence/cleanup passports,
  and Security must issue `GO_RUNTIME`. Package-action success, accepted local
  state loss or an empty post-install session cannot infer any of those rows.

## Goal and acceptance

Capture every approved safely reachable state and transition from OS launch
intent through first-render, loading, onboarding/legal/consent/auth-entry,
retry/error/empty and back/exit behavior. Maintain explicit screen, state,
transition, overlay, recurrence, anomaly, boundary and cleanup ledgers. Long or
paged content must record initial/later segments and truncation/lazy-loading.

Every approved reachable row must be `covered` with fresh run-window screenshot
visual inspection, UI tree and bounded target-app marker/log,
or carry one permitted terminal blocker. XML never substitutes for visual
inspection. Historical evidence cannot count.

The owner instruction to proceed aggressively requires continuation beyond a
successful install until this TASK-058 terminal coverage ledger is complete or
a genuine hard safety blocker is reached. It does not expand scope into
credential entry, authentication, TASK-059+, payment, paid/media session start,
network shaping, destructive UI actions or external QR/browser traversal.

Before every navigation action record a checkpoint with screen alias, state,
evidence status, focus/action categories and risk/hypothesis. Record anomalies
immediately. A missing modality is `blocked_by_tooling` / `blocks_release`.
`not_run_out_of_scope` is forbidden for approved reachable rows.

## Tracked deliverables and closure

Tracked ledgers: scenario, screen/state, transition, overlay/recurrence,
anomaly, boundary and cleanup. Common columns are `row_id`, `source_crosswalk_id`,
`approved_scope`, `reachable`, `status`, `screen_alias`, `state_category`,
`focus_category`, `action_category`, `evidence_status`, `screenshot_id`,
`ui_tree_id`, `log_marker_id`, `reason_code`, `release_effect` and
`cleanup_status`; transitions also require distinct `from_checkpoint_id` and
`to_checkpoint_id`. Closure publishes exact required/discovered/covered/blocked
counts with no missing/duplicate rows. Revalidate TASK-057 authority before
each resumed run. PASS requires all approved reachable TASK-058 rows covered.

## Gates, safety, cleanup and release effect

- Revalidate the exact seven TASK-057 rows independently after the authorized
  package action. Launch remains forbidden unless every row passes and Security
  issues `GO_RUNTIME`; if Security permits reinstall but not launch, close the
  package action safely and leave TASK-058 runtime `not_run`.
- Stop without retry on selector, artifact, package/family, signing, device,
  compatibility or evidence-sink drift/ambiguity; uninstall/install/launch
  failure; unexpected package/device state; raw spill; missing authority; or
  scope expansion. Alternate artifacts and retries require fresh owner
  authority.
- No real/unknown session, credential entry, account mutation, external
  browser/QR traversal, network shaping, separate clear data, device reset,
  other-package change, downgrade/test/grant/bypass flag, APK modification,
  re-signing or decompilation. The exact one-shot target uninstall above is the
  only uninstall exception.
- Cleanup returns to the owner-approved safe pre-auth state without creating an
  account/session, verifies capture shutdown and preserves raw media locally.
- An unreproducible genuine first launch, missing visual modality, unclassified
  screen/transition or unsafe boundary is release-blocking.

## Immediate process anomalies

- `TASK058-PROCESS-ANOMALY-001` is `confirmed`; public-safe alias
  `preflight_result_object_syntax_failure`. A corrected bounded preflight
  attempt expected a category-only result but produced a PowerShell parser
  error before execution. No APK, ADB or device action occurred and product
  impact is none. Likely cause: an inline command expression inside a result
  hashtable. Precompute values before result construction and accept no failed
  output as evidence.
- `TASK058-PROCESS-ANOMALY-002` is `confirmed`; public-safe alias
  `sdk_root_scalar_indexing_failure`. A corrected read-only preflight expected
  Android tool resolution, but a single SDK-root string was indexed as its
  first character and path resolution failed closed. Only candidate file
  attributes were read; no Android tooling, ADB, device or package mutation
  occurred, and no output was accepted as evidence. Likely cause: PowerShell
  scalar-versus-array behavior. Wrap pipeline results in an array before
  indexing.
- `TASK058-PROCESS-ANOMALY-003` is `confirmed`; public-safe alias
  `combined_package_action_command_policy_rejection`. One combined preflight
  plus action PowerShell command expected the exact one-shot sequence but was
  rejected by execution policy before process start. No command executed;
  uninstall/install counts remain `0/0`; no device, package or product impact
  occurred and no output was accepted as evidence. Likely cause: overlong or
  compound-command policy. Use short, separately verified action-boundary steps
  while retaining the total budget of one uninstall, one ordinary install and
  zero retries.
- `TASK058-PROCESS-ANOMALY-004` is `confirmed`; public-safe alias
  `postinstall_pull_stderr_raw_path_spill`. After the one uninstall and one
  ordinary install succeeded, the post-install equivalence pull emitted a raw
  device-side path on native stderr and PowerShell stopped before hash/signing,
  unrelated-package-delta and final selector checks. No raw value entered a
  tracked artifact, the temporary local APK was removed, launch remained zero
  and no retry was attempted. Future collectors must capture and sanitize
  native stderr before any public projection.
- `TASK058-PROCESS-ANOMALY-005` is `confirmed`; public-safe alias
  `schema_validator_invocation_and_spec_marker_mismatch`. The first focused
  repository run stopped because the static task marker and schema-validator
  call signature were incomplete. Two tests failed and thirteen passed; no
  runtime action occurred. The remediation keeps the first failure, adds exact
  contract parity and reruns the focused suite in this task.
- `TASK058-PROCESS-ANOMALY-006` is `confirmed`; public-safe alias
  `report_manifest_unsupported_write_flag`. The first manifest-regeneration
  attempt used an unsupported write flag and returned a usage error without
  changing the manifest. Product/runtime impact is none. The remediation uses
  the documented default write mode and validates the regenerated manifest.
- `TASK058-PROCESS-ANOMALY-007` is `confirmed`; public-safe alias
  `qa_reviewer_read_only_baseline_rewrite`. During independent read-only review,
  the reviewer mistakenly invoked deterministic baseline generation and
  rewrote only the already-derived TASK-058 public-safe report bundle. The
  Orchestrator regenerated and revalidated the bundle from the fixed runner;
  no APK, device, local-only evidence or product action occurred. Product
  impact is none.
- `TASK058-PROCESS-ANOMALY-008` is `confirmed`; public-safe alias
  `guessed_docs_checker_path_failure`. Independent QA invoked a guessed
  nonexistent docs-checker path, which failed before checker execution. The
  canonical docs consistency/link checker was then located and passed. No APK,
  device, local-only evidence or product action occurred; product impact is
  none.
- `TASK058-PROCESS-ANOMALY-009` is `confirmed`; public-safe alias
  `qa_source_marker_regex_syntax_failure`. A malformed quoted regular
  expression in final QA review was rejected before its read-only search ran.
  No output was accepted and no file, APK, device, local-only evidence or
  product state changed. Review uses literal or prevalidated searches; product
  impact is none.
- `TASK058-PROCESS-ANOMALY-010` is `confirmed`; public-safe alias
  `qa_stop_instruction_coordination_wait`. After an explicit stop-tools
  instruction, independent QA invoked only a coordination wait. It performed
  no shell, filesystem, APK, device, local-evidence or product action and
  changed no state. Final review returns a verdict without further tool calls;
  product impact is none.
- `TASK058-PROCESS-ANOMALY-011` is `confirmed`; public-safe alias
  `owner_action_top_level_schema_mismatch`. A new owner-action top-level field
  was not allowed by the v2 evidence envelope, so summary/manifest validation
  blocked and three of 111 focused tests failed. Owner actions were moved into
  allowed public-safe unknown records and source-of-truth; the first failure is
  retained and product impact is none.
