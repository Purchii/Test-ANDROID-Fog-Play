"""Validate TASK-030 REST negative/cache/state-sequence contracts offline.

The harness is intentionally offline-only. It may read an ignored local API
audit pack, but it models REST negative/cache/sequence behavior with local JSON
fixtures only and emits public-safe aliases, counts, statuses and blockers.
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
    validate_public_report as validate_task028_public_report,
)
from automation.api_layer_contract.validate_task029_rest_schema_fixture_contracts import (
    validate_public_report as validate_task029_public_report,
)
from automation.api_layer_contract.validate_task036_api_layer_exhaustive_coverage import (
    validate_public_report as validate_task036_public_report,
)


TASK_ID = "TASK-030"
SCHEMA_VERSION = "task030-rest-negative-cache-sequences-v1"
TOOL_NAME = "validate_task030_rest_negative_cache_sequences"
DEFAULT_TASK028_REPORT = Path("docs/qa/reports/task028_api_layer_contract_coverage.summary.json")
DEFAULT_TASK029_REPORT = Path("docs/qa/reports/task029_rest_schema_fixture_contracts.summary.json")
DEFAULT_TASK036_REPORT = Path("docs/qa/reports/task036_api_layer_exhaustive_coverage.summary.json")

TASK030_TARGETS = {"mock_http_test", "mock_http_sequence_test"}
TASK030_TEST_TYPES = {
    "cache_behavior",
    "negative_auth",
    "negative_server_error",
    "sequence_positive_or_negative",
}
SEQUENCE_LAYERS = {"state_machine_sequence"}
ALLOWED_FIXTURE_PREFIXES = {"fixtures/rest/", "fixtures/sequences/"}

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
    if required - columns:
        return rows, ["test_matrix_missing_required_columns"]
    return rows, []


def _safe_ref_error(reference: str) -> str | None:
    if not reference:
        return "task030_fixture_reference_empty"
    if "\\" in reference:
        return "task030_fixture_reference_uses_non_posix_separator"
    path = Path(reference)
    if path.is_absolute():
        return "task030_fixture_reference_absolute"
    if any(part in {"", ".", ".."} for part in path.parts):
        return "task030_fixture_reference_traversal"
    if not any(reference.startswith(prefix) for prefix in ALLOWED_FIXTURE_PREFIXES):
        return "task030_fixture_reference_unapproved_group"
    return None


def _read_fixture(path: Path, sequence_required: bool) -> tuple[str, list[str]]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return "malformed", ["task030_fixture_json_malformed"]
    except OSError:
        return "unreadable", ["task030_fixture_json_unreadable"]
    if loaded is None:
        return "invalid", ["task030_fixture_json_null"]
    if sequence_required:
        if isinstance(loaded, list):
            return "sequence_list", []
        if isinstance(loaded, dict) and isinstance(loaded.get("steps"), list):
            return "sequence_steps", []
        if isinstance(loaded, dict) and isinstance(loaded.get("sequence"), list):
            return "sequence_object", []
        virtual_time_keys = {"virtual_time", "poll_interval_seconds", "timeout_seconds", "expected_terminal_state"}
        if isinstance(loaded, dict) and virtual_time_keys <= set(loaded):
            return "sequence_virtual_time", []
        return "invalid_sequence", ["task030_sequence_fixture_shape_invalid"]
    if isinstance(loaded, dict):
        return "object", []
    if isinstance(loaded, list):
        return "list", []
    return "scalar", ["task030_mock_fixture_shape_invalid"]


def _is_task030_row(row: Mapping[str, str]) -> bool:
    layer = row.get("layer", "")
    target = row.get("automation_target", "")
    test_type = row.get("test_type", "")
    return target in TASK030_TARGETS or layer in SEQUENCE_LAYERS or (layer == "rest" and test_type in TASK030_TEST_TYPES)


def _row_contract_kind(row: Mapping[str, str]) -> str:
    test_type = row.get("test_type", "")
    layer = row.get("layer", "")
    target = row.get("automation_target", "")
    if test_type == "cache_behavior":
        return "cache_behavior"
    if layer in SEQUENCE_LAYERS or target == "mock_http_sequence_test":
        return "state_sequence"
    if test_type.startswith("negative_"):
        return "negative_response"
    if test_type == "critical_edge_case":
        return "critical_edge_case"
    return "mocked_rest"


def _analyze_pack(pack_root: Path) -> tuple[dict[str, Any], list[str]]:
    normalized, normalize_errors = _normalize_pack_root(pack_root)
    if normalized is None:
        status = "blocked_missing_local_quarantine_pack" if "blocked_missing_local_quarantine_pack" in normalize_errors else "blocked_pack_root_not_api_audit_pack"
        return {
            "status": status,
            "evidence_status": "unknown",
            "raw_pack_storage": "ignored_local_quarantine",
            "raw_values_public": False,
        }, normalize_errors

    rows, matrix_errors = _load_matrix(normalized)
    errors = list(matrix_errors)
    task030_rows = [row for row in rows if _is_task030_row(row)]
    target_counts = Counter(row.get("automation_target", "unknown") for row in task030_rows)
    test_type_counts = Counter(row.get("test_type", "unknown") for row in task030_rows)
    layer_counts = Counter(row.get("layer", "unknown") for row in task030_rows)
    contract_kind_counts = Counter(_row_contract_kind(row) for row in task030_rows)
    fixture_group_counts: Counter[str] = Counter()
    fixture_shape_counts: Counter[str] = Counter()
    missing_refs = 0
    invalid_refs = 0
    malformed_fixtures = 0
    sequence_shape_invalid = 0

    for row in task030_rows:
        reference = row.get("fixture_or_sequence", "")
        ref_error = _safe_ref_error(reference)
        if ref_error:
            invalid_refs += 1
            errors.append(ref_error)
            continue
        relative = Path(reference)
        try:
            fixture_path = (normalized / relative).resolve()
            fixture_path.relative_to(normalized)
        except ValueError:
            invalid_refs += 1
            errors.append("task030_fixture_reference_resolves_outside_pack")
            continue
        if not fixture_path.is_file():
            missing_refs += 1
            errors.append("task030_fixture_reference_missing")
            continue
        fixture_group_counts.update([relative.parts[1]])
        sequence_required = (
            row.get("test_type") == "cache_behavior"
            or row.get("automation_target") == "mock_http_sequence_test"
            or row.get("layer") in SEQUENCE_LAYERS
        )
        shape, fixture_errors = _read_fixture(fixture_path, sequence_required)
        fixture_shape_counts.update([shape])
        if "task030_fixture_json_malformed" in fixture_errors:
            malformed_fixtures += 1
        if "task030_sequence_fixture_shape_invalid" in fixture_errors:
            sequence_shape_invalid += 1
        errors.extend(fixture_errors)

    analysis = {
        "status": "pass" if not errors else "blocked_pack_contract_validation_failed",
        "evidence_status": "likely" if not errors else "unknown",
        "raw_pack_storage": "ignored_local_quarantine",
        "raw_values_public": False,
        "source_alias": "api-layer-audit-pack-20260706",
        "task030_matrix_rows": len(task030_rows),
        "mock_http_test_rows": target_counts.get("mock_http_test", 0),
        "mock_http_sequence_rows": target_counts.get("mock_http_sequence_test", 0),
        "state_machine_sequence_rows": layer_counts.get("state_machine_sequence", 0),
        "cache_behavior_rows": test_type_counts.get("cache_behavior", 0),
        "negative_auth_rows": test_type_counts.get("negative_auth", 0),
        "negative_server_error_rows": test_type_counts.get("negative_server_error", 0),
        "fixture_refs_checked": len(task030_rows),
        "fixture_refs_missing": missing_refs,
        "fixture_refs_invalid": invalid_refs,
        "fixture_json_malformed": malformed_fixtures,
        "sequence_fixture_shape_invalid": sequence_shape_invalid,
        "counts_by_task030_automation_target": dict(sorted(target_counts.items())),
        "counts_by_task030_test_type": dict(sorted(test_type_counts.items())),
        "counts_by_task030_layer": dict(sorted(layer_counts.items())),
        "counts_by_contract_kind": dict(sorted(contract_kind_counts.items())),
        "fixture_groups_checked": dict(sorted(fixture_group_counts.items())),
        "fixture_shape_counts": dict(sorted(fixture_shape_counts.items())),
        "mocked_transport_model": {
            "network_calls": "not_run",
            "transport": "in_memory_fixture_sequence_only",
            "negative_response_oracle": "fixture_shape_and_category_only",
            "cache_oracle": "sequence_fixture_shape_only",
        },
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


def _task036_task030_area(summary: dict[str, Any]) -> dict[str, Any] | None:
    ledger = summary.get("coverage_area_ledger")
    if not isinstance(ledger, list):
        return None
    for item in ledger:
        if isinstance(item, dict) and item.get("source_task") == TASK_ID:
            return item
    return None


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
    coverage = summary.get("coverage_summary", {})
    archive = summary.get("archive_intake", {})
    matrix_rows = archive.get("matrix_rows") if isinstance(archive, dict) else None
    if isinstance(matrix_rows, int) and isinstance(coverage, dict):
        for field_name in ("counts_by_layer", "counts_by_automation_target", "counts_by_test_type", "counts_by_status"):
            if _sum_count_map(coverage.get(field_name)) != matrix_rows:
                errors.append(f"task028_{field_name}_total_mismatch")
    else:
        errors.append("task028_matrix_rows_invalid")
    return sorted(set(errors))


def _validate_task029_summary(summary: dict[str, Any]) -> list[str]:
    errors = list(validate_task029_public_report(summary))
    if summary.get("task_id") != "TASK-029":
        errors.append("task029_summary_task_id_invalid")
    if summary.get("overall_status") != "pass":
        errors.append("task029_summary_not_pass")
    if summary.get("runtime_execution_status") != "not_run":
        errors.append("task029_runtime_status_not_not_run")
    if summary.get("live_api_execution_status") != "not_run":
        errors.append("task029_live_api_status_not_not_run")
    return sorted(set(errors))


def _validate_task036_summary(summary: dict[str, Any], task028_summary: dict[str, Any]) -> list[str]:
    errors = list(validate_task036_public_report(summary))
    if summary.get("task_id") != "TASK-036":
        errors.append("task036_summary_task_id_invalid")
    if summary.get("runtime_execution_status") != "not_run":
        errors.append("task036_runtime_status_not_not_run")
    if summary.get("live_api_execution_status") != "not_run":
        errors.append("task036_live_api_status_not_not_run")
    area = _task036_task030_area(summary)
    if area is None:
        errors.append("task036_task030_ledger_area_missing")
        return sorted(set(errors))
    coverage = task028_summary.get("coverage_summary", {})
    if not isinstance(coverage, dict):
        errors.append("task028_coverage_summary_invalid")
        return sorted(set(errors))
    layer_counts = coverage.get("counts_by_layer", {})
    target_counts = coverage.get("counts_by_automation_target", {})
    test_type_counts = coverage.get("counts_by_test_type", {})
    if area.get("known_sequence_rows") != layer_counts.get("state_machine_sequence"):
        errors.append("task036_task030_sequence_row_count_mismatch")
    if area.get("known_mock_http_tests") != target_counts.get("mock_http_test"):
        errors.append("task036_task030_mock_http_count_mismatch")
    if area.get("known_mock_http_sequence_tests") != target_counts.get("mock_http_sequence_test"):
        errors.append("task036_task030_mock_http_sequence_count_mismatch")
    if area.get("known_cache_behavior_tests") != test_type_counts.get("cache_behavior"):
        errors.append("task036_task030_cache_behavior_count_mismatch")
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
    target_counts = coverage.get("counts_by_automation_target", {})
    test_type_counts = coverage.get("counts_by_test_type", {})
    layer_counts = coverage.get("counts_by_layer", {})
    errors: list[str] = []
    if pack_contract.get("mock_http_test_rows") != target_counts.get("mock_http_test"):
        errors.append("pack_mock_http_count_mismatch_with_task028")
    if pack_contract.get("mock_http_sequence_rows") != target_counts.get("mock_http_sequence_test"):
        errors.append("pack_mock_http_sequence_count_mismatch_with_task028")
    if pack_contract.get("state_machine_sequence_rows") != layer_counts.get("state_machine_sequence"):
        errors.append("pack_sequence_row_count_mismatch_with_task028")
    if pack_contract.get("cache_behavior_rows") != test_type_counts.get("cache_behavior"):
        errors.append("pack_cache_behavior_count_mismatch_with_task028")
    return errors


def build_report(
    task028_report_path: Path = DEFAULT_TASK028_REPORT,
    task029_report_path: Path = DEFAULT_TASK029_REPORT,
    task036_report_path: Path = DEFAULT_TASK036_REPORT,
    pack_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    task028_summary, task028_load_errors = _read_json_object(task028_report_path, "task028_summary")
    task029_summary, task029_load_errors = _read_json_object(task029_report_path, "task029_summary")
    task036_summary, task036_load_errors = _read_json_object(task036_report_path, "task036_summary")

    summary_errors = task028_load_errors + task029_load_errors + task036_load_errors
    if not task028_load_errors:
        summary_errors.extend(_validate_task028_summary(task028_summary))
    if not task029_load_errors:
        summary_errors.extend(_validate_task029_summary(task029_summary))
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
    targets = coverage.get("counts_by_automation_target", {}) if isinstance(coverage, dict) else {}
    layers = coverage.get("counts_by_layer", {}) if isinstance(coverage, dict) else {}
    test_types = coverage.get("counts_by_test_type", {}) if isinstance(coverage, dict) else {}
    task036_area = _task036_task030_area(task036_summary) if isinstance(task036_summary, dict) else None

    public_safety = {key: False for key in sorted(FORBIDDEN_PUBLIC_FLAGS)}
    public_safety.update(
        {
            "public_report_contains_only_aliases_counts_categories_status_and_blockers": True,
            "raw_pack_content_read_from_public_repo": False,
            "local_quarantine_pack_required_for_pack_backed_parametrization": True,
            "mocked_transport_only": True,
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
                "mock_http_tests": targets.get("mock_http_test") if isinstance(targets, dict) else None,
                "mock_http_sequence_tests": targets.get("mock_http_sequence_test") if isinstance(targets, dict) else None,
                "state_machine_sequence_rows": layers.get("state_machine_sequence") if isinstance(layers, dict) else None,
                "cache_behavior_tests": test_types.get("cache_behavior") if isinstance(test_types, dict) else None,
                "negative_auth_tests": test_types.get("negative_auth") if isinstance(test_types, dict) else None,
                "negative_server_error_tests": test_types.get("negative_server_error") if isinstance(test_types, dict) else None,
            },
            "task029": {
                "source_report_alias": "task029_rest_schema_fixture_contracts_summary",
                "status": task029_summary.get("overall_status", "unknown") if task029_summary else "unknown",
                "evidence_status": task029_summary.get("evidence_status", "unknown") if task029_summary else "unknown",
            },
            "task036": {
                "source_report_alias": "task036_api_layer_exhaustive_coverage_summary",
                "status": task036_summary.get("overall_status", "unknown") if task036_summary else "unknown",
                "evidence_status": task036_summary.get("evidence_status", "unknown") if task036_summary else "unknown",
                "task030_ledger_status": task036_area.get("status") if isinstance(task036_area, dict) else "unknown",
            },
        },
        "rest_negative_cache_sequence_summary": {
            "known_mock_http_tests": targets.get("mock_http_test") if isinstance(targets, dict) else None,
            "known_mock_http_sequence_tests": targets.get("mock_http_sequence_test") if isinstance(targets, dict) else None,
            "known_state_machine_sequence_rows": layers.get("state_machine_sequence") if isinstance(layers, dict) else None,
            "known_cache_behavior_tests": test_types.get("cache_behavior") if isinstance(test_types, dict) else None,
            "known_negative_auth_tests": test_types.get("negative_auth") if isinstance(test_types, dict) else None,
            "known_negative_server_error_tests": test_types.get("negative_server_error") if isinstance(test_types, dict) else None,
            "source_reconciliation_status": "pass" if not summary_errors else "blocked",
        },
        "pack_contract": pack_contract,
        "offline_execution_boundary": {
            "live_rest_backend_calls": "not_run",
            "auth_token_cookie_header_replay": "not_run",
            "websocket_stomp_connections": "not_run",
            "webrtc_datachannel_connections": "not_run",
            "android_adb_runtime_actions": "not_run",
            "apk_read_install_or_modification": "not_run",
            "transport_strategy": "offline_mocked_transport_from_local_fixtures",
        },
        "public_safety": public_safety,
        "blocked_reasons": sorted(set(summary_errors + pack_errors)),
        "unverified_areas": [
            "live REST backend behavior",
            "backend authorization and ACL enforcement",
            "cache behavior against a real backend",
            "state transitions against a real backend",
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
        "android_runtime_status",
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
    for field_name in ("runtime_execution_status", "live_api_execution_status", "network_execution_status", "android_runtime_status"):
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
        if public_safety.get("mocked_transport_only") is not True:
            errors.append("mocked_transport_only_flag_missing")

    boundary = report.get("offline_execution_boundary")
    if not isinstance(boundary, dict):
        errors.append("offline_execution_boundary_not_object")
    elif any(value != "not_run" for key, value in boundary.items() if key != "transport_strategy"):
        errors.append("offline_execution_boundary_contains_executed_action")

    errors.extend(_public_safety_findings(report))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TASK-030 REST negative/cache/state-sequence contracts offline.")
    parser.add_argument("--task028-report", type=Path, default=DEFAULT_TASK028_REPORT, help="Tracked TASK-028 public summary.")
    parser.add_argument("--task029-report", type=Path, default=DEFAULT_TASK029_REPORT, help="Tracked TASK-029 public summary.")
    parser.add_argument("--task036-report", type=Path, default=DEFAULT_TASK036_REPORT, help="Tracked TASK-036 public summary.")
    parser.add_argument("--pack-root", type=Path, help="Optional ignored local API quarantine pack root.")
    parser.add_argument("--report", type=Path, help="Optional TASK-030 public-safe summary JSON output path.")
    args = parser.parse_args(argv)

    report = build_report(args.task028_report, args.task029_report, args.task036_report, args.pack_root)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "validation_status": report["overall_status"],
        "blocked_reason_count": len(report.get("blocked_reasons", [])),
        "pack_contract_status": report.get("pack_contract", {}).get("status"),
        "known_mock_http_tests": report.get("rest_negative_cache_sequence_summary", {}).get("known_mock_http_tests"),
        "known_mock_http_sequence_tests": report.get("rest_negative_cache_sequence_summary", {}).get("known_mock_http_sequence_tests"),
        "report_alias": "task030_rest_negative_cache_sequences_summary" if args.report else None,
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 1 if report["overall_status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
