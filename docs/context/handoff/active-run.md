# Active run

## Run Metadata

Mode: `BOUNDED_AUTONOMOUS`
Thread title: `TASK-017 - Synthetic redaction policy test corpus`
Thread status: `inactive_completed`
Fresh thread verified: `yes; continuation thread 019f28f3-79f6-7870-abd8-4a4c1de89004 accepted and renamed`
Task ID: `TASK-017`
Task branch: `qa/task-017-redaction-policy-test-corpus`
Default branch: `main`
Base commit: `bb49791c32dd400a9d2b43ee463571220b95d03b`
Merge/push authority: `BOUNDED_AUTONOMOUS after all gates pass; no force-push`
Production safety classification: `PROD_SAFE` for synthetic corpus files, local tests, static validation, docs, hygiene scans and diff review.

## Goal

TASK-017 creates a public-safe synthetic redaction policy test corpus and local
checks so report validators/redactors can be exercised against fabricated
sensitive-looking values without using real secrets, private endpoints, raw
evidence, APKs, device data or runtime captures.

## Source State

- TASK-014 completed and was merged/pushed to detected default branch `main` at
  `67bd47995551b2ba17e04c522647f1ac2e6dd279`.
- Before TASK-017 selection, `main` and `origin/main` were verified aligned at
  `bb49791c32dd400a9d2b43ee463571220b95d03b`, newer than the TASK-014 handoff
  baseline.
- Planner selected TASK-017 from `docs/tasks/backlog.md`; Security/Prod-safety
  approved the selection only for a tightly scoped synthetic-only corpus.

## Scope

- Add TASK-017 source-of-truth task spec.
- Add a public-safe synthetic redaction corpus using fabricated values only.
- Cover credential-like, token-like, URL/endpoint-like, route/deeplink-like,
  local/APK path-like, hash-like, device identifier-like, phone/OTP-like,
  payment/account-like, QR payload-like and raw evidence reference-like classes.
- Add local tests proving relevant validators/redactors reject, flag or redact
  the synthetic cases without printing raw specimens in command output.
- Harden the TASK-008 WebView/payment redactor for synthetic account-id style
  values found by QA A review.
- Update source-of-truth docs, quality gates, risk register and verification
  memory.

## Allowed files

- `automation/quality/synthetic_redaction_corpus.py`
- `automation/webview_payment_safe_runner/generate_webview_payment_safe_report.py`
- `tests/test_synthetic_redaction_corpus.py`
- `tasks/TASK_017_synthetic_redaction_policy_test_corpus.md`
- `docs/qa/synthetic-redaction-policy-test-corpus.md`
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
- Reading or traversing ignored `.qa_local/` raw evidence.
- Real secrets, credentials, device identifiers, phone/OTP values, QR targets,
  private endpoints, routes, account data or payment data.
- Publishing raw specimen values in scanner/validator command output.

## Forbidden files/actions

- Reading, listing, copying or deriving corpus values from ignored `.qa_local/`
  raw evidence, APKs, screenshots, logs, XML, videos or QR decode artifacts.
- ADB/device interaction, APK read/install/launch, runtime navigation,
  WebView/WebRTC/payment/network/offline execution or production interaction.
- Real secrets, endpoints, QR targets, phone/OTP values, device identifiers,
  account data or payment data in code, tests, docs or command output.
- Scanner, validator or CLI output that prints raw matched specimen values
  instead of case ids/categories.

## Acceptance criteria

- Every corpus entry is explicitly synthetic and public-safe.
- The corpus covers credential-like, token-like, URL/endpoint-like,
  route/deeplink-like, local/APK path-like, hash-like, device identifier-like,
  phone/OTP-like, payment/account-like, QR payload-like and raw evidence
  reference-like classes.
- Tests prove TASK-020/TASK-024 public report validators reject covered
  synthetic values without echoing raw specimens.
- Tests prove release gate and WebView/payment generated reports redact covered
  synthetic values without preserving raw specimens.
