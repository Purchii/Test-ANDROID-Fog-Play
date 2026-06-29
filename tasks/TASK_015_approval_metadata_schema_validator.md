# TASK-015 - Approval Metadata Schema Validator

Mode: `BOUNDED_AUTONOMOUS` for local fail-closed validation only.

Production safety classification: `PROD_SAFE`.

## Goal

Create public-safe approval metadata docs, examples, local validator and unit
tests so TASK-005 cannot start from ambiguous approval statements.

## In Scope

- Approval metadata example JSON with placeholders and aliases only.
- Approval policy, local path policy, device inventory template and synthetic
  QA user policy.
- Local validator at `automation/approvals/validate_approval_metadata.py`.
- Unit tests for hard blockers and success-with-not-run behavior.
- Regression safety fixes for release gate reviewer approvals and TASK-002
  evidence gating.
- README, pytest config and `.gitignore` hygiene.

## Out Of Scope

- APK execution, install, launch, decompilation, patching or resigning.
- Device, emulator, WebView, WebRTC, payment, network or live CI execution.
- Raw screenshots, logs, videos, packet captures or dumps.
- Raw phone, OTP, token, cookie, session, private endpoint or device identifier.

## Acceptance Criteria

- Pending example metadata validates as `blocked`.
- Fully confirmed synthetic metadata validates as
  `approved_for_limited_runtime` while runtime remains `not_run`.
- All required hard blockers have unit-test coverage.
- Release gates require QA A, QA B, Security/Prod-safety and Docs/Scribe
  approval or confirmation before a `pass` release decision.
- TASK-002 guard report blocks when any required prerequisite has
  `evidence_status != confirmed`.
- `pytest -q`, `python -m pytest -q`, `git diff --check` and compileall pass.

