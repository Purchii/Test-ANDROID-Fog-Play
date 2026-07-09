"""Validate TASK-029 REST schema/fixture contracts offline.

This harness is intentionally local/offline only. It can read an ignored
quarantine API-layer audit pack when the owner-provided pack is present, but it
emits only public-safe aliases, counts, statuses and blocker ids. It never
performs live HTTP, backend, Android runtime, ADB, APK or WebRTC actions.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from automation.api_layer_contract.validate_task028_api_layer_contract import (
    build_report as build_task028_pack_report,
)
from automation.api_layer_contract.validate_task028_api_layer_contract import (
    validate_public_report as validate_task028_public_report,
)
from automation.api_layer_contract.validate_task036_api_layer_exhaustive_coverage import (
    validate_public_report as validate_task036_public_report,
)


TASK_ID = "TASK-029"
SCHEMA_VERSION = "task029-rest-schema-fixture-contracts-v1"
TOOL_NAME = "validate_task029_rest_schema_fixture_contracts"
DEFAULT_TASK028_REPORT = Path("docs/qa/reports/task028_api_layer_contract_coverage.summary.json")
DEFAULT_TASK036_REPORT = Path("docs/qa/reports/task036_api_layer_exhaustive_coverage.summary.json")

REST_CONTRACT_TARGETS = {"fixture_schema_test", "fixture_schema_negative_test", "mock_or_fixture_test"}
REST_FIXTURE_PREFIXES = {"fixtures/rest/", "fixtures/gamepad/"}
REQUIRED_REST_SCHEMA_KEYS = {"$schema", "title", "type"}

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
    "raw_account_values_public",
    "raw_local_paths_public",
    "live_network_calls_performed",
    "live_backend_calls_performed",
    "websocket_or_datachannel_connections_performed",
    "adb_or_android_runtime_actions_performed",
    "apk_read_install_or_modification_performed",
    "real_payment_or_session_mutation_performed",
    "tls_or_security_bypass_performed",
}

RAW_PUBLIC_TEXT_RE = re.compile(
    r"\b(?:https?|wss?)://|"
    r"(?<![\w-])/(?:api|log|ws|socket|stomp|payment|billing|order|profile|auth|login|content)[/\w{}.,:@?=&%-]*|"
    r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])|"
    r"\b[a-fA-F0-9]{64}\b|"
    r"\b(?:authorization|bearer|cookie|session|token|secret|password|api[_-]?key|otp|captcha)[:=]\s*\S+|"
    r"\b(?:device[_-]?id|android[_-]?id|serial|imei|imsi|mac|account|payment|card|invoice|receipt)[_-]?"
    r"(?:id|number|value|token)?[:=]\s*\S+",
    re.IGNORECASE,
)

PACK_RAW_SIGNAL_PATTERNS = {
    "url_like": re.compile(r"\b(?:https?|wss?)://", re.IGNORECASE),
    "endpoint_path_like": re.compile(
        r"(?<![\w-])/(?:api|log|ws|socket|stomp|payment|billing|order|profile|auth|login|content)[/\w{}.,:@?=&%-]*",
        re.IGNORECASE,
    ),
    "secret_keyword_like": re.compile(
        r"\b(?:authorization|bearer|cookie|session|token|secret|password|api[_-]?key|otp|captcha)\b",
        re.IGNORECASE,
    ),
    "payment_or_account_keyword_like": re.compile(r"\b(?:payment|billing|card|receipt|invoice|account)\b", re.IGNORECASE),
    "device_identifier_keyword_like": re.compile(r"\b(?:device[_-]?id|android[_-]?id|serial|imei|imsi|mac)\b", re.IGNORECASE),
    "local_path_like": re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])", re.IGNORECASE),
}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json_object(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}, [f"{label}_json_malformed"]
    except OSError:
        return {}, [f"{label}_json_unreadable"]
    if not isinstance(loaded, dict):
        return {}, [f"{label}_json_not_object"]
    return loaded, []


def _normalize_pack_root(pack_root: Path) -> tuple[Path | None, list[str]]:
    if not pack_root.exists():
        return None, ["blocked_missing_local_quarantine_pack"]
    candidate = pack_root.resolve()
    if (candidate / "specs" / "test_matrix.csv").is_file():
        return candidate, []
    children = [path for path in candidate.iterdir() if path.is_dir()]
    matching = [path for path in children if (path / "specs" / "test_matrix.csv").is_file()]
    if len(matching) == 1:
        return matching[0], []
    return None, ["blocked_pack_root_not_api_audit_pack"]


def _load_matrix(pack_root: Path) -> tuple[list[dict[str, str]], list[str]]:
    try:
        with (pack_root / "specs" / "test_matrix.csv").open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
            columns = set(reader.fieldnames or [])
    except OSError:
        return [], ["test_matrix_unreadable"]

    required = {"test_id", "layer", "item", "test_type", "automation_target", "fixture_or_sequence", "status"}
    missing = required - columns
    if missing:
        return rows, ["test_matrix_missing_required_columns"]
    return rows, []


def _inventory_rest_items(pack_root: Path) -> tuple[set[str], list[str]]:
    try:
        lines = (pack_root / "specs" / "api_inventory.yaml").read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return set(), ["api_inventory_unreadable"]

    item_types: dict[str, str] = {}
    current_id: str | None = None
    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("- id:"):
            current_id = line.split(":", 1)[1].strip()
        elif current_id and line.startswith("type:"):
            item_types[current_id] = line.split(":", 1)[1].strip()
            current_id = None
    return {item_id for item_id, item_type in item_types.items() if item_type == "rest"}, []


def _safe_ref_error(reference: str, allowed_prefixes: set[str]) -> str | None:
    if not reference:
        return "rest_fixture_reference_empty"
    if "\\" in reference:
        return "rest_fixture_reference_uses_non_posix_separator"
    path = Path(reference)
    if path.is_absolute():
        return "rest_fixture_reference_absolute"
    if any(part in {"", ".", ".."} for part in path.parts):
        return "rest_fixture_reference_traversal"
    if not any(reference.startswith(prefix) for prefix in allowed_prefixes):
        return "rest_fixture_reference_unapproved_group"
    return None


def _load_json_file(path: Path, blocker: str) -> list[str]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return [blocker]
    except OSError:
        return [blocker]
    if loaded is None:
        return [blocker]
    return []


def _schema_shape_errors(schema_path: Path) -> list[str]:
    try:
        loaded = json.loads(schema_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return ["rest_schema_json_malformed"]
    except OSError:
        return ["rest_schema_unreadable"]
    if not isinstance(loaded, dict):
        return ["rest_schema_not_object"]
    missing = REQUIRED_REST_SCHEMA_KEYS - set(loaded)
    errors: list[str] = []
    if missing:
        errors.append("rest_schema_missing_required_keys")
    if loaded.get("type") not in {"object", "array", "boolean", "integer", "number", "string", "null"}:
        errors.append("rest_schema_top_level_type_unsupported")
    return errors


def _scan_pack_raw_signal_categories(pack_root: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    text_extensions = {".csv", ".json", ".md", ".txt", ".yaml", ".yml"}
    for path in sorted(pack_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in text_extensions:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for category, pattern in PACK_RAW_SIGNAL_PATTERNS.items():
            if pattern.search(text):
                counts.update([category])
    return dict(sorted(counts.items()))


def _analyze_pack(pack_root: Path) -> tuple[dict[str, Any], list[str]]:
    normalized, normalize_errors = _normalize_pack_root(pack_root)
    if normalized is None:
        return {
            "status": "blocked_missing_local_quarantine_pack"
            if "blocked_missing_local_quarantine_pack" in normalize_errors
            else "blocked_pack_root_not_api_audit_pack",
            "evidence_status": "unknown",
            "raw_pack_storage": "ignored_local_quarantine",
            "raw_values_public": False,
        }, normalize_errors

    task028_pack_report = build_task028_pack_report(normalized)
    task028_pack_errors = validate_task028_public_report(task028_pack_report)
    if task028_pack_report.get("overall_status") != "pass":
        task028_pack_errors.extend(task028_pack_report.get("blocked_reasons", []))

    rows, matrix_errors = _load_matrix(normalized)
    rest_items, inventory_errors = _inventory_rest_items(normalized)
    errors: list[str] = list(task028_pack_errors) + matrix_errors + inventory_errors

    rest_rows = [row for row in rows if row.get("layer") == "rest"]
    rest_contract_rows = [row for row in rest_rows if row.get("automation_target") in REST_CONTRACT_TARGETS]
    target_counts = Counter(row.get("automation_target", "unknown") for row in rest_rows)
    test_type_counts = Counter(row.get("test_type", "unknown") for row in rest_rows)
    status_counts = Counter(row.get("status", "unknown") for row in rest_rows)
    fixture_group_counts: Counter[str] = Counter()
    missing_refs = 0
    malformed_fixtures = 0
    invalid_refs = 0
    missing_inventory_items = 0

    for row in rest_contract_rows:
        if row.get("item") not in rest_items:
            missing_inventory_items += 1
            errors.append("rest_matrix_item_missing_from_rest_inventory")
        reference = row.get("fixture_or_sequence", "")
        ref_error = _safe_ref_error(reference, REST_FIXTURE_PREFIXES)
        if ref_error:
            invalid_refs += 1
            errors.append(ref_error)
            continue
        fixture_group_counts.update([Path(reference).parts[1]])
        fixture_path = normalized / Path(reference)
        try:
            fixture_path.resolve().relative_to(normalized)
        except ValueError:
            invalid_refs += 1
            errors.append("rest_fixture_reference_resolves_outside_pack")
            continue
        if not fixture_path.is_file():
            missing_refs += 1
            errors.append("rest_fixture_reference_missing")
            continue
        fixture_errors = _load_json_file(fixture_path, "rest_fixture_json_malformed")
        if fixture_errors:
            malformed_fixtures += 1
            errors.extend(fixture_errors)

    rest_schema_files = sorted((normalized / "schemas" / "rest").glob("*.json"))
    malformed_schemas = 0
    for schema_path in rest_schema_files:
        schema_errors = _schema_shape_errors(schema_path)
        if schema_errors:
            malformed_schemas += 1
            errors.extend(schema_errors)

    raw_signal_categories = _scan_pack_raw_signal_categories(normalized)
    analysis = {
        "status": "pass" if not errors else "blocked_pack_contract_validation_failed",
        "evidence_status": "likely" if not errors else "unknown",
        "raw_pack_storage": "ignored_local_quarantine",
        "raw_values_public": False,
        "source_alias": "api-layer-audit-pack-20260706",
        "rest_matrix_rows": len(rest_rows),
        "rest_contract_rows": len(rest_contract_rows),
        "rest_fixture_refs_checked": len(rest_contract_rows),
        "rest_fixture_refs_missing": missing_refs,
        "rest_fixture_refs_invalid": invalid_refs,
        "rest_fixture_json_malformed": malformed_fixtures,
        "rest_schema_json_files": len(rest_schema_files),
        "rest_schema_json_malformed_or_invalid": malformed_schemas,
        "rest_inventory_item_mismatches": missing_inventory_items,
        "counts_by_rest_automation_target": dict(sorted(target_counts.items())),
        "counts_by_rest_test_type": dict(sorted(test_type_counts.items())),
        "counts_by_rest_status": dict(sorted(status_counts.items())),
        "rest_fixture_groups_checked": dict(sorted(fixture_group_counts.items())),
        "raw_pack_signal_categories": raw_signal_categories,
    }
    return analysis, sorted(set(errors))


def _sum_count_map(value: Any) -> int | None:
    if not isinstance(value, Mapping):
        return None
    total = 0
    for count in value.values():
        if not isinstance(count, int) or count < 0:
            return None
        total += count
    return total


def _validate_task028_summary(summary: dict[str, Any]) -> list[str]:
    errors = list(validate_task028_public_report(summary))
    if summary.get("task_id") != "TASK-028":
        errors.append("task028_summary_task_id_invalid")
    if summary.get("overall_status") != "pass":
        errors.append("task028_summary_not_pass")
    if summary.get("runtime_execution_status") != "not_run":
        errors.append("task028_runtime_status_not_not_run")
    if summary.get("live_api_execution_status") != "not_run":
        errors.append("task028_live_api_status_not_not_run")

    archive = summary.get("archive_intake", {})
    coverage = summary.get("coverage_summary", {})
    matrix_rows = archive.get("matrix_rows") if isinstance(archive, dict) else None
    if not isinstance(matrix_rows, int) or matrix_rows <= 0:
        errors.append("task028_matrix_rows_invalid")
        matrix_rows = None
    if isinstance(coverage, dict) and matrix_rows is not None:
        for field_name in ("counts_by_layer", "counts_by_automation_target", "counts_by_test_type", "counts_by_status"):
            total = _sum_count_map(coverage.get(field_name))
            if total != matrix_rows:
                errors.append(f"task028_{field_name}_total_mismatch")
    return sorted(set(errors))


def _task036_task029_area(summary: dict[str, Any]) -> dict[str, Any] | None:
    ledger = summary.get("coverage_area_ledger")
    if not isinstance(ledger, list):
        return None
    for item in ledger:
        if isinstance(item, dict) and item.get("source_task") == TASK_ID:
            return item
    return None


def _validate_task036_summary(summary: dict[str, Any], task028_summary: dict[str, Any]) -> list[str]:
    errors = list(validate_task036_public_report(summary))
    if summary.get("task_id") != "TASK-036":
        errors.append("task036_summary_task_id_invalid")
    if summary.get("overall_status") not in {"pass", "partial_blocked"}:
        errors.append("task036_summary_status_not_usable")
    if summary.get("runtime_execution_status") != "not_run":
        errors.append("task036_runtime_status_not_not_run")
    if summary.get("live_api_execution_status") != "not_run":
        errors.append("task036_live_api_status_not_not_run")

    area = _task036_task029_area(summary)
    if area is None:
        errors.append("task036_task029_ledger_area_missing")
        return sorted(set(errors))

    coverage = task028_summary.get("coverage_summary", {})
    if not isinstance(coverage, dict):
        errors.append("task028_coverage_summary_invalid")
        return sorted(set(errors))
    layer_counts = coverage.get("counts_by_layer", {})
    target_counts = coverage.get("counts_by_automation_target", {})
    if area.get("known_matrix_rows") != layer_counts.get("rest"):
        errors.append("task036_task029_rest_row_count_mismatch")
    if area.get("known_fixture_schema_tests") != target_counts.get("fixture_schema_test"):
        errors.append("task036_task029_positive_fixture_count_mismatch")
    if area.get("known_negative_fixture_schema_tests") != target_counts.get("fixture_schema_negative_test"):
        errors.append("task036_task029_negative_fixture_count_mismatch")
    return sorted(set(errors))


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
    if isinstance(value, str) and RAW_PUBLIC_TEXT_RE.search(value):
        findings.append(f"{path} contains raw API/private/local evidence-like text.")
    return findings


def _compare_pack_to_task028(pack_contract: dict[str, Any], task028_summary: dict[str, Any]) -> list[str]:
    if pack_contract.get("status") != "pass":
        return []
    coverage = task028_summary.get("coverage_summary", {})
    if not isinstance(coverage, dict):
        return ["task028_coverage_summary_invalid"]
    layer_counts = coverage.get("counts_by_layer", {})
    target_counts = coverage.get("counts_by_automation_target", {})
    schema_groups = coverage.get("schema_groups", {})
    errors: list[str] = []
    if pack_contract.get("rest_matrix_rows") != layer_counts.get("rest"):
        errors.append("pack_rest_row_count_mismatch_with_task028")
    expected_contract_rows = target_counts.get("fixture_schema_test", 0) + target_counts.get("fixture_schema_negative_test", 0)
    if pack_contract.get("counts_by_rest_automation_target", {}).get("fixture_schema_test", 0) + pack_contract.get(
        "counts_by_rest_automation_target", {}
    ).get("fixture_schema_negative_test", 0) != expected_contract_rows:
        errors.append("pack_rest_fixture_schema_target_count_mismatch_with_task028")
    if pack_contract.get("rest_schema_json_files") != schema_groups.get("rest"):
        errors.append("pack_rest_schema_count_mismatch_with_task028")
    return errors


def build_report(
    task028_report_path: Path = DEFAULT_TASK028_REPORT,
    task036_report_path: Path = DEFAULT_TASK036_REPORT,
    pack_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    task028_summary, task028_load_errors = _read_json_object(task028_report_path, "task028_summary")
    task036_summary, task036_load_errors = _read_json_object(task036_report_path, "task036_summary")

    summary_errors = task028_load_errors + task036_load_errors
    if not task028_load_errors:
        summary_errors.extend(_validate_task028_summary(task028_summary))
    if not task036_load_errors and not task028_load_errors:
        summary_errors.extend(_validate_task036_summary(task036_summary, task028_summary))

    if pack_root is None:
        pack_contract = {
            "status": "blocked_pack_root_not_provided",
            "evidence_status": "unknown",
            "raw_pack_storage": "ignored_local_quarantine",
            "raw_values_public": False,
        }
        pack_errors = ["blocked_pack_root_not_provided"]
    else:
        pack_contract, pack_errors = _analyze_pack(pack_root)
        if not task028_load_errors:
            pack_errors.extend(_compare_pack_to_task028(pack_contract, task028_summary))

    if summary_errors:
        overall_status = "blocked"
        evidence_status = "unknown"
    elif pack_errors and set(pack_errors) <= {"blocked_pack_root_not_provided", "blocked_missing_local_quarantine_pack"}:
        overall_status = "partial_blocked"
        evidence_status = "likely_with_blockers"
    elif pack_errors:
        overall_status = "blocked"
        evidence_status = "unknown"
    else:
        overall_status = "pass"
        evidence_status = "likely"

    coverage = task028_summary.get("coverage_summary", {}) if isinstance(task028_summary, dict) else {}
    archive = task028_summary.get("archive_intake", {}) if isinstance(task028_summary, dict) else {}
    targets = coverage.get("counts_by_automation_target", {}) if isinstance(coverage, dict) else {}
    layers = coverage.get("counts_by_layer", {}) if isinstance(coverage, dict) else {}
    schema_groups = coverage.get("schema_groups", {}) if isinstance(coverage, dict) else {}
    fixture_groups = coverage.get("fixture_groups", {}) if isinstance(coverage, dict) else {}
    task036_area = _task036_task029_area(task036_summary) if isinstance(task036_summary, dict) else None

    public_safety = {key: False for key in sorted(FORBIDDEN_PUBLIC_FLAGS)}
    public_safety.update(
        {
            "public_report_contains_only_aliases_counts_categories_status_and_blockers": True,
            "raw_pack_content_read_from_public_repo": False,
            "local_quarantine_pack_required_for_pack_backed_parametrization": True,
            "pack_raw_signal_categories_are_counted_only": True,
        }
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "task_id": TASK_ID,
        "mode": "BOUNDED_AUTONOMOUS",
        "tool_name": TOOL_NAME,
        "overall_status": overall_status,
        "evidence_status": evidence_status,
        "production_safety_classification": "PROD_SAFE_OFFLINE_WITH_LOCAL_QUARANTINE_INPUT",
        "runtime_execution_status": "not_run",
        "live_api_execution_status": "not_run",
        "network_execution_status": "not_run",
        "android_runtime_status": "not_run",
        "source_summaries": {
            "task028": {
                "source_report_alias": "task028_api_layer_contract_coverage_summary",
                "status": task028_summary.get("overall_status", "unknown") if task028_summary else "unknown",
                "evidence_status": task028_summary.get("evidence_status", "unknown") if task028_summary else "unknown",
                "matrix_rows": archive.get("matrix_rows") if isinstance(archive, dict) else None,
                "rest_matrix_rows": layers.get("rest") if isinstance(layers, dict) else None,
                "fixture_schema_tests": targets.get("fixture_schema_test") if isinstance(targets, dict) else None,
                "fixture_schema_negative_tests": targets.get("fixture_schema_negative_test") if isinstance(targets, dict) else None,
                "rest_schema_json_files": schema_groups.get("rest") if isinstance(schema_groups, dict) else None,
                "rest_fixture_json_files": fixture_groups.get("rest") if isinstance(fixture_groups, dict) else None,
            },
            "task036": {
                "source_report_alias": "task036_api_layer_exhaustive_coverage_summary",
                "status": task036_summary.get("overall_status", "unknown") if task036_summary else "unknown",
                "evidence_status": task036_summary.get("evidence_status", "unknown") if task036_summary else "unknown",
                "task029_ledger_status": task036_area.get("status") if isinstance(task036_area, dict) else "unknown",
            },
        },
        "rest_contract_summary": {
            "known_rest_matrix_rows": layers.get("rest") if isinstance(layers, dict) else None,
            "known_rest_fixture_schema_contract_targets": {
                "fixture_schema_test": targets.get("fixture_schema_test") if isinstance(targets, dict) else None,
                "fixture_schema_negative_test": targets.get("fixture_schema_negative_test") if isinstance(targets, dict) else None,
                "mock_or_fixture_test": targets.get("mock_or_fixture_test") if isinstance(targets, dict) else None,
            },
            "known_rest_schema_group_count": schema_groups.get("rest") if isinstance(schema_groups, dict) else None,
            "known_rest_fixture_group_count": fixture_groups.get("rest") if isinstance(fixture_groups, dict) else None,
            "known_gamepad_fixture_group_count": fixture_groups.get("gamepad") if isinstance(fixture_groups, dict) else None,
            "source_reconciliation_status": "pass" if not summary_errors else "blocked",
        },
        "pack_contract": pack_contract,
        "offline_execution_boundary": {
            "live_rest_backend_calls": "not_run",
            "websocket_stomp_connections": "not_run",
            "webrtc_datachannel_connections": "not_run",
            "android_adb_runtime_actions": "not_run",
            "apk_read_install_or_modification": "not_run",
            "transport_strategy": "local_filesystem_json_only",
        },
        "public_safety": public_safety,
        "blocked_reasons": sorted(set(summary_errors + pack_errors)),
        "unverified_areas": [
            "live REST backend behavior",
            "backend authorization and ACL enforcement",
            "cache behavior against a real backend",
            "real payment order session mutation behavior",
            "Android runtime correlation with API-layer evidence",
        ],
    }

    report_errors = validate_public_report(report)
    if report_errors:
        report["overall_status"] = "blocked"
        report["evidence_status"] = "unknown"
        report["blocked_reasons"] = sorted(set(report["blocked_reasons"]) | set(report_errors))
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
        "network_execution_status",
        "public_safety",
        "blocked_reasons",
    }
    missing = sorted(required - set(report))
    if missing:
        errors.append(f"report_missing_required_fields:{','.join(missing)}")
    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if report.get("task_id") != TASK_ID:
        errors.append("task_id_invalid")
    if report.get("mode") != "BOUNDED_AUTONOMOUS":
        errors.append("mode_invalid")
    if report.get("overall_status") not in {"pass", "partial_blocked", "blocked"}:
        errors.append("overall_status_invalid")
    for field_name in ("runtime_execution_status", "live_api_execution_status", "network_execution_status"):
        if report.get(field_name) != "not_run":
            errors.append(f"{field_name}_must_be_not_run")

    public_safety = report.get("public_safety")
    if not isinstance(public_safety, dict):
        errors.append("public_safety_not_object")
    else:
        for flag in sorted(FORBIDDEN_PUBLIC_FLAGS):
            if public_safety.get(flag) is not False:
                errors.append(f"public_safety_{flag}_must_be_false")
        if public_safety.get("public_report_contains_only_aliases_counts_categories_status_and_blockers") is not True:
            errors.append("public_report_scope_flag_missing")

    boundary = report.get("offline_execution_boundary")
    if not isinstance(boundary, dict):
        errors.append("offline_execution_boundary_not_object")
    elif any(value != "not_run" for key, value in boundary.items() if key != "transport_strategy"):
        errors.append("offline_execution_boundary_contains_executed_action")

    errors.extend(_public_safety_findings(report))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TASK-029 REST schema/fixture contracts offline.")
    parser.add_argument("--task028-report", type=Path, default=DEFAULT_TASK028_REPORT, help="Tracked TASK-028 public summary.")
    parser.add_argument("--task036-report", type=Path, default=DEFAULT_TASK036_REPORT, help="Tracked TASK-036 public summary.")
    parser.add_argument("--pack-root", type=Path, help="Optional ignored local API quarantine pack root.")
    parser.add_argument("--report", type=Path, help="Optional TASK-029 public-safe summary JSON output path.")
    args = parser.parse_args(argv)

    report = build_report(args.task028_report, args.task036_report, args.pack_root)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "validation_status": report["overall_status"],
        "blocked_reason_count": len(report.get("blocked_reasons", [])),
        "pack_contract_status": report.get("pack_contract", {}).get("status"),
        "known_rest_matrix_rows": report.get("rest_contract_summary", {}).get("known_rest_matrix_rows"),
        "report_alias": "task029_rest_schema_fixture_contracts_summary" if args.report else None,
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 1 if report["overall_status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
