"""Validate TASK-028 API-layer contract coverage from a quarantined audit pack.

The validator is local/offline only. It reads an owner-provided archive after it
has been extracted into ignored local storage, validates contract coverage
structure and emits a public-safe summary without raw endpoints, URLs, headers,
payloads, tokens, fixture bodies or local machine paths.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "TASK-028"
SCHEMA_VERSION = "task028-api-layer-contract-coverage-v1"
TOOL_NAME = "validate_task028_api_layer_contract"

REQUIRED_PACK_FILES = (
    "specs/api_inventory.yaml",
    "specs/test_matrix.csv",
    "VALIDATION_RESULT.txt",
)
REQUIRED_PACK_DIRS = (
    "docs",
    "fixtures",
    "schemas",
    "specs",
)
REQUIRED_MATRIX_COLUMNS = {
    "test_id",
    "domain",
    "layer",
    "item",
    "test_type",
    "priority",
    "title",
    "automation_target",
    "fixture_or_sequence",
    "parallelization",
    "status",
}
ALLOWED_MATRIX_STATUSES = {"ready_or_fixture_only", "deferred_not_blocking_this_run"}
ALLOWED_PARALLELIZATION = {"independent_api_layer"}
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}
ALLOWED_LAYERS = {"rest", "protocol", "state_machine_sequence", "security", "runtime_optional"}
EXPECTED_FIXTURE_GROUPS = {"rest", "sequences", "stomp_signaling", "stomp_device", "datachannel", "gamepad"}
EXPECTED_SCHEMA_GROUPS = {"rest", "protocol"}
RUNTIME_OPTIONAL_EXPECTED_COUNT = 4

FORBIDDEN_PUBLIC_FLAGS = {
    "raw_endpoints_public",
    "raw_urls_public",
    "raw_headers_public",
    "raw_payloads_public",
    "raw_fixture_bodies_public",
    "raw_tokens_or_sessions_public",
    "raw_phone_otp_captcha_public",
    "raw_payment_values_public",
    "raw_device_identifiers_public",
    "raw_local_paths_public",
    "live_network_calls_performed",
    "real_payment_or_session_mutation_performed",
    "apk_or_runtime_actions_performed",
    "tls_or_security_bypass_performed",
}

FOLLOW_UP_TASKS = [
    {
        "task_id": "TASK-029",
        "title": "REST schema and fixture contract harness",
        "scope": "Generate parametrized REST fixture/schema tests from TASK-028 sanitized coverage ledger.",
        "production_safety_classification": "PROD_SAFE",
    },
    {
        "task_id": "TASK-030",
        "title": "REST negative, cache and state-sequence contract tests",
        "scope": "Implement offline cache/error/sequence tests with mocked transport only.",
        "production_safety_classification": "PROD_SAFE",
    },
    {
        "task_id": "TASK-031",
        "title": "STOMP signaling and device protocol contract tests",
        "scope": "Validate protocol fixtures and malformed-message behavior offline.",
        "production_safety_classification": "PROD_SAFE",
    },
    {
        "task_id": "TASK-032",
        "title": "DataChannel and gamepad protocol contract tests",
        "scope": "Validate DataChannel/gamepad message fixtures and invalid cases offline.",
        "production_safety_classification": "PROD_SAFE",
    },
    {
        "task_id": "TASK-033",
        "title": "API-layer redaction and production-safety guard tests",
        "scope": "Expand redaction/security guards for API, protocol, payment, device and session evidence.",
        "production_safety_classification": "PROD_SAFE",
    },
    {
        "task_id": "TASK-034",
        "title": "Optional approved staging API execution gate",
        "scope": "Only after explicit staging/QA environment, synthetic user, budget, cleanup and review approvals.",
        "production_safety_classification": "PROD_CONDITIONAL",
    },
]

URL_RE = re.compile(r"\b(?:https?|wss?)://", re.IGNORECASE)
ENDPOINT_PATH_RE = re.compile(r"(?<![\w-])/(?:api|log|ws|socket|stomp|payment|login|order|content)[/\w{}.-]*", re.IGNORECASE)
SECRET_RE = re.compile(
    r"\b(?:authorization|bearer|cookie|session|token|secret|password|api[_-]?key|otp|captcha)\b",
    re.IGNORECASE,
)
PAYMENT_RE = re.compile(r"\b(?:payment|billing|card|receipt|invoice|payurl|paymenturl)\b", re.IGNORECASE)
DEVICE_RE = re.compile(r"\b(?:device[_-]?id|android[_-]?id|serial|imei|imsi|mac)\b", re.IGNORECASE)
LOCAL_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])", re.IGNORECASE)
RAW_URL_OR_ENDPOINT_RE = re.compile(r"\b(?:https?|wss?)://|(?<![\w-])/(?:api|log|ws|socket|stomp)[/\w{}.-]*", re.IGNORECASE)
HEX_HASH_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")


@dataclass(frozen=True)
class MatrixAnalysis:
    rows: list[dict[str, str]]
    errors: list[str]
    counts_by_layer: Counter[str]
    counts_by_priority: Counter[str]
    counts_by_test_type: Counter[str]
    counts_by_target: Counter[str]
    counts_by_status: Counter[str]
    fixture_refs: list[str]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_pack_root(pack_root: Path) -> tuple[Path | None, list[str]]:
    candidate = pack_root.resolve()
    if (candidate / "specs" / "test_matrix.csv").exists():
        return candidate, []
    child_candidates = [path for path in candidate.iterdir() if path.is_dir()] if candidate.exists() else []
    matching = [path for path in child_candidates if (path / "specs" / "test_matrix.csv").exists()]
    if len(matching) == 1:
        return matching[0], []
    if not candidate.exists():
        return None, ["pack_root does not exist."]
    return None, ["pack_root must point to the extracted API audit pack root or its single parent directory."]


def _repo_safe_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _read_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except json.JSONDecodeError as exc:
        return None, f"{path.name}: invalid JSON: {exc.msg}"
    except OSError as exc:
        return None, f"{path.name}: cannot read JSON: {exc}"


def _blocked_report(generated_at_utc: str | None, reasons: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "task_id": TASK_ID,
        "mode": "NON_AUTONOMOUS",
        "tool_name": TOOL_NAME,
        "overall_status": "blocked",
        "evidence_status": "unknown",
        "production_safety_classification": "PROD_SAFE_OFFLINE_WITH_LOCAL_QUARANTINE_INPUT",
        "blocked_reasons": sorted(set(reasons)),
        "runtime_execution_status": "not_run",
        "live_api_execution_status": "not_run",
        "public_safety": {key: False for key in sorted(FORBIDDEN_PUBLIC_FLAGS)},
    }


def _inventory_item_ids(pack_root: Path) -> tuple[set[str], Counter[str], list[str]]:
    inventory = pack_root / "specs" / "api_inventory.yaml"
    ids: set[str] = set()
    item_types: Counter[str] = Counter()
    errors: list[str] = []
    current_id: str | None = None
    for raw_line in inventory.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if line.startswith("- id:"):
            current_id = line.split(":", 1)[1].strip()
            if not current_id:
                errors.append("api_inventory contains an empty item id.")
            elif current_id in ids:
                errors.append(f"api_inventory contains duplicate item id {current_id}.")
            else:
                ids.add(current_id)
        elif current_id and line.startswith("type:"):
            item_types.update([line.split(":", 1)[1].strip()])
    return ids, item_types, errors


def _local_pack_ref_error(pack_root: Path, reference: str, *, allowed_prefix: str, label: str) -> str | None:
    if "\\" in reference:
        return f"{label} reference must use POSIX separators."
    ref_path = Path(reference)
    if ref_path.is_absolute():
        return f"{label} reference must be relative to pack root."
    if not reference.startswith(allowed_prefix):
        return f"{label} reference must stay under {allowed_prefix.rstrip('/')}."
    if any(part in {"", ".", ".."} for part in ref_path.parts):
        return f"{label} reference must not contain traversal segments."
    try:
        resolved_root = pack_root.resolve()
        resolved_ref = (pack_root / ref_path).resolve()
        resolved_ref.relative_to(resolved_root)
    except (OSError, ValueError):
        return f"{label} reference must resolve inside pack root."
    if not resolved_ref.is_file():
        return f"{label} reference points to a missing file."
    return None


def _analyze_matrix(pack_root: Path) -> MatrixAnalysis:
    matrix_path = pack_root / "specs" / "test_matrix.csv"
    errors: list[str] = []
    try:
        with matrix_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            columns = set(reader.fieldnames or [])
    except OSError as exc:
        return MatrixAnalysis([], [f"test_matrix.csv cannot be read: {exc}"], Counter(), Counter(), Counter(), Counter(), Counter(), [])

    missing = sorted(REQUIRED_MATRIX_COLUMNS - columns)
    if missing:
        errors.append(f"test_matrix.csv missing columns: {missing}.")

    seen_test_ids: set[str] = set()
    fixture_refs: list[str] = []
    counts_by_layer: Counter[str] = Counter()
    counts_by_priority: Counter[str] = Counter()
    counts_by_test_type: Counter[str] = Counter()
    counts_by_target: Counter[str] = Counter()
    counts_by_status: Counter[str] = Counter()
    for index, row in enumerate(rows, start=2):
        test_id = row.get("test_id", "").strip()
        if not test_id:
            errors.append(f"test_matrix.csv row {index} has empty test_id.")
        elif test_id in seen_test_ids:
            errors.append(f"test_matrix.csv duplicate test_id {test_id}.")
        seen_test_ids.add(test_id)

        layer = row.get("layer", "").strip()
        priority = row.get("priority", "").strip()
        test_type = row.get("test_type", "").strip()
        target = row.get("automation_target", "").strip()
        status = row.get("status", "").strip()
        parallelization = row.get("parallelization", "").strip()
        fixture_ref = row.get("fixture_or_sequence", "").strip()

        counts_by_layer.update([layer])
        counts_by_priority.update([priority])
        counts_by_test_type.update([test_type])
        counts_by_target.update([target])
        counts_by_status.update([status])

        if layer not in ALLOWED_LAYERS:
            errors.append(f"test_matrix.csv row {index} has unsupported layer.")
        if priority not in ALLOWED_PRIORITIES:
            errors.append(f"test_matrix.csv row {index} has unsupported priority.")
        if status not in ALLOWED_MATRIX_STATUSES:
            errors.append(f"test_matrix.csv row {index} has unsupported status.")
        if parallelization not in ALLOWED_PARALLELIZATION:
            errors.append(f"test_matrix.csv row {index} is not independent_api_layer.")
        if fixture_ref:
            fixture_refs.append(fixture_ref)
            if status == "deferred_not_blocking_this_run":
                fixture_error = _local_pack_ref_error(
                    pack_root,
                    fixture_ref,
                    allowed_prefix="templates/",
                    label="deferred template",
                )
            else:
                fixture_error = _local_pack_ref_error(
                    pack_root,
                    fixture_ref,
                    allowed_prefix="fixtures/",
                    label="fixture/sequence",
                )
            if fixture_error:
                errors.append(f"test_matrix.csv row {index} has invalid pack reference: {fixture_error}")

    return MatrixAnalysis(
        rows=rows,
        errors=errors,
        counts_by_layer=counts_by_layer,
        counts_by_priority=counts_by_priority,
        counts_by_test_type=counts_by_test_type,
        counts_by_target=counts_by_target,
        counts_by_status=counts_by_status,
        fixture_refs=fixture_refs,
    )


def _analyze_json_files(pack_root: Path, folder_name: str) -> dict[str, Any]:
    folder = pack_root / folder_name
    files = sorted(folder.rglob("*.json"))
    errors: list[str] = []
    group_counts: Counter[str] = Counter()
    empty_files = 0
    valid_files = 0
    for path in files:
        rel = path.relative_to(folder)
        group = rel.parts[0] if len(rel.parts) > 1 else path.parent.name
        group_counts.update([group])
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            empty_files += 1
            errors.append(f"{folder_name}/{_repo_safe_path(folder, path)} is empty.")
            continue
        _, error = _read_json(path)
        if error:
            errors.append(f"{folder_name}/{_repo_safe_path(folder, path)} is not valid JSON.")
        else:
            valid_files += 1
    return {
        "total_json_files": len(files),
        "valid_json_files": valid_files,
        "empty_json_files": empty_files,
        "counts_by_group": dict(sorted(group_counts.items())),
        "errors": errors,
    }


def _analyze_schema_shapes(pack_root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((pack_root / "schemas").rglob("*.json")):
        loaded, error = _read_json(path)
        if error:
            continue
        if not isinstance(loaded, dict):
            errors.append(f"schema {path.name} must be a JSON object.")
            continue
        if "$schema" not in loaded:
            errors.append(f"schema {path.name} is missing $schema.")
        if "title" not in loaded:
            errors.append(f"schema {path.name} is missing title.")
        if "type" not in loaded:
            errors.append(f"schema {path.name} is missing top-level type.")
    return errors


def _scan_raw_pack_signals(pack_root: Path) -> dict[str, Any]:
    categories = {
        "url_like": URL_RE,
        "endpoint_path_like": ENDPOINT_PATH_RE,
        "secret_keyword_like": SECRET_RE,
        "payment_keyword_like": PAYMENT_RE,
        "device_identifier_keyword_like": DEVICE_RE,
        "local_path_like": LOCAL_PATH_RE,
    }
    counts: Counter[str] = Counter()
    file_group_counts: Counter[str] = Counter()
    text_extensions = {".csv", ".json", ".md", ".py", ".txt", ".yaml", ".yml"}
    for path in sorted(pack_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in text_extensions:
            continue
        rel = path.relative_to(pack_root)
        group = rel.parts[0] if rel.parts else "root"
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        matched_any = False
        for category, pattern in categories.items():
            if pattern.search(text):
                counts.update([category])
                matched_any = True
        if matched_any:
            file_group_counts.update([group])
    return {
        "raw_value_signal_categories": dict(sorted(counts.items())),
        "file_groups_with_raw_value_signals": dict(sorted(file_group_counts.items())),
        "classification": "local_quarantine_required",
    }


def _public_safety_findings(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            findings.extend(_public_safety_findings(child, f"{path}.{key}"))
        return findings
    if isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_public_safety_findings(child, f"{path}[{index}]"))
        return findings
    if not isinstance(value, str) or not value:
        return findings
    if RAW_URL_OR_ENDPOINT_RE.search(value):
        findings.append(f"{path} contains a raw URL or endpoint-like value.")
    if LOCAL_PATH_RE.search(value):
        findings.append(f"{path} contains a raw local path.")
    if HEX_HASH_RE.search(value):
        findings.append(f"{path} contains a raw hash-like value.")
    if SECRET_RE.search(value) and re.search(r"[:=]\s*\S+", value):
        findings.append(f"{path} contains a secret-like key/value.")
    return findings


def build_report(pack_root: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    normalized_pack_root, root_errors = _normalize_pack_root(pack_root)
    if normalized_pack_root is None:
        return _blocked_report(generated_at_utc, root_errors)

    errors: list[str] = []
    for required_dir in REQUIRED_PACK_DIRS:
        if not (normalized_pack_root / required_dir).is_dir():
            errors.append(f"required pack directory {required_dir} is missing.")
    for required_file in REQUIRED_PACK_FILES:
        if not (normalized_pack_root / required_file).is_file():
            errors.append(f"required pack file {required_file} is missing.")
    if errors:
        return _blocked_report(generated_at_utc, errors)

    matrix = _analyze_matrix(normalized_pack_root)
    inventory_ids, inventory_types, inventory_errors = _inventory_item_ids(normalized_pack_root)
    fixture_analysis = _analyze_json_files(normalized_pack_root, "fixtures")
    schema_analysis = _analyze_json_files(normalized_pack_root, "schemas")
    schema_shape_errors = _analyze_schema_shapes(normalized_pack_root)
    raw_signal_summary = _scan_raw_pack_signals(normalized_pack_root)

    errors.extend(matrix.errors)
    errors.extend(inventory_errors)
    errors.extend(fixture_analysis["errors"])
    errors.extend(schema_analysis["errors"])
    errors.extend(schema_shape_errors)

    inventory_link_required_layers = {"rest"}
    matrix_items = {
        row.get("item", "").strip()
        for row in matrix.rows
        if row.get("item", "").strip() and row.get("layer", "").strip() in inventory_link_required_layers
    }
    missing_inventory_items = sorted(item for item in matrix_items if item and item not in inventory_ids)
    if missing_inventory_items:
        errors.append(f"test_matrix references items missing from api_inventory: {missing_inventory_items[:10]}.")

    fixture_groups = set(fixture_analysis["counts_by_group"])
    schema_groups = set(schema_analysis["counts_by_group"])
    missing_fixture_groups = sorted(EXPECTED_FIXTURE_GROUPS - fixture_groups)
    missing_schema_groups = sorted(EXPECTED_SCHEMA_GROUPS - schema_groups)
    if missing_fixture_groups:
        errors.append(f"fixtures missing expected groups: {missing_fixture_groups}.")
    if missing_schema_groups:
        errors.append(f"schemas missing expected groups: {missing_schema_groups}.")
    if matrix.counts_by_status.get("deferred_not_blocking_this_run", 0) != RUNTIME_OPTIONAL_EXPECTED_COUNT:
        errors.append("runtime_optional deferred count does not match the TASK-028 expected boundary count.")

    public_safety = {key: False for key in sorted(FORBIDDEN_PUBLIC_FLAGS)}
    public_safety["raw_pack_signals_detected_in_local_quarantine"] = bool(raw_signal_summary["raw_value_signal_categories"])
    public_safety["public_report_contains_only_aliases_counts_and_categories"] = True

    blocked_reasons = sorted(set(errors))
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "task_id": TASK_ID,
        "mode": "NON_AUTONOMOUS",
        "tool_name": TOOL_NAME,
        "overall_status": "pass" if not blocked_reasons else "blocked",
        "evidence_status": "likely" if not blocked_reasons else "unknown",
        "production_safety_classification": "PROD_SAFE_OFFLINE_WITH_LOCAL_QUARANTINE_INPUT",
        "source_pack": {
            "source_alias": "api-layer-audit-pack-20260706",
            "raw_archive_location": "local_only_not_committed",
            "raw_pack_storage": "ignored_local_quarantine",
            "raw_values_public": False,
            "evidence_status": "likely",
        },
        "runtime_execution_status": "not_run",
        "live_api_execution_status": "not_run",
        "backend_environment_status": "not_configured",
        "archive_intake": {
            "required_files_present": all((normalized_pack_root / path).exists() for path in REQUIRED_PACK_FILES),
            "matrix_rows": len(matrix.rows),
            "inventory_items": len(inventory_ids),
            "schema_json_files": schema_analysis["total_json_files"],
            "fixture_json_files": fixture_analysis["total_json_files"],
            "fixture_or_sequence_refs": len(matrix.fixture_refs),
            "missing_fixture_refs": 0 if not matrix.errors else "see_blocked_reasons",
        },
        "coverage_summary": {
            "counts_by_layer": dict(sorted(matrix.counts_by_layer.items())),
            "counts_by_priority": dict(sorted(matrix.counts_by_priority.items())),
            "counts_by_test_type": dict(sorted(matrix.counts_by_test_type.items())),
            "counts_by_automation_target": dict(sorted(matrix.counts_by_target.items())),
            "counts_by_status": dict(sorted(matrix.counts_by_status.items())),
            "inventory_types": dict(sorted(inventory_types.items())),
            "fixture_groups": fixture_analysis["counts_by_group"],
            "schema_groups": schema_analysis["counts_by_group"],
        },
        "coverage_contract": {
            "exhaustive_scope": "all_known_rows_fixtures_and_schema_files_in_quarantined_pack",
            "live_api_surface_status": "unknown_until_separate_approved_task",
            "ui_runtime_scope": "parallel_ui_coverage_not_duplicated",
            "payment_stream_mutation_scope": "not_run_blocked_without_separate_approval",
            "raw_endpoint_publication": "forbidden",
        },
        "raw_pack_signal_summary": raw_signal_summary,
        "follow_up_task_decomposition": FOLLOW_UP_TASKS,
        "public_safety": public_safety,
        "blocked_reasons": blocked_reasons,
        "unverified_areas": [
            "live REST backend behavior",
            "live STOMP/WebSocket behavior",
            "live WebRTC/DataChannel behavior",
            "real payment/order/session mutations",
            "backend authorization and ACL enforcement",
            "runtime correlation with Android app evidence",
        ],
    }
    return report


def validate_public_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "generated_at_utc",
        "task_id",
        "mode",
        "overall_status",
        "runtime_execution_status",
        "live_api_execution_status",
        "coverage_summary",
        "coverage_contract",
        "public_safety",
        "blocked_reasons",
    }
    missing = sorted(required - set(report))
    if missing:
        errors.append(f"report missing required fields: {missing}.")
    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}.")
    if report.get("task_id") != TASK_ID:
        errors.append("task_id must be TASK-028.")
    if report.get("mode") != "NON_AUTONOMOUS":
        errors.append("mode must be NON_AUTONOMOUS.")
    if report.get("runtime_execution_status") != "not_run":
        errors.append("runtime_execution_status must be not_run.")
    if report.get("live_api_execution_status") != "not_run":
        errors.append("live_api_execution_status must be not_run.")
    public_safety = report.get("public_safety")
    if not isinstance(public_safety, dict):
        errors.append("public_safety must be an object.")
    else:
        for flag in sorted(FORBIDDEN_PUBLIC_FLAGS):
            if public_safety.get(flag) is not False:
                errors.append(f"public_safety.{flag} must be false.")
        if public_safety.get("public_report_contains_only_aliases_counts_and_categories") is not True:
            errors.append("public_safety.public_report_contains_only_aliases_counts_and_categories must be true.")
    errors.extend(_public_safety_findings(report))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TASK-028 API-layer contract coverage intake.")
    parser.add_argument("--pack-root", type=Path, required=True, help="Extracted local-only API audit pack root.")
    parser.add_argument("--report", type=Path, help="Optional public-safe summary JSON output path.")
    args = parser.parse_args(argv)

    report = build_report(args.pack_root)
    report_errors = validate_public_report(report)
    if report_errors:
        report["overall_status"] = "blocked"
        report["blocked_reasons"] = sorted(set(report.get("blocked_reasons", [])) | set(report_errors))

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "validation_status": "pass" if report["overall_status"] == "pass" and not report_errors else "blocked",
        "report_path": args.report.as_posix() if args.report else None,
        "matrix_rows": report.get("archive_intake", {}).get("matrix_rows"),
        "fixture_json_files": report.get("archive_intake", {}).get("fixture_json_files"),
        "schema_json_files": report.get("archive_intake", {}).get("schema_json_files"),
        "blocked_reasons": report.get("blocked_reasons", []),
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if result["validation_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
