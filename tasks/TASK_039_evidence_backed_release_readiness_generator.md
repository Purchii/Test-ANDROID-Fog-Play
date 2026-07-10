# TASK-039 - Evidence-backed release-readiness generator

## Mode

`BOUNDED_AUTONOMOUS`

## Production safety classification

`PROD_SAFE_OFFLINE_STATIC_ONLY`

## Audit backlog item

`QA-P0-02` - Evidence-backed release-readiness generator.

## Goal

Generate a public-safe release-readiness report from the TASK-038
`report-manifest-v1` authority layer. A release pass is allowed only when
required R0/R1 gates are backed by authoritative `evidence-report-envelope-v2`
records with confirmed evidence, reviewer approval, valid artifact hashes and
confirmed evidence storage plus cleanup/rollback prerequisites.

## Scope

- Validate `docs/qa/reports/report-manifest.json` before release evaluation.
- Reject absolute, alternate and non-Git-tracked manifest paths before reading
  their content; production CLI and importable APIs expose no bypass.
- Add a manifest-backed generator at
  `automation/reporting/generate_release_readiness_report.py`.
- Generate `docs/qa/reports/task039_release_readiness.summary.json`.
- Keep the current repository release readiness `blocked` while reports remain
  legacy migration blockers or lack authoritative v2 gate evidence.
- Add adversarial tests for legacy-only manifests, missing/stale manifests,
  manifest/source mismatch, internal artifact drift, missing provenance SHA,
  missing reviewer approval, non-confirmed evidence, incomplete PASS reports,
  pre-read path/index bypasses and self-asserted pass attempts.
- Regenerate `docs/qa/reports/report-manifest.json` so TASK-039 is indexed.

## Out of scope

- Migrating all legacy reports to v2.
- Rewriting archive docs checks or export scanners.
- CI/toolchain locking.
- ADB, Android runtime, APK read/hash/install/launch, device IP access,
  WebView/payment, stream/session, live API/backend/network actions.
- Reading ignored `.qa_local` raw evidence or publishing private/raw values.

## Acceptance criteria

- TASK-039 branch starts from integrated `main@0770840`.
- Release readiness is derived from the manifest and v2 source reports, not
  free-form metadata.
- Legacy-only manifest output is `blocked` and exits non-zero by default.
- Explicit `--allow-blocked` may emit a structurally valid blocked report only
  when manifest/source/artifact input integrity passes; malformed, missing,
  stale or mismatched input remains non-zero.
- A synthetic all-gates authoritative v2 manifest can pass only when required
  reviewer and evidence-storage/cleanup prerequisites are confirmed.
- Public output contains aliases, counts, status values, public repo-relative
  references and blocker categories only.
- TASK-039 report validates through the TASK-038 manifest tooling without
  circular SHA dependency on `report-manifest.json`.

## Verification

```text
git status --short --branch
git diff --check
python automation/reporting/generate_release_readiness_report.py --manifest docs/qa/reports/report-manifest.json --output docs/qa/reports/task039_release_readiness.summary.json --allow-blocked
python automation/reporting/generate_report_manifest.py --output docs/qa/reports/report-manifest.json
python automation/reporting/generate_report_manifest.py --validate-only --manifest docs/qa/reports/report-manifest.json
python -m unittest -q tests.test_release_readiness_report tests.test_report_manifest tests.test_release_gate_report
python -m compileall -q automation tests
python automation/quality/full_tree_hygiene_scan.py
python automation/quality/full_tree_hygiene_scan.py --mode public-safe-tree
python automation/quality/public_repo_safety_scan.py
python automation/quality/docs_consistency_link_sanity.py
```
