# Active run

## Run Metadata

Mode: `BOUNDED_AUTONOMOUS`
Thread title: `TASK-018 - Docs consistency and link sanity checks`
Thread status: `active_final_review_passed`
Fresh thread verified: `yes; continuation thread 019f2915-4152-7ee2-b37c-21b892dcc845 accepted and renamed`
Task ID: `TASK-018`
Task branch: `qa/task-018-docs-consistency-link-sanity`
Default branch: `main`
Base commit: `29b299c79f78377666d6c130c91162448e4e5b1b`
Merge/push authority: `BOUNDED_AUTONOMOUS after all gates pass; no force-push`
Production safety classification: `PROD_SAFE` for tracked-docs/static link checks,
local tests, documentation updates, hygiene scans and diff review.

## Goal

TASK-018 adds local public-safe documentation consistency and link sanity checks
so tracked Markdown links, anchors and public repo-relative references fail
closed without crawling external links, touching runtime systems or reading
ignored local evidence.

## Source State

- TASK-017 completed and was merged/pushed to detected default branch `main` at
  `3216f2872ac5b6ad8640de4f7be027eb794c907c`.
- Before TASK-018 branch creation, `main` and `origin/main` were verified
  aligned at `29b299c79f78377666d6c130c91162448e4e5b1b`, newer than the
  TASK-017 handoff baseline.
- Planner selected TASK-018 from `docs/tasks/backlog.md`; Security/Prod-safety
  approved the selection only for a static public-docs/link-sanity scope.

## Scope

- Add TASK-018 source-of-truth task spec.
- Add a public-safe local Markdown link and repo-relative reference checker.
- Cover valid links, missing files, missing anchors, duplicate heading anchors,
  unsafe absolute/traversal paths, forbidden local/raw Markdown link targets and
  external-link non-crawling with focused tests.
- Update README/automation docs and source-of-truth state.

## Allowed files

- `automation/quality/docs_consistency_link_sanity.py`
- `tests/test_docs_consistency_link_sanity.py`
- `tasks/TASK_018_docs_consistency_link_sanity_checks.md`
- `docs/qa/docs-consistency-link-sanity.md`
- `automation/README.md`
- `README.md`
- `docs/context/current-state.md`
- `docs/context/handoff/active-run.md`
- `docs/context/governance/risk-register.md`
- `docs/context/engineering/quality-gates.md`
- `docs/context/engineering/verification-memory.md`
- `docs/tasks/backlog.md`

## Out Of Scope

- ADB, Android runtime, APK read/install/launch or APK inspection.
- WebView/browser/payment/stream/WebRTC/network/offline execution.
- Reading, listing, parsing, copying or deriving from ignored `.qa_local/` raw
  evidence, local APKs, local secrets, raw QR artifacts or private endpoint
  inventories.
- External link crawling, redirect following, DNS probing or HTTP requests.
- Broad policy rewrites or runtime/product behavior claims.

## Forbidden files/actions

- Reading ignored `.qa_local/` raw evidence, APKs, screenshots, logs, XML,
  videos, QR decode artifacts or local secret files.
- ADB/device interaction, APK handling, runtime navigation, WebView/WebRTC,
  payment, network/offline execution or production interaction.
- External internet link validation.
- Scanner output that prints raw forbidden targets or private-looking values.
- Destructive git operations or default-branch integration before gates pass.

## Acceptance criteria

- TASK-018 has a source-of-truth task spec.
- The checker scans tracked Markdown files by default and does not traverse
  ignored `.qa_local` or raw artifact directories.
- External links are never fetched or crawled.
- The checker fails closed on missing public targets, missing local Markdown
  anchors, unsafe absolute/traversal paths and Markdown links to forbidden
  local/raw/package/secret-like targets.
- Checker output reports rule id, source path, line and sanitized/category-level
  target information without echoing raw forbidden targets.
- Tests cover the behavior above.
- Source-of-truth docs state that TASK-018 does not approve runtime, APK, ADB,
  WebView, WebRTC, payment, network/offline or raw evidence work.

## Multi-Agent Status

