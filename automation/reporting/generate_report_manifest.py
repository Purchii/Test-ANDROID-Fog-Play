"""Generate and validate the public-safe TASK-038 report manifest.

TASK-038 is offline/static only. This tool indexes tracked public-safe JSON
reports under docs/qa/reports, computes SHA-256 values, and emits explicit
schema-v2 or legacy-migration records. It never reads ignored raw evidence,
APKs, Android devices, network services, WebView/payment/session material or
private endpoints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any


TASK_ID = "TASK-038"
TOOL_NAME = "reporting.report_manifest_generator"
MANIFEST_SCHEMA_VERSION = "report-manifest-v1"
ENVELOPE_SCHEMA_VERSION = "evidence-report-envelope-v2"
PROD_SAFE_CLASSIFICATION = "PROD_SAFE_OFFLINE_STATIC_ONLY"
DEFAULT_REPORTS_ROOT = Path("docs/qa/reports")
DEFAULT_OUTPUT = DEFAULT_REPORTS_ROOT / "report-manifest.json"
CANONICAL_TEXT_SUFFIXES = {".csv", ".json", ".md", ".py", ".txt", ".yaml", ".yml"}

SCHEMA_VALIDATION_STATUSES = {"v2_valid", "legacy_migration_blocked", "unknown_schema", "invalid"}
EXECUTION_STATUSES = {
    "pass",
    "fail",
    "blocked",
    "not_run",
    "partial",
    "partial_blocked",
    "covered",
    "closed_by_ledger",
    "partial_runtime_correlated",
    "unknown",
}
COVERAGE_STATUSES = {"covered", "partial", "partial_blocked", "blocked", "not_run", "unknown"}
EVIDENCE_STATUSES = {
    "confirmed",
    "confirmed_for_recorded_checkpoints",
    "likely",
    "likely_with_blockers",
    "hypothesis",
    "unknown",
}
RELEASE_EFFECTS = {"candidate_evidence", "blocks_release", "no_release_claim", "deferred", "unknown"}
AUTHORITY_STATUSES = {"authoritative", "superseded", "legacy_not_authoritative", "blocked"}
FORBIDDEN_REFERENCE_PARTS = {
    ".qa_local",
    "qa_reverse_analysis",
    "safe_archives",
    "docs/context/reverse-analysis/raw",
}
RAW_VALUE_RE = re.compile(
    r"\b(?:https?|wss?|otpauth)://|"
    r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])|"
    r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{2,5})?\b|"
    r"\b[A-Za-z0-9.-]+\.(?:com|ru|net|org|io|dev|app|cloud|tv)(?:/[^\s\"']*)?|"
    r"\b(?:authorization|bearer|cookie|session|token|secret|password|api[_-]?key|otp|captcha)"
    r"[:=]\s*\S+",
    re.IGNORECASE,
)
FORBIDDEN_VALUE_PARTS = {
    ".qa_local",
    "qa_reverse_analysis",
    "safe_archives",
    "docs/context/reverse-analysis/raw",
}
FORBIDDEN_PAYLOAD_STATUS_TOKENS = {
    "adb",
    "android",
    "apk",
    "backend",
    "live_api",
    "network",
    "payment",
    "runtime",
    "session",
    "stream",
    "webview",
    "webrtc",
}
V2_REQUIRED_FIELDS = {
    "schema_version",
    "schema_validation_status",
    "execution_status",
    "coverage_status",
    "evidence_status",
    "release_effect",
    "production_safety_classification",
    "generated_at_utc",
    "task_id",
    "build_ref",
    "target_alias",
    "run_id",
    "artifacts",
    "blocked_reasons",
    "unknowns",
    "risks",
    "verification",
    "review",
    "provenance",
}
V2_ALLOWED_FIELDS = V2_REQUIRED_FIELDS | {"payload", "supersession"}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    content = path.read_bytes()
    if path.suffix.lower() in CANONICAL_TEXT_SUFFIXES:
        content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        relative = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        relative = path
    return relative.as_posix()


def _is_safe_reference(reference: str) -> bool:
    if not reference or RAW_VALUE_RE.search(reference):
        return False
    pure = PurePosixPath(reference)
    if pure.is_absolute() or ".." in pure.parts:
        return False
    normalized = reference.replace("\\", "/")
    return not any(normalized == part or normalized.startswith(part + "/") for part in FORBIDDEN_REFERENCE_PARTS)


def _tracked_report_paths(reports_root: Path, repo_root: Path | None = None) -> tuple[list[Path], str, list[str]]:
    repo_root = (repo_root or Path.cwd()).resolve()
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={repo_root.as_posix()}",
                "ls-files",
                "-z",
                "--",
                f"{reports_root.as_posix()}/*.json",
            ],
            check=False,
            capture_output=True,
            text=False,
            cwd=repo_root,
        )
    except OSError:
        result = None
    if result is not None and result.returncode == 0:
        paths = [Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]
        return _filter_report_paths(paths), "git_tracked", []
    return [], "git_tracked_unavailable", ["tracked_report_index_unavailable"]


def _filter_report_paths(paths: Any) -> list[Path]:
    filtered = []
    for path in paths:
        path = Path(path)
        normalized = path.as_posix()
        if path.name == DEFAULT_OUTPUT.name:
            continue
        if path.suffix.lower() != ".json":
            continue
        if DEFAULT_REPORTS_ROOT.as_posix() not in normalized:
            continue
        filtered.append(path)
    return sorted(filtered, key=lambda item: item.as_posix())


def _load_json_object(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"json_malformed:{exc.msg}"]
    except OSError:
        return {}, ["json_unreadable"]
    if not isinstance(loaded, dict):
        return {}, ["json_not_object"]
    return loaded, []


def _infer_task_id(path: Path, data: dict[str, Any]) -> str:
    task_id = data.get("task_id")
    if isinstance(task_id, str) and re.fullmatch(r"TASK-\d{3}[A-Z]?", task_id):
        return task_id
    match = re.search(r"task(\d{3})([a-z]?)", path.name, re.IGNORECASE)
    if match:
        suffix = match.group(2).upper()
        return f"TASK-{match.group(1)}{suffix}"
    return "TASK-UNKNOWN"


def _first_string(data: dict[str, Any], names: tuple[str, ...], default: str) -> str:
    for name in names:
        value = data.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def _build_alias(data: dict[str, Any]) -> str:
    build_ref = data.get("build_ref")
    if isinstance(build_ref, dict):
        alias = build_ref.get("alias")
        if isinstance(alias, str) and alias.strip():
            return alias.strip()
    if isinstance(build_ref, str) and build_ref.strip():
        return build_ref.strip()
    return _first_string(data, ("build_alias", "approved_build_alias"), "unknown_build")


def _normalize(value: Any, allowed: set[str], default: str) -> str:
    if isinstance(value, str) and value.strip() in allowed:
        return value.strip()
    return default


def _is_known_legacy_schema(schema_version: Any) -> bool:
    if schema_version == "1.0":
        return True
    return isinstance(schema_version, str) and re.fullmatch(r"task[-_a-zA-Z0-9]+v\d+", schema_version) is not None


def _private_text_findings(text: str) -> list[str]:
    findings: list[str] = []
    normalized = text.replace("\\", "/").lower()
    if any(part in normalized for part in FORBIDDEN_VALUE_PARTS):
        findings.append("raw_forbidden_path_family")
    if RAW_VALUE_RE.search(text):
        findings.append("raw_private_like_text")
    return findings


def _raw_value_findings(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str):
                findings.extend(f"{path}_{finding}_key" for finding in _private_text_findings(key))
            findings.extend(_raw_value_findings(child, f"{path}.{key}"))
        return findings
    if isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_raw_value_findings(child, f"{path}[{index}]"))
        return findings
    if isinstance(value, str):
        findings.extend(f"{path}_{finding}" for finding in _private_text_findings(value))
    return findings


def _payload_overclaim_findings(value: Any, path: str = "$", in_forbidden_domain: bool = False) -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            child_forbidden_domain = in_forbidden_domain or any(
                token in key_text for token in FORBIDDEN_PAYLOAD_STATUS_TOKENS
            )
            if key_text.endswith("_status") and any(token in key_text for token in FORBIDDEN_PAYLOAD_STATUS_TOKENS):
                findings.append(f"{path}.{key}_hidden_runtime_or_live_status_key")
            if key_text == "status" and in_forbidden_domain:
                findings.append(f"{path}.{key}_hidden_runtime_or_live_status_key")
            findings.extend(_payload_overclaim_findings(child, f"{path}.{key}", child_forbidden_domain))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_payload_overclaim_findings(child, f"{path}[{index}]", in_forbidden_domain))
    return findings


def _safe_public_string(value: str, fallback: str, field_name: str) -> tuple[str, list[str]]:
    findings = _private_text_findings(value)
    if findings:
        return fallback, [f"unsafe_public_field:{field_name}:{finding}" for finding in findings]
    return value, []


def _validate_v2_envelope(data: dict[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    missing = sorted(V2_REQUIRED_FIELDS - set(data))
    if missing:
        errors.append(f"v2_missing_required_fields:{','.join(missing)}")
    unknown = sorted(set(data) - V2_ALLOWED_FIELDS)
    if unknown:
        errors.append(f"v2_unknown_top_level_fields:{','.join(unknown)}")
    if data.get("schema_version") != ENVELOPE_SCHEMA_VERSION:
        errors.append("v2_schema_version_invalid")
    if data.get("schema_validation_status") != "pass":
        errors.append("v2_schema_validation_status_must_be_pass")
    if data.get("execution_status") not in EXECUTION_STATUSES:
        errors.append("v2_execution_status_invalid")
    if data.get("coverage_status") not in COVERAGE_STATUSES:
        errors.append("v2_coverage_status_invalid")
    if data.get("evidence_status") not in EVIDENCE_STATUSES:
        errors.append("v2_evidence_status_invalid")
    if data.get("release_effect") not in RELEASE_EFFECTS:
        errors.append("v2_release_effect_invalid")
    safety = data.get("production_safety_classification")
    if not isinstance(safety, str) or not safety.startswith("PROD_"):
        errors.append("v2_production_safety_classification_invalid")
    if not isinstance(data.get("build_ref"), dict):
        errors.append("v2_build_ref_must_be_object")
    if not isinstance(data.get("target_alias"), str) or not data.get("target_alias"):
        errors.append("v2_target_alias_invalid")
    if not isinstance(data.get("run_id"), str) or not data.get("run_id"):
        errors.append("v2_run_id_invalid")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("v2_artifacts_must_be_non_empty_list")
    else:
        for item in artifacts:
            if not _artifact_is_valid(item):
                errors.append("v2_artifact_entry_invalid")
                continue
            reference = item["reference"]
            artifact_path = repo_root / PurePosixPath(reference)
            if not artifact_path.exists():
                errors.append(f"v2_artifact_reference_missing:{reference}")
                continue
            if _sha256(artifact_path) != item["sha256"]:
                errors.append(f"v2_artifact_sha256_mismatch:{reference}")
    for field_name in ("blocked_reasons", "unknowns", "risks", "verification"):
        if not isinstance(data.get(field_name), list):
            errors.append(f"v2_{field_name}_must_be_list")
    for field_name in ("review", "provenance"):
        if not isinstance(data.get(field_name), dict):
            errors.append(f"v2_{field_name}_must_be_object")
    if data.get("execution_status") == "pass" and data.get("evidence_status") != "confirmed":
        errors.append("v2_pass_requires_confirmed_evidence")
    if data.get("execution_status") == "pass" and data.get("blocked_reasons") not in ([], None):
        errors.append("v2_pass_requires_empty_blocked_reasons")
    if data.get("payload") is not None and not isinstance(data.get("payload"), dict):
        errors.append("v2_payload_must_be_object")
    elif isinstance(data.get("payload"), dict):
        errors.extend(f"v2_{finding}" for finding in _payload_overclaim_findings(data["payload"], "$.payload"))
    errors.extend(f"v2_{finding}" for finding in _raw_value_findings(data))
    return sorted(set(errors))


def _artifact_is_valid(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    reference = item.get("reference")
    sha = item.get("sha256")
    kind = item.get("kind")
    evidence_status = item.get("evidence_status")
    return (
        isinstance(reference, str)
        and _is_safe_reference(reference)
        and isinstance(sha, str)
        and re.fullmatch(r"[a-f0-9]{64}", sha) is not None
        and isinstance(kind, str)
        and bool(kind)
        and evidence_status in EVIDENCE_STATUSES
    )


def _record_from_report(path: Path, repo_root: Path) -> dict[str, Any]:
    reference = _repo_relative(path, repo_root)
    sha = _sha256(path)
    data, load_errors = _load_json_object(path)
    raw_schema_version = data.get("schema_version")
    schema_version = raw_schema_version
    task_id = _infer_task_id(path, data)
    field_errors: list[str] = []
    raw_build_alias = _build_alias(data)
    build_alias, build_errors = _safe_public_string(raw_build_alias, "unknown_build", "build_ref.alias")
    field_errors.extend(build_errors)
    raw_target_alias = _first_string(
        data,
        ("target_alias", "public_device_alias", "public_runtime_profile_alias"),
        "unknown_target",
    )
    target_alias, target_errors = _safe_public_string(raw_target_alias, "unknown_target", "target_alias")
    field_errors.extend(target_errors)
    raw_run_id = _first_string(data, ("run_id",), path.stem)
    run_id, run_errors = _safe_public_string(raw_run_id, path.stem, "run_id")
    field_errors.extend(run_errors)
    raw_generated_at = _first_string(data, ("generated_at_utc",), "unknown")
    generated_at, generated_errors = _safe_public_string(raw_generated_at, "unknown", "generated_at_utc")
    field_errors.extend(generated_errors)
    public_schema_version, schema_version_errors = _safe_public_string(
        raw_schema_version if isinstance(raw_schema_version, str) else "missing",
        "unsafe_or_missing",
        "schema_version",
    )
    field_errors.extend(schema_version_errors)

    if load_errors:
        schema_status = "invalid"
        blocked_reasons = load_errors
    elif schema_version == ENVELOPE_SCHEMA_VERSION:
        v2_errors = _validate_v2_envelope(data, repo_root)
        schema_status = "v2_valid" if not v2_errors else "invalid"
        blocked_reasons = v2_errors
    elif _is_known_legacy_schema(schema_version):
        schema_status = "legacy_migration_blocked"
        blocked_reasons = ["legacy_report_not_evidence_envelope_v2"]
    else:
        schema_status = "unknown_schema"
        blocked_reasons = ["unknown_report_schema_version"]
    if field_errors:
        schema_status = "invalid"
        blocked_reasons = sorted(set(blocked_reasons + field_errors))

    execution_status = _normalize(
        data.get("execution_status", data.get("runtime_execution_status", data.get("overall_status"))),
        EXECUTION_STATUSES,
        "unknown",
    )
    coverage_status = _normalize(data.get("coverage_status", data.get("overall_status")), COVERAGE_STATUSES, "unknown")
    evidence_status = _normalize(data.get("evidence_status"), EVIDENCE_STATUSES, "unknown")
    release_effect = _normalize(data.get("release_effect"), RELEASE_EFFECTS, "no_release_claim")
    production_safety = _first_string(data, ("production_safety_classification",), "unknown")
    if not production_safety.startswith("PROD_"):
        production_safety = "unknown"
    production_safety, safety_errors = _safe_public_string(
        production_safety,
        "unknown",
        "production_safety_classification",
    )
    field_errors.extend(safety_errors)
    if field_errors:
        schema_status = "invalid"
        blocked_reasons = sorted(set(blocked_reasons + field_errors))

    record_id = _record_id(task_id, build_alias, target_alias, run_id, reference)
    return {
        "record_id": record_id,
        "task_id": task_id,
        "build_ref": {"alias": build_alias},
        "target_alias": target_alias,
        "run_id": run_id,
        "generated_at_utc": generated_at,
        "schema_version": public_schema_version,
        "schema_validation_status": schema_status,
        "execution_status": execution_status,
        "coverage_status": coverage_status,
        "evidence_status": evidence_status,
        "release_effect": release_effect,
        "production_safety_classification": production_safety,
        "authority_status": "blocked" if schema_status in {"invalid", "unknown_schema"} else "legacy_not_authoritative",
        "authoritative": False,
        "supersedes": [],
        "superseded_by": None,
        "artifacts": [
            {
                "reference": reference,
                "sha256": sha,
                "kind": "public_safe_report_summary",
                "evidence_status": evidence_status,
            }
        ],
        "blocked_reasons": blocked_reasons,
        "unknowns": _unknowns_for(data, schema_status),
        "risks": _risks_for(schema_status),
        "verification": [
            {
                "name": "report_file_sha256",
                "status": "pass",
                "evidence_status": "confirmed",
                "reference": reference,
                "sha256": sha,
            }
        ],
        "review": {
            "manifest_generator": "generated",
            "schema_policy": schema_status,
        },
        "provenance": {
            "source_reference": reference,
            "source_sha256": sha,
            "source_kind": "tracked_public_safe_report",
            "indexed_by_task": TASK_ID,
        },
    }


def _record_id(task_id: str, build_alias: str, target_alias: str, run_id: str, reference: str) -> str:
    raw = f"{task_id}__{build_alias}__{target_alias}__{run_id}__{Path(reference).stem}"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)


def _unknowns_for(data: dict[str, Any], schema_status: str) -> list[dict[str, str]]:
    unknowns = []
    if schema_status != "v2_valid":
        unknowns.append(
            {
                "id": "U-T038-MIGRATION",
                "evidence_status": "unknown",
                "question": "Report is not yet migrated to evidence-report-envelope-v2.",
            }
        )
    for field_name in ("generated_at_utc", "evidence_status", "production_safety_classification"):
        if field_name not in data:
            unknowns.append(
                {
                    "id": f"U-T038-MISSING-{field_name.upper()}",
                    "evidence_status": "unknown",
                    "question": f"Legacy report has no top-level {field_name}.",
                }
            )
    return unknowns


def _risks_for(schema_status: str) -> list[dict[str, str]]:
    if schema_status == "v2_valid":
        return []
    return [
        {
            "id": "RISK-065",
            "level": "High",
            "status": "active",
            "summary": "Legacy or unknown report schema cannot be used as authoritative release evidence.",
        }
    ]


def _authority_key(record: dict[str, Any]) -> tuple[str, str, str, str]:
    build = record.get("build_ref", {}).get("alias", "unknown_build")
    return (record["task_id"], build, record["target_alias"], record["run_id"])


def _assign_authority(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["schema_validation_status"] == "v2_valid":
            by_key[_authority_key(record)].append(record)

    for grouped in by_key.values():
        sorted_group = sorted(grouped, key=lambda item: (item.get("generated_at_utc", ""), item["record_id"]))
        if len(sorted_group) > 1:
            latest_time = sorted_group[-1].get("generated_at_utc")
            if len([item for item in sorted_group if item.get("generated_at_utc") == latest_time]) > 1:
                errors.append(f"ambiguous_authoritative_records:{','.join(item['record_id'] for item in sorted_group)}")
                for item in sorted_group:
                    item["authority_status"] = "blocked"
                continue
        winner = sorted_group[-1]
        winner["authoritative"] = True
        winner["authority_status"] = "authoritative"
        for item in sorted_group[:-1]:
            item["authority_status"] = "superseded"
            item["superseded_by"] = winner["record_id"]
            winner["supersedes"].append(item["record_id"])
    return errors


def build_manifest(
    report_paths: list[Path] | None = None,
    repo_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or Path(".")
    path_errors: list[str] = []
    if report_paths is None:
        report_paths, path_source, path_errors = _tracked_report_paths(DEFAULT_REPORTS_ROOT, repo_root)
    else:
        report_paths = _filter_report_paths(report_paths)
        path_source = "explicit"

    records = [_record_from_report(path, repo_root) for path in report_paths]
    authority_errors = _assign_authority(records)
    validation_errors = validate_manifest_records(records, repo_root)
    blocked_reasons = sorted(set(path_errors + authority_errors + validation_errors))
    if not records:
        blocked_reasons.append("manifest_records_empty")

    legacy_count = len([record for record in records if record["schema_validation_status"] == "legacy_migration_blocked"])
    v2_count = len([record for record in records if record["schema_validation_status"] == "v2_valid"])
    unknown_schema_count = len([record for record in records if record["schema_validation_status"] == "unknown_schema"])
    invalid_count = len([record for record in records if record["schema_validation_status"] == "invalid"])
    authoritative_count = len([record for record in records if record["authoritative"] is True])

    manifest_status = "pass"
    if blocked_reasons or unknown_schema_count or invalid_count or not records:
        manifest_status = "blocked"
    elif legacy_count:
        manifest_status = "pass_with_legacy_migration_blockers"

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "task_id": TASK_ID,
        "tool_name": TOOL_NAME,
        "mode": "BOUNDED_AUTONOMOUS",
        "production_safety_classification": PROD_SAFE_CLASSIFICATION,
        "manifest_status": manifest_status,
        "reports_root": DEFAULT_REPORTS_ROOT.as_posix(),
        "path_source": path_source,
        "record_count": len(records),
        "authoritative_record_count": authoritative_count,
        "legacy_record_count": legacy_count,
        "v2_record_count": v2_count,
        "unknown_schema_record_count": unknown_schema_count,
        "invalid_record_count": invalid_count,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "records": records,
        "verification": [
            {
                "name": "manifest_generation",
                "status": "pass" if manifest_status != "blocked" else "blocked",
                "evidence_status": "confirmed",
                "classification": PROD_SAFE_CLASSIFICATION,
                "note": "Indexed public-safe report JSON files only; no ignored raw evidence was read.",
            }
        ],
    }


def validate_manifest_records(records: list[dict[str, Any]], repo_root: Path) -> list[str]:
    errors: list[str] = []
    authority_keys: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    for record in records:
        errors.extend(_validate_record_shape(record))
        if record.get("authoritative") is True:
            authority_keys[_authority_key(record)].append(record["record_id"])
        for artifact in record.get("artifacts", []):
            reference = artifact.get("reference") if isinstance(artifact, dict) else None
            if not isinstance(reference, str) or not _is_safe_reference(reference):
                errors.append(f"unsafe_artifact_reference:{record.get('record_id', 'unknown')}")
                continue
            artifact_path = repo_root / PurePosixPath(reference)
            if not artifact_path.exists():
                errors.append(f"missing_artifact_reference:{reference}")
                continue
            expected_sha = artifact.get("sha256")
            actual_sha = _sha256(artifact_path)
            if expected_sha != actual_sha:
                errors.append(f"artifact_sha256_mismatch:{reference}")
    for key, record_ids in authority_keys.items():
        if len(record_ids) > 1:
            errors.append(f"duplicate_authoritative_records:{'|'.join(key)}:{','.join(sorted(record_ids))}")
    return sorted(set(errors))


def _validate_record_shape(record: dict[str, Any]) -> list[str]:
    required = {
        "record_id",
        "task_id",
        "build_ref",
        "target_alias",
        "run_id",
        "schema_version",
        "schema_validation_status",
        "execution_status",
        "coverage_status",
        "evidence_status",
        "release_effect",
        "production_safety_classification",
        "authority_status",
        "authoritative",
        "artifacts",
        "blocked_reasons",
        "unknowns",
        "risks",
        "verification",
        "review",
        "provenance",
    }
    errors: list[str] = []
    missing = sorted(required - set(record))
    if missing:
        errors.append(f"record_missing_required_fields:{record.get('record_id', 'unknown')}:{','.join(missing)}")
    if record.get("schema_validation_status") not in SCHEMA_VALIDATION_STATUSES:
        errors.append(f"record_schema_validation_status_invalid:{record.get('record_id', 'unknown')}")
    if record.get("schema_validation_status") == "unknown_schema":
        errors.append(f"record_unknown_schema:{record.get('record_id', 'unknown')}")
    if record.get("execution_status") not in EXECUTION_STATUSES:
        errors.append(f"record_execution_status_invalid:{record.get('record_id', 'unknown')}")
    if record.get("coverage_status") not in COVERAGE_STATUSES:
        errors.append(f"record_coverage_status_invalid:{record.get('record_id', 'unknown')}")
    if record.get("evidence_status") not in EVIDENCE_STATUSES:
        errors.append(f"record_evidence_status_invalid:{record.get('record_id', 'unknown')}")
    if record.get("release_effect") not in RELEASE_EFFECTS:
        errors.append(f"record_release_effect_invalid:{record.get('record_id', 'unknown')}")
    if record.get("authority_status") not in AUTHORITY_STATUSES:
        errors.append(f"record_authority_status_invalid:{record.get('record_id', 'unknown')}")
    if not isinstance(record.get("authoritative"), bool):
        errors.append(f"record_authoritative_must_be_boolean:{record.get('record_id', 'unknown')}")
    if not isinstance(record.get("artifacts"), list) or not record.get("artifacts"):
        errors.append(f"record_artifacts_must_be_non_empty_list:{record.get('record_id', 'unknown')}")
    if record.get("schema_validation_status") == "legacy_migration_blocked" and not record.get("blocked_reasons"):
        errors.append(f"legacy_record_requires_blocked_reasons:{record.get('record_id', 'unknown')}")
    raw_findings = _raw_value_findings(record)
    if raw_findings:
        errors.extend(f"record_raw_private_value:{record.get('record_id', 'unknown')}:{finding}" for finding in raw_findings)
    return errors


def validate_manifest(
    manifest: dict[str, Any],
    repo_root: Path | None = None,
    enforce_tracked_index: bool = True,
) -> list[str]:
    repo_root = repo_root or Path(".")
    errors: list[str] = []
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append("manifest_schema_version_invalid")
    records = manifest.get("records")
    if not isinstance(records, list):
        return errors + ["manifest_records_must_be_list"]
    if not records:
        errors.append("manifest_records_empty")
    errors.extend(validate_manifest_records(records, repo_root))
    if manifest.get("record_count") != len(records):
        errors.append("manifest_record_count_mismatch")
    if manifest.get("unknown_schema_record_count", 0) != 0:
        errors.append("manifest_unknown_schema_record_count_must_be_zero")
    if manifest.get("invalid_record_count", 0) != 0:
        errors.append("manifest_invalid_record_count_must_be_zero")
    if enforce_tracked_index:
        reports_root = Path(manifest.get("reports_root", DEFAULT_REPORTS_ROOT.as_posix()))
        tracked_paths, _, tracked_errors = _tracked_report_paths(reports_root, repo_root)
        if tracked_errors:
            errors.extend(f"manifest_{error}" for error in tracked_errors)
        else:
            expected_refs = {_repo_relative(path, repo_root) for path in tracked_paths}
            actual_refs = {
                record.get("provenance", {}).get("source_reference")
                for record in records
                if isinstance(record, dict) and isinstance(record.get("provenance"), dict)
            }
            actual_refs = {ref for ref in actual_refs if isinstance(ref, str)}
            missing_refs = sorted(expected_refs - actual_refs)
            extra_refs = sorted(actual_refs - expected_refs)
            if missing_refs:
                errors.append(f"manifest_missing_tracked_reports:{','.join(missing_refs)}")
            if extra_refs:
                errors.append(f"manifest_untracked_report_records:{','.join(extra_refs)}")
    if manifest.get("manifest_status") == "blocked":
        blocked_reasons = manifest.get("blocked_reasons")
        if not blocked_reasons:
            errors.append("blocked_manifest_requires_blocked_reasons")
        elif isinstance(blocked_reasons, list):
            errors.extend(f"manifest_blocked:{reason}" for reason in blocked_reasons)
        else:
            errors.append("blocked_manifest_reasons_must_be_list")
    return sorted(set(errors))


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or validate the TASK-038 report manifest.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Manifest output path.")
    parser.add_argument("--manifest", type=Path, help="Existing manifest to validate.")
    parser.add_argument("--validate-only", action="store_true", help="Validate an existing manifest.")
    args = parser.parse_args(argv)

    repo_root = Path(".")
    if args.validate_only:
        manifest_path = args.manifest or args.output
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            sys.stdout.write(
                json.dumps({"validation_status": "blocked", "blocked_reasons": ["manifest_unreadable_or_malformed"]})
                + "\n"
            )
            return 1
    else:
        manifest = build_manifest(repo_root=repo_root)
        _write_manifest(args.output, manifest)

    errors = validate_manifest(manifest, repo_root)
    result = {
        "validation_status": "pass" if not errors else "blocked",
        "manifest_status": manifest.get("manifest_status", "unknown"),
        "record_count": manifest.get("record_count", 0),
        "legacy_record_count": manifest.get("legacy_record_count", 0),
        "authoritative_record_count": manifest.get("authoritative_record_count", 0),
        "blocked_reasons": errors,
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