- TASK-014 public repository safety scan and full-tree hygiene checks pass.
- Docs state that TASK-017 does not approve or execute runtime, APK, WebView,
  WebRTC, payment, network or local raw evidence work.


## Multi-Agent Status

- Orchestrator: `complete`.
- Planner: `complete; selected TASK-017`.
- Builder: `complete; added synthetic corpus and tests within assigned ownership`.
- QA Reviewer A: `approved_after_webview_payment_redaction_remediation`.
- QA Reviewer B: `approved_after_final_recheck`.
- Security/Prod-safety Reviewer: `approved_after_final_recheck`.
- Docs/Scribe: `approved_after_final_recheck`.

## Deliverables

- `tasks/TASK_017_synthetic_redaction_policy_test_corpus.md`
- `docs/qa/synthetic-redaction-policy-test-corpus.md`
- `automation/quality/synthetic_redaction_corpus.py`
- `tests/test_synthetic_redaction_corpus.py`
- source-of-truth doc updates

## Verification Plan

```bash
git status --short --branch
git diff --check
python -m pytest -q tests/test_synthetic_redaction_corpus.py tests/test_post_auth_navigation_report_validator.py tests/test_native_regression_report_validator.py tests/test_release_gate_report.py tests/test_webview_payment_safe_runner.py
python -m pytest -q
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
```

## Verification Results

- `python -m pytest -q tests/test_synthetic_redaction_corpus.py`: `46 passed` before QA A remediation; `55 passed` after QA A remediation.
- `python -m pytest -q tests/test_synthetic_redaction_corpus.py tests/test_post_auth_navigation_report_validator.py tests/test_native_regression_report_validator.py tests/test_release_gate_report.py tests/test_webview_payment_safe_runner.py`: `92 passed` before QA A remediation; `101 passed` after QA A remediation and after account-id redaction remediation.
- `git diff --check`: `pass`.
- `python -m compileall -q automation tests`: `pass`.
- `python automation/quality/full_tree_hygiene_scan.py`: `pass`.
- `python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree`: `pass`.
- `python automation/quality/public_repo_safety_scan.py`: `pass`, `scanned_files=162`, `findings=0`.
- `python -m pytest -q`: `505 passed, 1 skipped` before QA A remediation; `514 passed, 1 skipped` after QA A remediation.
- Staged `git diff --cached --check`: `pass`.
- Staged-candidate `python automation/quality/public_repo_safety_scan.py`: `pass`, `scanned_files=166`, `findings=0`.
- Staged-candidate `python automation/quality/full_tree_hygiene_scan.py`: `pass`.

## Review Results

- Planner: selected TASK-017 because it reduces redaction/leak risks more
  directly than TASK-018 while remaining public-safe.
- Security/Prod-safety: approved only with synthetic-only safeguards and no
  `.qa_local`, APK, runtime, QR target, endpoint or raw evidence use.
- QA Reviewer A: `blocked_pending_recheck`; initial review required WebView/payment corpus coverage, explicit per-entry synthetic/public-safe markers and static validator coverage matrix. Remediation added all three. Re-review found WebView/payment account-id fragment leakage for `SRC-009`; remediation added account-id redaction and sensitive-fragment assertions. Verification was rerun.
- QA Reviewer B: `approved`.
- QA Reviewer A final re-review: `approved`.
- QA Reviewer B final re-review: `approved`.
- Security/Prod-safety final re-review: `approved`.
- Docs/Scribe final re-review: `approved`.

## Thread Handoff

- Current thread status: `inactive_completed`.
- Next thread created: `yes; 019f2915-4152-7ee2-b37c-21b892dcc845`.
- Next thread title/prompt seed: `NEXT_TASK_SELECTION_FROM_main@3216f28`.
- Next task selection must happen in the fresh continuation thread after it
  verifies current default branch state.

## Stop Conditions

Stop if the task requires real/local raw evidence inspection, APK handling,
ADB/device/app runtime execution, private endpoints, real accounts, real
payments, real phone/OTP/device/QR values, production interaction, or scanner
behavior that would print matched raw specimen values into public logs.
