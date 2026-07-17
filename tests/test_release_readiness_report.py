import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation.reporting.generate_report_manifest import ENVELOPE_SCHEMA_VERSION, _sha256, build_manifest
from automation.reporting.generate_release_gate_report import DEFAULT_RELEASE_GATES
from automation.reporting.generate_release_readiness_report import build_report, main, validate_report
from automation.quality.official_export_index import INDEX_NAME, ExportEntry, _index_bytes, _sha256_bytes


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_official_index(root: Path) -> None:
    entries = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file() and candidate.name != INDEX_NAME):
        content = path.read_bytes()
        entries.append(ExportEntry(path.relative_to(root).as_posix(), len(content), _sha256_bytes(content)))
    (root / INDEX_NAME).write_bytes(_index_bytes(entries))


def _sha(path: Path) -> str:
    return _sha256(path)


def _write_task_spec(root: Path) -> None:
    spec = root / "tasks" / "TASK_039_evidence_backed_release_readiness_generator.md"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text("# TASK-039\n", encoding="utf-8")


def _build_test_report(manifest_path: Path, root: Path) -> dict:
    expected = root / "docs" / "qa" / "reports" / "report-manifest.json"
    if manifest_path.resolve() != expected.resolve():
        raise AssertionError("synthetic manifest must use the canonical repository-relative path")
    with patch("automation.reporting.generate_release_readiness_report._manifest_is_git_tracked", return_value=True):
        return build_report(Path("docs/qa/reports/report-manifest.json"), repo_root=root)


def _v2_report(
    root: Path,
    *,
    task_id: str = "TASK-900",
    run_id: str = "run-public-001",
    gate_ids: list[str] | None = None,
    evidence_status: str = "confirmed",
    execution_status: str = "pass",
    coverage_status: str = "covered",
    release_effect: str = "candidate_evidence",
    review_status: str = "approved",
    prerequisites_confirmed: bool = True,
    blocked_reasons: list[str] | None = None,
    extra: dict | None = None,
) -> dict:
    artifact = root / "docs" / "qa" / "reports" / f"{run_id}.artifact.json"
    _write_json(artifact, {"artifact": run_id, "public_safe": True})
    prereq_status = "confirmed" if prerequisites_confirmed else "unknown"
    payload = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "schema_validation_status": "pass",
        "execution_status": execution_status,
        "coverage_status": coverage_status,
        "evidence_status": evidence_status,
        "release_effect": release_effect,
        "production_safety_classification": "PROD_SAFE_OFFLINE_STATIC_ONLY",
        "generated_at_utc": "2026-07-10T00:00:00Z",
        "task_id": task_id,
        "build_ref": {"alias": "build-public-001", "public_hash_prefix": "abcdef123456"},
        "target_alias": "target-public-001",
        "run_id": run_id,
        "artifacts": [
            {
                "reference": artifact.relative_to(root).as_posix(),
                "sha256": _sha(artifact),
                "kind": "public_safe_report_summary",
                "evidence_status": evidence_status,
            }
        ],
        "blocked_reasons": blocked_reasons or [],
        "unknowns": [],
        "risks": [],
        "verification": [{"name": "fixture", "status": "pass", "evidence_status": evidence_status}],
        "review": {
            "qa_reviewer_a": review_status,
            "qa_reviewer_b": review_status,
            "security_prod_safety_reviewer": review_status,
            "docs_scribe": review_status,
        },
        "provenance": {"source_task": task_id, "generator": "test_fixture"},
        "payload": {
            "release_gate_ids": gate_ids or [gate["id"] for gate in DEFAULT_RELEASE_GATES],
            "release_prerequisites": {
                "evidence_storage": {"present": prerequisites_confirmed, "evidence_status": prereq_status},
                "cleanup_rollback": {"present": prerequisites_confirmed, "evidence_status": prereq_status},
            },
        },
    }
    if extra:
        payload.update(extra)
    return payload


