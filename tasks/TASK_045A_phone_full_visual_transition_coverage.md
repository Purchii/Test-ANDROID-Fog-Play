# TASK-045A — Phone Full visual screen and transition coverage

## Mode

`BOUNDED_AUTONOMOUS`

## Production safety

- Repository implementation and validation: `PROD_SAFE`.
- Physical phone runtime: `PROD_CONDITIONAL`, currently `BLOCK_RUNTIME`.
- Television and paired evidence: `blocked_by_external_state` because the TV is unavailable.

## Goal

Create an explicit, fail-closed Phone Full screen/state/navigation graph that
distinguishes terminal ledger closure from fresh visual coverage. Every
approved reachable branch must end as `covered`, `blocked_by_boundary`,
`blocked_by_tooling`, `blocked_by_external_state`, or
`not_run_out_of_scope`, with public-safe evidence identifiers.

## Branch

`qa/task-045a-phone-full-visual-transition-coverage`

## Dependencies

- completed TASK-045 lifecycle closure;
- approved Phone Full lane preflight;
- task-authoritative synthetic-session passport for session-dependent product
  coverage;
- Security/Prod-safety `GO` before any device action.

## Required scenario contract

`docs/qa/epics/scenarios/task045a_phone_visual_transition_branches.csv`

The contract contains 17 public-safe branch families, `A001` through `A017`.
Runtime discovery may add screen states and edges, but may not remove or merge
the required families.

## Evidence eligibility

- Historical TASK-045 screenshots, UI trees and logs are quarantined audit
  evidence only.
- The category-only audit records 20 PNG, 19 XML and 19 bounded-log artifacts.
- Prior checkpoint `cp001` is incomplete because XML and bounded log are
  absent.
- Every historical item has `audit_only=true` and
  `counts_as_product_coverage=false`.
- A session-dependent node or edge can be `covered` only when the active run
  has `active_session_provenance=approved_synthetic_fixture` and a separately
  validated task-authoritative session passport.
- Fresh covered checkpoints require a visually inspected screenshot, UI tree
  and bounded target-app log/marker captured inside the run window.
- Every public terminal ledger row carries its own redacted evidence ids, not
  only an aggregate count.
- A runtime GO passport must bind the current task/run, phone alias, build
  alias, lane alias, reviewer decision and authority evidence id inside a
  bounded current-UTC confirmation/expiry window. The canonical local path is
  fail-closed against symlink or reparse escape.

## Runtime boundaries

Forbidden without a later explicit oracle/fixture:

- payment or paid/active game session start;
- account, profile, logout or session mutation;
- QR, browser, WebView or other external traversal;
- network shaping or unsafe lock/unlock;
- unknown targets;
- APK modification, decompile, bypass, uninstall, clear-data or downgrade
  override.

Visible QR may be decoded only in ignored local evidence with the established
local decoder. The target must not be followed and raw target data must not be
published.

## Required outputs

- strict typed adapter schema;
- static-only validator/publisher runner;
- scenario ledger;
- screen/state ledger;
- transition ledger;
- branch-closure ledger;
- anomaly ledger;
- boundary ledger;
- cleanup ledger;
- v2 public-safe summary and report-manifest entry.

## Runner contract

```text
python automation/gamepad/task045a_phone_visual_transition_coverage.py --validate-only
python automation/gamepad/task045a_phone_visual_transition_coverage.py --preflight --adapter-input .qa_local/evidence/task-045a/runtime-adapter.local.json
python automation/gamepad/task045a_phone_visual_transition_coverage.py --execute --adapter-input .qa_local/evidence/task-045a/runtime-adapter.local.json --session-passport .qa_local/evidence/task-045a/synthetic-session-passport.local.json --allow-prod-conditional-ingest
python automation/gamepad/task045a_phone_visual_transition_coverage.py --publish-blocked-baseline
python automation/gamepad/task045a_phone_visual_transition_coverage.py --validate-report
```

The runner never performs ADB, APK, device, app, network or external actions.
It only validates typed ignored input and atomically publishes sanitized
tracked outputs. Runtime capture helpers remain ignored under
`.qa_local/tools/task045a/`.

## Acceptance criteria

- no closed TASK-045 artifact is modified;
- prior evidence is audit-only and cannot satisfy product coverage;
- unproven session provenance blocks every session-dependent node and edge;
- missing TV blocks every paired-only branch and never produces paired proof;
- TV/Television/paired-side screen aliases, layouts, states, edges and evidence
  are categorically ineligible for the independent Phone Full coverage graph;
- covered nodes require all three fresh modalities and visual inspection;
- transition edges link exact from/to nodes and preserve first failures,
  recoveries and recurrences;
- covered edges use distinct same-scenario endpoints, the exact union of both
  fresh visual triplets and a positive bounded attempt index;
- covered branch graphs contain every discovered node/edge, are directionally
  connected and enforce branch-specific list, menu, overlay, recurrence,
  lifecycle, read-only-route and boundary-recovery invariants;
- long-list initial/later segments, menu states, overlays and screenshot/XML
  mismatches are first-class state data;
- approved reachable branches cannot be classified `not_run_out_of_scope`;
- boundaries and cleanup remain non-mutating and redacted;
- the blocked baseline is `blocked` / `blocks_release`.

## Verification

```text
python automation/gamepad/task045a_phone_visual_transition_coverage.py --validate-only
python automation/gamepad/task045a_phone_visual_transition_coverage.py --validate-report
python -m pytest -q tests/test_task045a_phone_visual_transition_coverage.py
python -m compileall -q automation tests
git diff --check
```

## Stop conditions

Stop runtime work when Security remains `BLOCK_RUNTIME`, the synthetic-session
passport is missing/unproven, the approved phone lane is not authoritative, a
required action crosses a boundary, or raw/local-only data could enter tracked
output. Continue safe static implementation and blocked reporting.
