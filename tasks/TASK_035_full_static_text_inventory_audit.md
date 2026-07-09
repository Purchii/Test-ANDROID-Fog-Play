# TASK-035 - Full static text inventory and coverage audit

## Mode

`BOUNDED_AUTONOMOUS`

## Production safety

`PROD_SAFE_LOCAL_STATIC_ONLY`

TASK-035 is an offline/static audit. It does not run Android runtime, ADB, APK
install/launch, live backend/API/network calls, WebView/payment/stream actions,
source-code inspection, APK patching, APK modification, decompilation, smali or
method-body analysis.

## Goal

Build a fail-closed static text inventory foundation for all static text data
available from the local sanitized reverse-analysis artifact, while keeping raw
text values local-only and publishing only counts, hash prefixes, categories,
coverage status and redaction classes.

## Source inputs

Allowed input:

- local ignored sanitized artifact:
  `qa_reverse_analysis/raw/apk_analysis_sanitized.json`;
- tracked public-safe reverse-analysis summaries;
- synthetic test fixtures created inside tests.

Forbidden input:

- application source code;
- decompiled code, smali or method bodies;
- APK patching/modification;
- live runtime/ADB/backend/API evidence;
- real secrets, accounts, payment data, private endpoints or device IDs.

## Deliverables

- `automation/static_text_inventory/build_task035_static_text_inventory.py`
- `tests/test_task035_static_text_inventory.py`
- `docs/qa/static-text/static-text-inventory-policy.md`
- `docs/qa/reports/task035_static_text_inventory.summary.json`
- ignored local raw-value inventory:
  `.qa_local/static_text_inventory/task035_available_static_text_inventory.local.jsonl`

## Acceptance criteria

- The public report records the source-reported likely static UI string count.
- Every raw string available in the sanitized sample list is inventoried
  locally with a stable ID, SHA-256 and redaction classification.
- Raw string values are not committed or printed in the public report.
- Public report contains only hash prefixes, counts, categories, redaction
  classes and status values.
- The report explicitly marks missing full raw value coverage when the
  available source has only a sample list.
- Runtime visibility, translation quality, accessibility behavior, backend/API
  behavior and Android runtime behavior remain `not_run` or `unknown`.
- Tests cover local-only raw inventory, public report redaction, runtime
  overclaim blocking and high-risk text-family classification.
- Security/Prod-safety and QA review approve the final claims.

## Current TASK-035 finding

The available local sanitized reverse-analysis artifact reports
`19187` likely UI/static strings but exposes only `160` raw sample values.
TASK-035 therefore inventories all available raw sample values and records the
remaining `19027` raw values as
`blocked_by_missing_full_static_text_values_source`.

This is a coverage finding, not product evidence. It means exact raw-value
coverage of every static text requires a future approved local-only full static
string export.

## Verification

Required checks:

```text
git status --short --branch
git diff --check
python automation/static_text_inventory/build_task035_static_text_inventory.py --source qa_reverse_analysis/raw/apk_analysis_sanitized.json --local-inventory .qa_local/static_text_inventory/task035_available_static_text_inventory.local.jsonl --report docs/qa/reports/task035_static_text_inventory.summary.json
python automation/static_text_inventory/build_task035_static_text_inventory.py --validate-only --report docs/qa/reports/task035_static_text_inventory.summary.json
python -m pytest -q tests/test_task035_static_text_inventory.py
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```