class ReleaseReadinessReportTests(unittest.TestCase):
    def test_current_manifest_without_external_v2_gate_evidence_blocks_release(self) -> None:
        report = build_report(generated_at_utc="2026-07-10T00:00:00Z")

        self.assertEqual(validate_report(report), [])
        self.assertEqual(report["task_id"], "TASK-039")
        self.assertEqual(report["execution_status"], "blocked")
        self.assertEqual(report["payload"]["readiness_decision"], "blocked")
        self.assertIn("authoritative_v2_gate_evidence_records_missing", report["blocked_reasons"])
        self.assertGreater(report["payload"]["manifest_record_count"], 0)

    def test_missing_manifest_blocks_and_is_structurally_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            report = _build_test_report(root / "docs" / "qa" / "reports" / "report-manifest.json", root)

            self.assertEqual(validate_report(report), [])
            self.assertEqual(report["execution_status"], "blocked")
            self.assertIn("manifest_missing", report["blocked_reasons"])

    def test_untracked_manifest_path_is_rejected_before_content_loading(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            untracked = root / ".qa_local" / "raw-manifest.json"
            untracked.parent.mkdir(parents=True, exist_ok=True)
            untracked.write_text("not-json-and-must-not-be-read", encoding="utf-8")

            report = build_report(untracked, repo_root=root)

            self.assertEqual(report["payload"]["input_integrity_status"], "blocked")
            self.assertIn("manifest_path_not_allowed", report["blocked_reasons"])
            self.assertNotIn("manifest_malformed_json", report["blocked_reasons"])
            self.assertEqual(report["payload"]["manifest_reference"], "rejected_manifest_reference")

    def test_absolute_canonical_manifest_path_is_rejected_before_read(self) -> None:
        absolute_manifest = Path("docs/qa/reports/report-manifest.json").resolve()
        with patch(
            "automation.reporting.generate_release_readiness_report._load_json_object",
            side_effect=AssertionError("manifest content read must not occur"),
        ) as loader:
            report = build_report(absolute_manifest)

        loader.assert_not_called()
        self.assertIn("manifest_path_not_allowed", report["blocked_reasons"])

    def test_untracked_canonical_manifest_is_rejected_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, {"must_not_be_read": True})
            with patch(
                "automation.reporting.generate_release_readiness_report._load_json_object",
                side_effect=AssertionError("manifest content read must not occur"),
            ) as loader:
                report = build_report(Path("docs/qa/reports/report-manifest.json"), repo_root=root)

            loader.assert_not_called()
            self.assertIn("manifest_not_git_tracked", report["blocked_reasons"])

    def test_no_git_valid_official_index_authorizes_canonical_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            legacy = root / "docs" / "qa" / "reports" / "legacy.summary.json"
            _write_json(legacy, {"schema_version": "task900-legacy-v1", "task_id": "TASK-900"})
            manifest = build_manifest([legacy], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)
            _write_official_index(root)

            report = build_report(Path("docs/qa/reports/report-manifest.json"), repo_root=root)

            self.assertNotIn("manifest_not_git_tracked", report["blocked_reasons"])
            self.assertEqual(report["payload"]["manifest_reference"], "docs/qa/reports/report-manifest.json")

    def test_no_git_stale_official_index_blocks_manifest_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, {"schema_version": "report-manifest-v1", "records": []})
            _write_official_index(root)
            _write_json(manifest_path, {"changed": True})

            report = build_report(Path("docs/qa/reports/report-manifest.json"), repo_root=root)

            self.assertIn("manifest_not_git_tracked", report["blocked_reasons"])
            self.assertEqual(report["payload"]["manifest_reference"], "rejected_manifest_reference")

    def test_legacy_report_with_self_asserted_pass_cannot_satisfy_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            legacy = root / "docs" / "qa" / "reports" / "legacy.summary.json"
            _write_json(
                legacy,
                {
                    "schema_version": "task900-legacy-v1",
                    "task_id": "TASK-900",
                    "overall_status": "pass",
                    "evidence_status": "confirmed",
                    "release_decision": "pass",
                },
            )
            manifest = build_manifest([legacy], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)

            report = _build_test_report(manifest_path, root)

            self.assertEqual(report["payload"]["readiness_decision"], "blocked")
            self.assertIn("authoritative_v2_evidence_records_missing", report["blocked_reasons"])
            self.assertTrue(
                any(
                    "no_authoritative_v2_evidence" in reason
                    for gate in report["payload"]["release_gates"]
                    for reason in gate["blocked_reasons"]
                )
            )

    def test_one_authoritative_v2_record_satisfies_only_mapped_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            source = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(source, _v2_report(root, gate_ids=["RG-001"]))
            manifest = build_manifest([source], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)

            report = _build_test_report(manifest_path, root)
            gates = {gate["id"]: gate for gate in report["payload"]["release_gates"]}

            self.assertEqual(gates["RG-001"]["decision"], "pass")
            self.assertEqual(gates["RG-002"]["decision"], "blocked")
            self.assertEqual(report["payload"]["readiness_decision"], "blocked")

    def test_full_synthetic_v2_gate_set_can_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            source = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(source, _v2_report(root))
            manifest = build_manifest([source], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)

            report = _build_test_report(manifest_path, root)

            self.assertEqual(validate_report(report), [])
            self.assertEqual(report["payload"]["readiness_decision"], "pass")
            self.assertEqual(report["execution_status"], "pass")
            self.assertEqual(report["blocked_reasons"], [])

    def test_pending_review_blocks_otherwise_passing_v2(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            source = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(source, _v2_report(root, review_status="pending"))
            manifest = build_manifest([source], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)

            report = _build_test_report(manifest_path, root)

            self.assertEqual(report["payload"]["readiness_decision"], "blocked")
            self.assertTrue(any("qa_reviewer_a_not_approved" in reason for reason in report["blocked_reasons"]))

    def test_unknown_evidence_and_blocks_release_do_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            source = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(source, _v2_report(root, evidence_status="unknown", release_effect="blocks_release"))
            manifest = build_manifest([source], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)

            report = _build_test_report(manifest_path, root)

            self.assertEqual(report["payload"]["readiness_decision"], "blocked")
            self.assertIn("authoritative_v2_evidence_records_missing", report["blocked_reasons"])

    def test_raw_private_like_v2_source_blocks_and_is_not_republished(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            source = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(source, _v2_report(root, extra={"payload": {"private_hint": "token=synthetic-secret-like"}}))
            manifest = build_manifest([source], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)

            report = _build_test_report(manifest_path, root)
            encoded = json.dumps(report)

            self.assertEqual(report["payload"]["readiness_decision"], "blocked")
            self.assertNotIn("synthetic-secret-like", encoded)
            self.assertTrue(any("authoritative_v2_gate_evidence_records_missing" in reason for reason in report["blocked_reasons"]))

    def test_manifest_record_cannot_override_blocked_source_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            source = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(
                source,
                _v2_report(
                    root,
                    execution_status="blocked",
                    coverage_status="blocked",
                    evidence_status="unknown",
                    release_effect="blocks_release",
                    blocked_reasons=["synthetic_blocker"],
                ),
            )
            manifest = build_manifest([source], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            record = manifest["records"][0]
            record["execution_status"] = "pass"
            record["coverage_status"] = "covered"
            record["evidence_status"] = "confirmed"
            record["release_effect"] = "candidate_evidence"
            record["artifacts"][0]["evidence_status"] = "confirmed"
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)

            report = _build_test_report(manifest_path, root)

            self.assertEqual(report["payload"]["readiness_decision"], "blocked")
            self.assertEqual(report["payload"]["input_integrity_status"], "blocked")
            self.assertTrue(any("manifest_source_field_mismatch" in reason for reason in report["blocked_reasons"]))

    def test_missing_source_sha256_is_an_input_integrity_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            source = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(source, _v2_report(root))
            manifest = build_manifest([source], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            del manifest["records"][0]["provenance"]["source_sha256"]
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)

            report = _build_test_report(manifest_path, root)

            self.assertEqual(report["payload"]["input_integrity_status"], "blocked")
            self.assertTrue(any("source_sha256_missing_or_invalid" in reason for reason in report["blocked_reasons"]))

    def test_internal_artifact_drift_after_manifest_generation_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            source = root / "docs" / "qa" / "reports" / "v2.summary.json"
            source_payload = _v2_report(root)
            _write_json(source, source_payload)
            manifest = build_manifest([source], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)
            artifact = root / source_payload["artifacts"][0]["reference"]
            _write_json(artifact, {"artifact": "changed-after-manifest", "public_safe": True})

            report = _build_test_report(manifest_path, root)

            self.assertEqual(report["payload"]["input_integrity_status"], "blocked")
            self.assertTrue(any("source_v2_artifact_sha256_mismatch" in reason for reason in report["blocked_reasons"]))

    def test_validator_rejects_incomplete_or_incoherent_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_task_spec(root)
            source = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(source, _v2_report(root))
            manifest = build_manifest([source], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            manifest_path = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(manifest_path, manifest)
            report = _build_test_report(manifest_path, root)

            incomplete = copy.deepcopy(report)
            incomplete["payload"]["release_gates"] = []
            incoherent = copy.deepcopy(report)
            incoherent["coverage_status"] = "blocked"

            self.assertIn("release_gates_must_match_required_set", validate_report(incomplete))
            self.assertIn("pass_readiness_requires_covered_status", validate_report(incoherent))

    def test_cli_returns_nonzero_for_blocked_unless_allowed(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            blocked_exit = main(["--manifest", "docs/qa/reports/report-manifest.json"])
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "readiness.json"
            allowed_exit = main(
                [
                    "--manifest",
                    "docs/qa/reports/report-manifest.json",
                    "--output",
                    str(output),
                    "--allow-blocked",
                ]
            )

            self.assertEqual(blocked_exit, 1)
            self.assertEqual(allowed_exit, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["payload"]["readiness_decision"], "blocked")

        with tempfile.TemporaryDirectory() as temp_dir:
            with contextlib.redirect_stdout(io.StringIO()):
                missing_exit = main(
                    [
                        "--manifest",
                        str(Path(temp_dir) / "missing.json"),
                        "--allow-blocked",
                    ]
                )
            self.assertEqual(missing_exit, 1)


if __name__ == "__main__":
    unittest.main()
