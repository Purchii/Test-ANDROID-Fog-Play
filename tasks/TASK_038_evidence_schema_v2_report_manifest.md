# TASK-038 - Evidence schema v2 and authoritative report manifest

Mode: `BOUNDED_AUTONOMOUS`
Branch: `qa/task-038-evidence-schema-v2-report-manifest`
Production safety classification: `PROD_SAFE_OFFLINE_STATIC_ONLY`

## Scope

TASK-038 implements audit backlog item QA-P0-01 for findings F-004 and F-005:

- add a versioned public-safe evidence/report envelope v2 contract;
- add an authoritative report manifest generator/validator for tracked reports
  matching `docs/qa/reports/*.json`;
- generate `docs/qa/reports/report-manifest.json`;
- add focused adversarial tests for manifest authority and fail-closed
  migration behavior;
- update source-of-truth docs for the audit-chain handoff.

## Out Of Scope

- QA-P0-02 release generator rewrite;
- QA-P0-03 docs checker fix;
- QA-P0-04 archive/export scanner;
- CI lock/coverage follow-ups;
- Android runtime, ADB, APK read/hash/install/launch, device IP use,
  WebView/payment/stream/session actions, live API/backend/network calls;
- reading ignored `.qa_local` raw evidence or publishing private values.

## Acceptance Criteria

- `docs/qa/schemas/evidence-report-envelope-v2.schema.json` documents the v2
  envelope fields and status separation.
- `automation/reporting/generate_report_manifest.py` indexes only tracked
  public-safe JSON reports matching `docs/qa/reports/*.json`, computes SHA-256 values,
  records legacy migration blockers and fails closed for missing refs, hash
  drift, unknown schemas, duplicate authority, unsafe refs and v2 overclaims.
- `docs/qa/reports/report-manifest.json` exists and explicitly lists existing
  reports as `legacy_migration_blocked` until migrated to v2.
- Focused tests cover duplicate authority, missing ref, hash mismatch, unknown
  schema, zero records, legacy handling and v2 evidence/raw-value false-pass
  cases.
- Source-of-truth docs record the recovery lifecycle anomaly from the stalled
  same-directory first turn.

## Verification

Required checks are the focused manifest tests, manifest generator/validator,
diff checks, compileall and repository quality scans. `pytest` should be run if
available; when it is unavailable in the current Python environment, the
stdlib `unittest` TASK-038 focused gate is authoritative for the new tests and
the pytest blocker must be recorded.
