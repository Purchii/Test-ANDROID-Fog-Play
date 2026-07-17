"""Generate a manifest-backed public-safe release-readiness report.

TASK-039 is offline/static only. The generator consumes the TASK-038
report-manifest as the authority layer and refuses release pass decisions unless
R0/R1 gates are backed by authoritative evidence-report-envelope-v2 records.
It does not read ignored raw evidence, APKs, devices, network resources,
WebView/payment/session material or private endpoints.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from automation.reporting.generate_report_manifest import (
    ENVELOPE_SCHEMA_VERSION,
    _is_safe_reference,
    _raw_value_findings,
    _sha256,
    _validate_v2_envelope,
    validate_manifest,
)
from automation.reporting.generate_release_gate_report import DEFAULT_RELEASE_GATES, REQUIRED_REVIEWERS
from automation.quality.official_export_index import (
    INDEX_NAME as OFFICIAL_EXPORT_INDEX_NAME,
    ExportIndexError,
    validated_portable_paths,
)


TASK_ID = "TASK-039"
TOOL_NAME = "reporting.release_readiness_report_generator"
PROD_SAFE_CLASSIFICATION = "PROD_SAFE_OFFLINE_STATIC_ONLY"
DEFAULT_MANIFEST = Path("docs/qa/reports/report-manifest.json")
DEFAULT_OUTPUT = Path("docs/qa/reports/task039_release_readiness.summary.json")
DEFAULT_TASK_SPEC = Path("tasks/TASK_039_evidence_backed_release_readiness_generator.md")
BUILD_ALIAS = "public-safe-repo-main-0770840"
TARGET_ALIAS = "repo-public-safe"
RUN_ID = "task039-manifest-backed-release-readiness"
PASSING_REVIEW_STATUSES = {"approved", "confirmed"}
PASSABLE_COVERAGE_STATUSES = {"covered"}
PASSABLE_RELEASE_EFFECTS = {"candidate_evidence"}
REQUIRED_RELEASE_PREREQUISITES = ("evidence_storage", "cleanup_rollback")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json_object(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {}, ["manifest_missing"]
    except json.JSONDecodeError:
        return {}, ["manifest_malformed_json"]
    except OSError:
        return {}, ["manifest_unreadable"]
    if not isinstance(loaded, dict):
        return {}, ["manifest_not_object"]
    return loaded, []


def _manifest_is_git_tracked(repo_root: Path) -> bool:
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={repo_root.as_posix()}",
                "ls-files",
                "--error-unmatch",
                "--",
                DEFAULT_MANIFEST.as_posix(),
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=False,
        )
    except OSError:
        result = None
    if result is not None and result.returncode == 0:
        return True
    official_index = repo_root / OFFICIAL_EXPORT_INDEX_NAME
    if not official_index.is_file():
        return False
    try:
        governed_paths = validated_portable_paths(repo_root)
    except (ExportIndexError, OSError, RuntimeError, ValueError):
        return False
    return DEFAULT_MANIFEST in governed_paths


def _allowed_manifest_path(
    manifest_path: Path,
    repo_root: Path,
) -> tuple[Path | None, list[str]]:
    root = repo_root.resolve()
    expected_path = root / DEFAULT_MANIFEST
    if manifest_path.is_absolute():
        return None, ["manifest_path_not_allowed"]
    if not manifest_path.is_absolute() and manifest_path.as_posix() != DEFAULT_MANIFEST.as_posix():
        return None, ["manifest_path_not_allowed"]
    candidate_path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    expected = expected_path.resolve()
    candidate = candidate_path.resolve()
    if candidate_path.is_symlink() or not expected.is_relative_to(root) or candidate != expected:
        return None, ["manifest_path_not_allowed"]
    if not _manifest_is_git_tracked(root):
        return None, ["manifest_not_git_tracked"]
    return candidate, []


def _safe_reason(reason: Any, fallback: str = "blocked") -> str:
    if not isinstance(reason, str) or not reason.strip():
        return fallback
    findings = _raw_value_findings(reason)
    if findings:
        return "unsafe_reason_redacted"
    return reason.strip()


def _safe_reason_list(reasons: Any) -> list[str]:
    if not isinstance(reasons, list):
        return []
    return sorted({_safe_reason(reason) for reason in reasons})


def _source_reference(record: dict[str, Any]) -> str | None:
    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        return None
    reference = provenance.get("source_reference")
    if not isinstance(reference, str) or not _is_safe_reference(reference):
        return None
    return reference


def _load_authoritative_source(record: dict[str, Any], repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    reference = _source_reference(record)
    record_id = str(record.get("record_id", "unknown_record"))
    if reference is None:
        return {}, [f"{record_id}:source_reference_missing_or_unsafe"]

    source_path = repo_root / PurePosixPath(reference)
    if not source_path.is_file():
        return {}, [f"{record_id}:source_reference_missing"]

    expected_sha = record.get("provenance", {}).get("source_sha256")
    if not isinstance(expected_sha, str) or re.fullmatch(r"[a-f0-9]{64}", expected_sha) is None:
        return {}, [f"{record_id}:source_sha256_missing_or_invalid"]
    actual_sha = _sha256(source_path)
    if expected_sha != actual_sha:
        return {}, [f"{record_id}:source_sha256_mismatch"]

    source, errors = _load_json_object(source_path)
    if errors:
        return {}, [f"{record_id}:{error}" for error in errors]
    if source.get("schema_version") != ENVELOPE_SCHEMA_VERSION:
        return {}, [f"{record_id}:source_not_evidence_envelope_v2"]
    envelope_errors = _validate_v2_envelope(source, repo_root)
    if envelope_errors:
        return {}, [f"{record_id}:source_{error}" for error in envelope_errors]
    raw_findings = _raw_value_findings(source)
    if raw_findings:
        return {}, [f"{record_id}:source_contains_raw_or_private_like_values"]
    consistency_errors = _record_source_consistency_errors(record, source, reference, actual_sha)
    if consistency_errors:
        return {}, [f"{record_id}:{error}" for error in consistency_errors]
    return source, []


def _record_source_consistency_errors(
    record: dict[str, Any],
    source: dict[str, Any],
    reference: str,
    source_sha256: str,
) -> list[str]:
    errors: list[str] = []
    mirrored_fields = (
        "task_id",
        "target_alias",
        "run_id",
        "generated_at_utc",
        "schema_version",
        "execution_status",
        "coverage_status",
        "evidence_status",
        "release_effect",
        "production_safety_classification",
    )
    for field_name in mirrored_fields:
        if record.get(field_name) != source.get(field_name):
            errors.append(f"manifest_source_field_mismatch:{field_name}")

    record_build = record.get("build_ref") if isinstance(record.get("build_ref"), dict) else {}
    source_build = source.get("build_ref") if isinstance(source.get("build_ref"), dict) else {}
    if record_build.get("alias") != source_build.get("alias"):
        errors.append("manifest_source_field_mismatch:build_ref.alias")

    provenance = record.get("provenance") if isinstance(record.get("provenance"), dict) else {}
    if provenance.get("source_reference") != reference:
        errors.append("manifest_source_provenance_reference_mismatch")
    if provenance.get("source_sha256") != source_sha256:
        errors.append("manifest_source_provenance_sha256_mismatch")

    expected_artifact = {
        "reference": reference,
        "sha256": source_sha256,
        "kind": "public_safe_report_summary",
        "evidence_status": source.get("evidence_status"),
    }
    artifacts = record.get("artifacts")
    if not isinstance(artifacts, list) or expected_artifact not in artifacts:
        errors.append("manifest_source_artifact_binding_mismatch")
    return sorted(set(errors))


def _review_approved(source: dict[str, Any]) -> tuple[bool, list[str]]:
    raw_review = source.get("review")
    if not isinstance(raw_review, dict):
        return False, ["source_review_missing"]
    blockers = []
    for reviewer in REQUIRED_REVIEWERS:
        status = raw_review.get(reviewer)
        if not isinstance(status, str) or status.strip().lower() not in PASSING_REVIEW_STATUSES:
            blockers.append(f"{reviewer}_not_approved")
    return not blockers, blockers


def _release_prerequisites(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = source.get("payload")
    if not isinstance(payload, dict):
        return {}
    raw_prerequisites = payload.get("release_prerequisites")
    if not isinstance(raw_prerequisites, dict):
        return {}
    prerequisites: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_RELEASE_PREREQUISITES:
        raw_item = raw_prerequisites.get(name)
        if not isinstance(raw_item, dict):
            raw_item = {}
        prerequisites[name] = {
            "present": raw_item.get("present") is True,
            "evidence_status": raw_item.get("evidence_status") if isinstance(raw_item.get("evidence_status"), str) else "unknown",
        }
    return prerequisites


def _source_gate_ids(source: dict[str, Any]) -> set[str]:
    payload = source.get("payload")
    if not isinstance(payload, dict):
        return set()
    raw_gate_ids = payload.get("release_gate_ids")
    if not isinstance(raw_gate_ids, list):
        return set()
    return {gate_id for gate_id in raw_gate_ids if isinstance(gate_id, str)}


def _record_is_candidate(record: dict[str, Any], source: dict[str, Any]) -> tuple[bool, list[str]]:
    record_id = str(record.get("record_id", "unknown_record"))
    blockers = []
    if record.get("task_id") == TASK_ID:
        blockers.append(f"{record_id}:task039_readiness_report_cannot_satisfy_release_gate")
    if record.get("authoritative") is not True:
        blockers.append(f"{record_id}:record_not_authoritative")
    if record.get("authority_status") != "authoritative":
        blockers.append(f"{record_id}:record_authority_status_invalid")
    if record.get("schema_validation_status") != "v2_valid":
        blockers.append(f"{record_id}:record_not_v2_valid")
    if record.get("execution_status") != "pass":
        blockers.append(f"{record_id}:execution_not_pass")
    if record.get("coverage_status") not in PASSABLE_COVERAGE_STATUSES:
        blockers.append(f"{record_id}:coverage_not_passable")
    if record.get("evidence_status") != "confirmed":
        blockers.append(f"{record_id}:evidence_not_confirmed")
    if record.get("release_effect") not in PASSABLE_RELEASE_EFFECTS:
        blockers.append(f"{record_id}:release_effect_not_candidate_evidence")
    if record.get("blocked_reasons"):
        blockers.append(f"{record_id}:record_has_blockers")
    if source.get("execution_status") != "pass":
        blockers.append(f"{record_id}:source_execution_not_pass")
    if source.get("coverage_status") not in PASSABLE_COVERAGE_STATUSES:
        blockers.append(f"{record_id}:source_coverage_not_passable")
    if source.get("evidence_status") != "confirmed":
        blockers.append(f"{record_id}:source_evidence_not_confirmed")
    if source.get("release_effect") not in PASSABLE_RELEASE_EFFECTS:
        blockers.append(f"{record_id}:source_release_effect_not_candidate_evidence")
    if source.get("blocked_reasons"):
        blockers.append(f"{record_id}:source_has_blockers")
    if source.get("unknowns"):
        blockers.append(f"{record_id}:source_has_unknowns")
    artifacts = source.get("artifacts")
    if not isinstance(artifacts, list) or any(item.get("evidence_status") != "confirmed" for item in artifacts):
        blockers.append(f"{record_id}:source_artifacts_not_confirmed")
    verification = source.get("verification")
    if (
        not isinstance(verification, list)
        or not verification
        or any(
            not isinstance(item, dict)
            or item.get("status") != "pass"
            or item.get("evidence_status") != "confirmed"
            for item in verification
        )
    ):
        blockers.append(f"{record_id}:source_verification_not_confirmed")
    review_ok, review_blockers = _review_approved(source)
    if not review_ok:
        blockers.extend(f"{record_id}:{blocker}" for blocker in review_blockers)
    prerequisites = _release_prerequisites(source)
    for name in REQUIRED_RELEASE_PREREQUISITES:
        item = prerequisites.get(name, {})
        if item.get("present") is not True or item.get("evidence_status") != "confirmed":
            blockers.append(f"{record_id}:{name}_not_confirmed")
    return not blockers, blockers


def _evaluate_gate(gate_definition: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    supporting = []
    blockers = []
    for candidate in candidates:
        gate_ids = _source_gate_ids(candidate["source"])
        if gate_definition["id"] not in gate_ids:
            continue
        ok, candidate_blockers = _record_is_candidate(candidate["record"], candidate["source"])
        if ok:
            supporting.append(candidate["record"]["record_id"])
        else:
            blockers.extend(candidate_blockers)

    if supporting:
        decision = "pass"
        evidence_status = "confirmed"
        gate_blockers: list[str] = []
    else:
        decision = "blocked"
        evidence_status = "unknown"
        gate_blockers = blockers or [f"{gate_definition['id']}:no_authoritative_v2_evidence"]

    return {
        "id": gate_definition["id"],
        "name": gate_definition["name"],
        "risk_level": gate_definition["risk_level"],
        "runtime_dependent": gate_definition["runtime_dependent"],
        "decision": decision,
        "evidence_status": evidence_status,
        "source_record_ids": sorted(supporting),
        "blocked_reasons": sorted(set(_safe_reason(reason) for reason in gate_blockers)),
    }


def _artifact_for_report(repo_root: Path, reference: Path = DEFAULT_TASK_SPEC) -> tuple[list[dict[str, str]], list[str]]:
    artifact_path = repo_root / reference
    if not artifact_path.exists():
        return [], [f"task039_artifact_missing:{reference.as_posix()}"]
    return [
        {
            "reference": reference.as_posix(),
            "sha256": _sha256(artifact_path),
            "kind": "task_spec",
            "evidence_status": "confirmed",
        }
    ], []


def _public_reference(path: Path, repo_root: Path) -> str:
    try:
        reference = path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        reference = path.name
    return reference if _is_safe_reference(reference) else "unsafe_reference_redacted"


def build_report(
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    repo_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or Path(".")
    allowed_manifest_path, path_errors = _allowed_manifest_path(manifest_path, repo_root)
    if path_errors:
        manifest, load_errors = {}, path_errors
        manifest_reference = "rejected_manifest_reference"
    else:
        manifest, load_errors = _load_json_object(allowed_manifest_path)
        manifest_reference = _public_reference(allowed_manifest_path, repo_root)
    manifest_errors = []
    if not load_errors:
        enforce_tracked_index = manifest.get("path_source") != "explicit"
        manifest_errors = validate_manifest(manifest, repo_root=repo_root, enforce_tracked_index=enforce_tracked_index)

    records = manifest.get("records") if isinstance(manifest.get("records"), list) else []
    authoritative_records = [
        record
        for record in records
        if isinstance(record, dict) and record.get("authoritative") is True and record.get("schema_validation_status") == "v2_valid"
    ]

    candidates = []
    source_errors = []
    for record in authoritative_records:
        # The output replaces its own prior manifest record and can never satisfy
        # a release gate. Skipping it here keeps the two-step report/manifest
        # regeneration workflow possible while all external evidence is still
        # revalidated in full.
        if record.get("task_id") == TASK_ID:
            continue
        source, errors = _load_authoritative_source(record, repo_root)
        if errors:
            source_errors.extend(errors)
            continue
        candidates.append({"record": record, "source": source})

    gate_evidence_candidates = [
        candidate
        for candidate in candidates
        if candidate["record"].get("release_effect") in PASSABLE_RELEASE_EFFECTS
        and candidate["source"].get("release_effect") in PASSABLE_RELEASE_EFFECTS
        and _source_gate_ids(candidate["source"])
    ]

    release_gates = [_evaluate_gate(gate, candidates) for gate in DEFAULT_RELEASE_GATES]
    gate_blockers = [
        reason
        for gate in release_gates
        if gate["risk_level"] in {"R0", "R1"} and gate["decision"] != "pass"
        for reason in gate["blocked_reasons"]
    ]

    artifact_entries, artifact_errors = _artifact_for_report(repo_root)
    input_integrity_reasons = sorted(
        set(
            _safe_reason_list(load_errors)
            + _safe_reason_list(manifest_errors)
            + _safe_reason_list(source_errors)
            + _safe_reason_list(artifact_errors)
        )
    )
    blocked_reasons = sorted(
        set(
            input_integrity_reasons
            + _safe_reason_list(gate_blockers)
        )
    )
    if not records and not load_errors:
        blocked_reasons.append("manifest_records_empty")
    if not authoritative_records:
        blocked_reasons.append("authoritative_v2_evidence_records_missing")
    if not gate_evidence_candidates:
        blocked_reasons.append("authoritative_v2_gate_evidence_records_missing")

    release_decision = "pass" if not blocked_reasons and all(gate["decision"] == "pass" for gate in release_gates) else "blocked"
    execution_status = "pass" if release_decision == "pass" else "blocked"
    coverage_status = "covered" if release_decision == "pass" else "blocked"
    release_effect = "candidate_evidence" if release_decision == "pass" else "blocks_release"

    return {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "schema_validation_status": "pass",
        "execution_status": execution_status,
        "coverage_status": coverage_status,
        "evidence_status": "confirmed",
        "release_effect": release_effect,
        "production_safety_classification": PROD_SAFE_CLASSIFICATION,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "task_id": TASK_ID,
        "build_ref": {"alias": BUILD_ALIAS},
        "target_alias": TARGET_ALIAS,
        "run_id": RUN_ID,
        "artifacts": artifact_entries,
        "blocked_reasons": blocked_reasons,
        "unknowns": [
            {
                "id": "U-T039-LEGACY-MIGRATION",
                "evidence_status": "unknown",
                "question": "Legacy public summaries cannot satisfy release readiness until migrated to evidence-report-envelope-v2.",
            }
        ]
        if release_decision != "pass"
        else [],
        "risks": [
            {
                "id": "RISK-066",
                "level": "Critical",
                "status": "active",
                "summary": "Release readiness must not pass from self-asserted metadata or legacy-only summaries.",
            }
        ],
        "verification": [
            {
                "name": "report_manifest_validation",
                "status": "pass" if not manifest_errors and not load_errors else "blocked",
                "evidence_status": "confirmed",
                "classification": PROD_SAFE_CLASSIFICATION,
                "note": "Validated tracked public-safe report manifest only.",
            },
            {
                "name": "release_readiness_generation",
                "status": "pass",
                "evidence_status": "confirmed",
                "classification": PROD_SAFE_CLASSIFICATION,
                "note": "Generated without Android/runtime/device/network/API/raw-evidence access.",
            },
        ],
        "review": {
            "qa_reviewer_a": "pending",
            "qa_reviewer_b": "pending",
            "security_prod_safety_reviewer": "pending",
            "docs_scribe": "pending",
        },
        "provenance": {
            "source_manifest_reference": manifest_reference,
            "source_manifest_schema_version": manifest.get("schema_version", "unknown") if isinstance(manifest, dict) else "unknown",
            "source_manifest_record_count": manifest.get("record_count", 0) if isinstance(manifest, dict) else 0,
            "source_manifest_authoritative_record_count": manifest.get("authoritative_record_count", 0)
            if isinstance(manifest, dict)
            else 0,
            "generator": TOOL_NAME,
        },
        "payload": {
            "readiness_decision": release_decision,
            "input_integrity_status": "pass" if not input_integrity_reasons else "blocked",
            "input_integrity_reasons": input_integrity_reasons,
            "manifest_reference": manifest_reference,
            "manifest_record_count": manifest.get("record_count", 0) if isinstance(manifest, dict) else 0,
            "manifest_authoritative_record_count": len(authoritative_records),
            "manifest_legacy_record_count": manifest.get("legacy_record_count", 0) if isinstance(manifest, dict) else 0,
            "release_gates": release_gates,
            "excluded_domains": [
                "payment",
                "webview",
                "stream_session",
                "live_api_backend",
                "broad_compatibility",
                "performance_qoe_soak",
                "accessibility_localization",
                "product_security_privacy",
            ],
        },
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("schema_version") != ENVELOPE_SCHEMA_VERSION:
        errors.append("readiness_schema_version_invalid")
    if report.get("schema_validation_status") != "pass":
        errors.append("readiness_schema_validation_status_invalid")
    payload = report.get("payload")
    if not isinstance(payload, dict):
        errors.append("readiness_payload_must_be_object")
        payload = {}
    readiness_decision = payload.get("readiness_decision")
    if readiness_decision not in {"pass", "blocked"}:
        errors.append("readiness_decision_invalid")
    input_integrity_status = payload.get("input_integrity_status")
    input_integrity_reasons = payload.get("input_integrity_reasons")
    if input_integrity_status not in {"pass", "blocked"}:
        errors.append("input_integrity_status_invalid")
    if not isinstance(input_integrity_reasons, list):
        errors.append("input_integrity_reasons_must_be_list")
    elif input_integrity_status == "pass" and input_integrity_reasons:
        errors.append("passing_input_integrity_requires_empty_reasons")
    elif input_integrity_status == "blocked" and not input_integrity_reasons:
        errors.append("blocked_input_integrity_requires_reasons")

    release_gates = payload.get("release_gates")
    expected_gate_ids = {gate["id"] for gate in DEFAULT_RELEASE_GATES}
    actual_gate_ids = [gate.get("id") for gate in release_gates if isinstance(gate, dict)] if isinstance(release_gates, list) else []
    if not isinstance(release_gates, list):
        errors.append("release_gates_must_be_list")
    elif (
        not all(isinstance(gate_id, str) for gate_id in actual_gate_ids)
        or len(actual_gate_ids) != len(expected_gate_ids)
        or set(actual_gate_ids) != expected_gate_ids
    ):
        errors.append("release_gates_must_match_required_set")

    if readiness_decision == "pass":
        if report.get("execution_status") != "pass":
            errors.append("pass_readiness_requires_pass_execution")
        if report.get("coverage_status") != "covered":
            errors.append("pass_readiness_requires_covered_status")
        if report.get("release_effect") != "candidate_evidence":
            errors.append("pass_readiness_requires_candidate_evidence_effect")
        if report.get("blocked_reasons"):
            errors.append("pass_readiness_requires_empty_blocked_reasons")
        if input_integrity_status != "pass":
            errors.append("pass_readiness_requires_valid_input_integrity")
        for gate in release_gates if isinstance(release_gates, list) else []:
            if (
                not isinstance(gate, dict)
                or gate.get("decision") != "pass"
                or gate.get("evidence_status") != "confirmed"
                or not gate.get("source_record_ids")
            ):
                errors.append("pass_readiness_requires_all_gates_confirmed")
                break
    elif readiness_decision == "blocked":
        if report.get("execution_status") != "blocked":
            errors.append("blocked_readiness_requires_blocked_execution")
        if report.get("coverage_status") != "blocked":
            errors.append("blocked_readiness_requires_blocked_coverage")
        if report.get("release_effect") != "blocks_release":
            errors.append("blocked_readiness_requires_blocks_release_effect")
        if not report.get("blocked_reasons"):
            errors.append("blocked_readiness_requires_reasons")
    if _raw_value_findings(report):
        errors.append("readiness_report_contains_raw_or_private_like_values")
    return sorted(set(errors))


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a manifest-backed TASK-039 release-readiness report.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Public-safe report manifest.")
    parser.add_argument("--output", type=Path, default=None, help="Optional output JSON path. Defaults to stdout.")
    parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Return success after emitting a structurally valid blocked readiness report.",
    )
    args = parser.parse_args(argv)

    report = build_report(args.manifest)
    validation_errors = validate_report(report)
    if validation_errors:
        report["execution_status"] = "blocked"
        report["coverage_status"] = "blocked"
        report["release_effect"] = "blocks_release"
        report["blocked_reasons"] = sorted(set(report.get("blocked_reasons", []) + validation_errors))

    if args.output is None:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    else:
        _write_report(args.output, report)

    if validation_errors:
        return 1
    if report["payload"].get("input_integrity_status") != "pass":
        return 1
    if report["payload"]["readiness_decision"] != "pass" and not args.allow_blocked:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
