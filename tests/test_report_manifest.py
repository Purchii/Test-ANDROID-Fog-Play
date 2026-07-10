import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation.reporting.generate_report_manifest import (
    ENVELOPE_SCHEMA_VERSION,
    build_manifest,
    main,
    validate_manifest,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _legacy_report(task_id: str = "TASK-900", schema_version: str = "task900-legacy-v1") -> dict:
    return {
        "schema_version": schema_version,
        "task_id": task_id,
        "overall_status": "pass",
        "evidence_status": "likely",
        "production_safety_classification": "PROD_SAFE",
    }


def _v2_report(
    repo_root: Path,
    *,
    task_id: str = "TASK-900",
    build_alias: str = "build-public-001",
    target_alias: str = "target-public-001",
    run_id: str = "run-public-001",
    generated_at_utc: str = "2026-07-10T00:00:00Z",
    evidence_status: str = "confirmed",
    execution_status: str = "pass",
    extra: dict | None = None,
) -> dict:
    artifact = repo_root / "docs" / "qa" / "reports" / f"{run_id}.artifact.json"
    _write_json(artifact, {"artifact": run_id, "public_safe": True})
    payload = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "schema_validation_status": "pass",
        "execution_status": execution_status,
        "coverage_status": "covered",
        "evidence_status": evidence_status,
        "release_effect": "candidate_evidence",
        "production_safety_classification": "PROD_SAFE_OFFLINE_STATIC_ONLY",
        "generated_at_utc": generated_at_utc,
        "task_id": task_id,
        "build_ref": {"alias": build_alias, "public_hash_prefix": "abcdef123456"},
        "target_alias": target_alias,
        "run_id": run_id,
        "artifacts": [
            {
                "reference": artifact.relative_to(repo_root).as_posix(),
                "sha256": _sha(artifact),
                "kind": "public_safe_report_summary",
                "evidence_status": evidence_status,
            }
        ],
        "blocked_reasons": [],
        "unknowns": [],
        "risks": [],
        "verification": [
            {
                "name": "synthetic_v2_fixture",
                "status": "pass",
                "evidence_status": evidence_status,
            }
        ],
        "review": {"qa": "approved", "security": "approved"},
        "provenance": {
            "source_task": task_id,
            "generator": "test_fixture",
            "supersedes": [],
        },
    }
    if extra:
        payload.update(extra)
    return payload


