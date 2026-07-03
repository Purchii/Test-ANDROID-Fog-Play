# TASK-014 - Public repository safety scan checklist and local guard plan

## Mode

`BOUNDED_AUTONOMOUS`

## Goal

Create a public-safe repository safety checklist and local guard for tracked
artifact paths so future branches fail before raw APKs, local-only evidence,
secrets, signing material or packaged reverse-analysis artifacts enter the
public source tree.

## Context

TASK-020 through TASK-024 added selected-lane runtime reports, inventories and
regression tooling. Raw evidence remains local-only under ignored `.qa_local/`
paths, while public reports use aliases, categories and redacted summaries.
TASK-014 reduces the remaining public-repository leak risk with a static guard
that complements the full-tree hygiene scan.

## Production Safety

- `PROD_SAFE`: docs, tracked-file path scanning, unit tests, compile checks and
  public-safe diff review.
- `PROD_CONDITIONAL`: scanning ignored local evidence is out of scope for this
  task and would require a separate approved redaction plan.
- `PROD_FORBIDDEN`: ADB/device/runtime execution, APK install or inspection,
  WebView/browser/payment/stream/network execution, secret extraction, endpoint
  extraction and raw evidence publication.

## Scope

- Add a local static guard for tracked public-repository path risks.
- Document the pre-commit/pre-merge safety checklist.
- Keep `.qa_local/...` path patterns in public docs as category-level local
  storage contracts, not as runtime evidence publication.
- Avoid broad content regexes that would false-fail synthetic redaction tests.
- Update source-of-truth docs and verification memory.

## Out Of Scope

- Reading ignored `.qa_local/` raw evidence.
- Inspecting APKs, APK hashes, screenshots, videos, XML dumps, logcat or QR
  targets.
- Runtime validation, app launch, ADB collection, network/offline probes,
  WebView, WebRTC, payment, account mutation or production interaction.
- Complete secret-detection replacement for dedicated secret-scanning tools.

## Acceptance Criteria

- `automation/quality/public_repo_safety_scan.py` fails closed on tracked
  forbidden path prefixes, raw artifact extensions, local config filenames and
  screenshot-like raw evidence names.
- The scanner reports only rule ids, paths and reasons, never matched file
  contents.
- Existing public-safe `.qa_local/...` path contracts and synthetic redaction
  tests remain allowed.
- `docs/qa/public-repository-safety-scan.md` records the manual checklist and
  local guard plan.
- Source-of-truth docs state that TASK-014 is static/public-safe and does not
  confirm runtime behavior.

## Verification Plan

```bash
git status --short --branch
git diff --check
python -m pytest -q tests/test_public_repo_safety_scan.py tests/test_full_tree_hygiene_scan.py
python -m pytest -q
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
```

Runtime/device/APK checks are not run in TASK-014 because they are out of
scope and would be `PROD_CONDITIONAL` or `PROD_FORBIDDEN` without separate
confirmed approvals.

## Stop Conditions

Stop if the task requires raw local evidence inspection, APK handling, ADB,
device/app runtime execution, private endpoints, real accounts, real payments,
secret values in output, or a scanner design that would print matched raw
content into public logs.