- Orchestrator: `in_progress`.
- Planner: `complete; selected TASK-018`.
- Security/Prod-safety pre-implementation review: `approved_with_boundaries`.
- Builder: `complete; implementation staged for review`.
- QA Reviewer A: `approved_after_url_query_sanitization_and_reference_style_remediation`.
- QA Reviewer B: `approved_after_final_recheck`.
- Security/Prod-safety final review: `approved_after_final_recheck`.
- Docs/Scribe: `approved_after_final_recheck`.

## Process Anomalies

- During initial task reconnaissance, a broad filename-only PowerShell search
  listed ignored `.qa_local` paths by name while looking for TASK-018-related
  files. No ignored local evidence contents were read, parsed, copied or used.
  TASK-018 implementation and verification are constrained to git-tracked files
  or explicit test fixtures only.

## Deliverables

- `automation/quality/docs_consistency_link_sanity.py`
- `tests/test_docs_consistency_link_sanity.py`
- `tasks/TASK_018_docs_consistency_link_sanity_checks.md`
- `docs/qa/docs-consistency-link-sanity.md`
- source-of-truth doc updates

## Verification Plan

```bash
git status --short --branch
git diff --check
python -m pytest -q tests/test_docs_consistency_link_sanity.py
python -m pytest -q tests/test_public_repo_safety_scan.py tests/test_full_tree_hygiene_scan.py tests/test_synthetic_redaction_corpus.py
python -m pytest -q
python -m compileall -q automation tests
python automation/quality/docs_consistency_link_sanity.py
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
```

## Verification Results

- `python -m pytest -q tests/test_docs_consistency_link_sanity.py`: `6 passed`
  after inline-reference parser remediation; `8 passed` after final reviewer
  URL/query target-output sanitization and reference-style link definition
  remediation.
- `python automation/quality/docs_consistency_link_sanity.py`: `pass`,
  `scanned_files=166`, `findings=0` after inline-reference parser remediation.
- Staged `git diff --check` and `git diff --cached --check`: `pass`.
- Staged `python automation/quality/docs_consistency_link_sanity.py`: `pass`,
  `scanned_files=170`, `findings=0`.
- `python -m pytest -q tests/test_docs_consistency_link_sanity.py tests/test_public_repo_safety_scan.py tests/test_full_tree_hygiene_scan.py tests/test_synthetic_redaction_corpus.py`: `75 passed`; `77 passed` after final reviewer URL/query target-output sanitization and reference-style link definition remediation.
- `python -m compileall -q automation tests`: `pass`.
- Final reviewer post-remediation `python -m compileall -q automation tests`:
  `pass`.
- `python automation/quality/full_tree_hygiene_scan.py`: `pass`.
- `python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree`: `pass`.
- `python automation/quality/public_repo_safety_scan.py`: `pass`,
  `scanned_files=170`, `findings=0`.
- Final full `python -m pytest -q`: `522 passed, 1 skipped`.

## Review Results

- Planner: selected TASK-018 because it is the only unfinished proposed P4
  public-safe task, is locally verifiable and reduces source-of-truth drift risk.
- Security/Prod-safety precheck: approved only with tracked/public-safe file
  scanning, no `.qa_local` traversal, no runtime/APK/ADB/network/external-link
  execution and sanitized findings.
- QA Reviewer A: initially blocked on raw query/URL-like target echo and
  reference-style link definition coverage; approved after remediation.
- QA Reviewer B: initially blocked on staged-vs-working-tree drift and stale
  raw-target remediation; approved after the staged state was aligned and final
  verification counts were recorded.
- Security/Prod-safety final review: approved the final staged state after
  confirming no `.qa_local` traversal/read, APK/ADB/runtime, external crawling,
  raw forbidden target echo or destructive command.
- Docs/Scribe: approved after confirming source-of-truth consistency, process
  anomaly recording, final counts and no stale TASK-017 active-run state.

## Thread Handoff

- Current thread status: `active`.
- Next thread created: `no; TASK-018 still in progress`.
- Next task selection must happen only after TASK-018 is verified,
  reviewed, merged/pushed to detected default branch and this thread is marked
  inactive.

## Stop Conditions

Stop if the task requires real/local raw evidence inspection, APK handling,
ADB/device/app runtime execution, private endpoints, real accounts, real
payments, real phone/OTP/device/QR values, production interaction, external
link crawling or scanner behavior that would print raw forbidden values into
public logs.