class ReportManifestTests(unittest.TestCase):
    def test_existing_public_safe_reports_are_v2_or_explicit_legacy(self) -> None:
        manifest = build_manifest(generated_at_utc="2026-07-10T00:00:00Z")

        self.assertEqual(validate_manifest(manifest), [])
        self.assertGreater(manifest["record_count"], 0)
        self.assertEqual(manifest["manifest_status"], "pass_with_legacy_migration_blockers")
        self.assertGreater(manifest["legacy_record_count"], 0)
        self.assertTrue(
            all(
                record["schema_validation_status"] in {"v2_valid", "legacy_migration_blocked"}
                for record in manifest["records"]
            )
        )
        self.assertTrue(
            all(
                record["blocked_reasons"] == ["legacy_report_not_evidence_envelope_v2"]
                for record in manifest["records"]
                if record["schema_validation_status"] == "legacy_migration_blocked"
            )
        )

    def test_duplicate_authority_blocks_ambiguous_latest_v2_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_a = root / "docs" / "qa" / "reports" / "a.summary.json"
            report_b = root / "docs" / "qa" / "reports" / "b.summary.json"
            payload = _v2_report(root)
            _write_json(report_a, payload)
            _write_json(report_b, payload)

            manifest = build_manifest(
                [report_a, report_b],
                repo_root=root,
                generated_at_utc="2026-07-10T00:00:00Z",
            )

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertTrue(
                any(reason.startswith("ambiguous_authoritative_records:") for reason in manifest["blocked_reasons"])
            )
            errors = validate_manifest(manifest, repo_root=root, enforce_tracked_index=False)
            self.assertTrue(any(reason.startswith("manifest_blocked:ambiguous_authoritative_records:") for reason in errors))
            self.assertTrue(all(record["authority_status"] == "blocked" for record in manifest["records"]))

    def test_missing_report_reference_blocks_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "legacy.summary.json"
            _write_json(report, _legacy_report())
            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            report.unlink()

            errors = validate_manifest(manifest, repo_root=root, enforce_tracked_index=False)

            self.assertIn("missing_artifact_reference:docs/qa/reports/legacy.summary.json", errors)

    def test_hash_mismatch_blocks_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "legacy.summary.json"
            _write_json(report, _legacy_report())
            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            _write_json(report, _legacy_report(task_id="TASK-901"))

            errors = validate_manifest(manifest, repo_root=root, enforce_tracked_index=False)

            self.assertIn("artifact_sha256_mismatch:docs/qa/reports/legacy.summary.json", errors)

    def test_unknown_schema_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "unknown.summary.json"
            _write_json(report, {"schema_version": "surprise-schema-v9", "task_id": "TASK-900"})

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertEqual(manifest["unknown_schema_record_count"], 1)
            self.assertIn(
                "record_unknown_schema:TASK-900__unknown_build__unknown_target__unknown.summary__unknown.summary",
                validate_manifest(manifest, repo_root=root, enforce_tracked_index=False),
            )

    def test_zero_reports_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = build_manifest([], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn("manifest_records_empty", manifest["blocked_reasons"])
            self.assertIn("manifest_records_empty", validate_manifest(manifest, repo_root=root, enforce_tracked_index=False))

    def test_legacy_reports_are_explicit_migration_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "legacy.summary.json"
            _write_json(report, _legacy_report())

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "pass_with_legacy_migration_blockers")
            self.assertEqual(manifest["legacy_record_count"], 1)
            self.assertEqual(manifest["records"][0]["schema_validation_status"], "legacy_migration_blocked")
            self.assertIs(manifest["records"][0]["authoritative"], False)
            self.assertEqual(validate_manifest(manifest, repo_root=root, enforce_tracked_index=False), [])

    def test_legacy_raw_public_identity_fields_are_not_republished(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "legacy.summary.json"
            payload = _legacy_report()
            payload["build_ref"] = "C:/Users/example/private.apk"
            payload["target_alias"] = ".qa_local/raw-target"
            _write_json(report, payload)

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            encoded = json.dumps(manifest, sort_keys=True)

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn("unsafe_public_field:build_ref.alias:raw_private_like_text", manifest["records"][0]["blocked_reasons"])
            self.assertIn("unsafe_public_field:target_alias:raw_forbidden_path_family", manifest["records"][0]["blocked_reasons"])
            self.assertNotIn("C:/Users/example/private.apk", encoded)
            self.assertNotIn(".qa_local/raw-target", encoded)

    def test_legacy_raw_public_metadata_fields_are_not_republished(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "legacy.summary.json"
            payload = _legacy_report(schema_version="C:/Users/example/schema.json")
            payload["generated_at_utc"] = "https://private.example.com/generated"
            payload["production_safety_classification"] = "PROD_SAFE token=synthetic-secret-like-value"
            _write_json(report, payload)

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            encoded = json.dumps(manifest, sort_keys=True)

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn("unsafe_public_field:schema_version:raw_private_like_text", manifest["records"][0]["blocked_reasons"])
            self.assertIn("unsafe_public_field:generated_at_utc:raw_private_like_text", manifest["records"][0]["blocked_reasons"])
            self.assertIn(
                "unsafe_public_field:production_safety_classification:raw_private_like_text",
                manifest["records"][0]["blocked_reasons"],
            )
            self.assertNotIn("C:/Users/example/schema.json", encoded)
            self.assertNotIn("private.example.com", encoded)
            self.assertNotIn("synthetic-secret-like-value", encoded)

    def test_v2_pass_with_unknown_evidence_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(report, _v2_report(root, evidence_status="unknown"))

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn("v2_pass_requires_confirmed_evidence", manifest["records"][0]["blocked_reasons"])

    def test_v2_missing_internal_artifact_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "v2.summary.json"
            payload = _v2_report(root)
            reference = payload["artifacts"][0]["reference"]
            (root / reference).unlink()
            _write_json(report, payload)

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn(f"v2_artifact_reference_missing:{reference}", manifest["records"][0]["blocked_reasons"])
            self.assertFalse(manifest["records"][0]["authoritative"])

    def test_v2_internal_artifact_hash_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "v2.summary.json"
            payload = _v2_report(root)
            reference = payload["artifacts"][0]["reference"]
            _write_json(root / reference, {"artifact": "changed", "public_safe": True})
            _write_json(report, payload)

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn(f"v2_artifact_sha256_mismatch:{reference}", manifest["records"][0]["blocked_reasons"])
            self.assertFalse(manifest["records"][0]["authoritative"])

    def test_v2_unknown_top_level_and_raw_private_like_values_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(
                report,
                _v2_report(
                    root,
                    extra={
                        "live_api_status": "pass",
                        "payload": {"private_hint": "token=synthetic-secret-like-value"},
                    },
                ),
            )

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")
            reasons = manifest["records"][0]["blocked_reasons"]

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn("v2_unknown_top_level_fields:live_api_status", reasons)
            self.assertTrue(any("raw_private_like_text" in reason for reason in reasons))

    def test_v2_payload_hidden_runtime_status_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(report, _v2_report(root, extra={"payload": {"runtime_execution_status": "pass"}}))

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn(
                "v2_$.payload.runtime_execution_status_hidden_runtime_or_live_status_key",
                manifest["records"][0]["blocked_reasons"],
            )

    def test_v2_payload_namespaced_runtime_status_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(report, _v2_report(root, extra={"payload": {"live_api": {"status": "pass"}}}))

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn(
                "v2_$.payload.live_api.status_hidden_runtime_or_live_status_key",
                manifest["records"][0]["blocked_reasons"],
            )

    def test_v2_payload_forbidden_raw_family_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "v2.summary.json"
            _write_json(
                report,
                _v2_report(root, extra={"payload": {"source_family": "qa_reverse_analysis/raw/example.json"}}),
            )

            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertTrue(any("raw_forbidden_path_family" in reason for reason in manifest["records"][0]["blocked_reasons"]))

    def test_validate_manifest_detects_stale_missing_tracked_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "legacy.summary.json"
            omitted = root / "docs" / "qa" / "reports" / "omitted.summary.json"
            _write_json(report, _legacy_report())
            _write_json(omitted, _legacy_report(task_id="TASK-901"))
            manifest = build_manifest([report], repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            with mock.patch(
                "automation.reporting.generate_report_manifest._tracked_report_paths",
                return_value=([report, omitted], "git_tracked", []),
            ):
                errors = validate_manifest(manifest, repo_root=root)

            self.assertIn("manifest_missing_tracked_reports:docs/qa/reports/omitted.summary.json", errors)

    def test_missing_git_tracked_index_fails_closed_for_default_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = build_manifest(repo_root=root, generated_at_utc="2026-07-10T00:00:00Z")

            self.assertEqual(manifest["manifest_status"], "blocked")
            self.assertIn("tracked_report_index_unavailable", manifest["blocked_reasons"])

    def test_cli_generates_and_validates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "docs" / "qa" / "reports" / "legacy.summary.json"
            output = root / "docs" / "qa" / "reports" / "report-manifest.json"
            _write_json(report, _legacy_report())

            original_cwd = Path.cwd()
            try:
                os.chdir(root)
                with mock.patch(
                    "automation.reporting.generate_report_manifest._tracked_report_paths",
                    return_value=([report], "git_tracked", []),
                ):
                    with contextlib.redirect_stdout(io.StringIO()) as first:
                        exit_code = main(["--output", str(output)])
                    generated = json.loads(output.read_text(encoding="utf-8"))
                    first_stdout = json.loads(first.getvalue())
                    with contextlib.redirect_stdout(io.StringIO()) as second:
                        validate_exit_code = main(["--validate-only", "--manifest", str(output)])
                    second_stdout = json.loads(second.getvalue())
            finally:
                os.chdir(original_cwd)

            self.assertEqual(exit_code, 0)
            self.assertEqual(validate_exit_code, 0)
            self.assertEqual(first_stdout["validation_status"], "pass")
            self.assertEqual(second_stdout["validation_status"], "pass")
            self.assertEqual(generated["record_count"], 1)


if __name__ == "__main__":
    unittest.main()
