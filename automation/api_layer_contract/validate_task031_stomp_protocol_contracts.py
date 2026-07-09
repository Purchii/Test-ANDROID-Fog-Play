"""Validate TASK-031 STOMP/device protocol contracts offline.

The harness is intentionally offline-only. It may read an ignored local API
audit pack, but it validates only STOMP signaling and device protocol fixture
categories and emits public-safe aliases, counts, statuses and blockers.
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
from automation.api_layer_contract.validate_task030_rest_negative_cache_sequences import (
    validate_public_report as validate_task030_public_report,
)
from automation.api_layer_contract.validate_task036_api_layer_exhaustive_coverage import (
    validate_public_report as validate_task036_public_report,
)


TASK_ID = "TASK-031"
SCHEMA_VERSION = "task031-stomp-protocol-contracts-v1"
TOOL_NAME = "validate_task031_stomp_protocol_contracts"
DEFAULT_TASK028_REPORT = Path("docs/qa/reports/task028_api_layer_contract_coverage.summary.json")
DEFAULT_TASK030_REPORT = Path("docs/qa/reports/task030_rest_negative_cache_sequences.summary.json")
DEFAULT_TASK036_REPORT = Path("docs/qa/reports/task036_api_layer_exhaustive_coverage.summary.json")

TASK031_FIXTURE_GROUPS = {"stomp_signaling", "stomp_device"}
TASK032_OUT_OF_SCOPE_FIXTURE_GROUPS = {"datachannel", "gamepad"}
TASK031_TARGETS = {"protocol_fixture_test", "protocol_negative_test", "protocol_sequence_or_fixture_test"}
TASK031_TEST_TYPES = {
    "positive_protocol_schema",
    "negative_invalid_fields",
    "negative_malformed_base64",
    "negative_malformed_json",
    "sequence_positive_or_negative",
}
ALLOWED_FIXTURE_PREFIXES = tuple(f"fixtures/{group}/" for group in sorted(TASK031_FIXTURE_GROUPS))

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
    "websocket_stomp_connections_performed",
    "datachannel_webrtc_connections_performed",
    "adb_or_android_runtime_actions_performed",
    "apk_read_install_or_modification_performed",
    "real_payment_or_session_mutation_performed",
    "tls_or_security_bypass_performed",
}

RAW_PUBLIC_TEXT_RE = re.compile(
    r"\b(?:https?|wss?)://|"
    r"(?<![\w-])/(?:api|log|ws|socket|stomp|payment|billing|order|profile|auth|login|content)[/\w{}.,:@?=&%-]*|"
    r"(?<![\w-])/(?:topic|queue|user/queue|app)[/\w{}.,:@?=&%-]*|"
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
        return "task031_fixture_reference_empty"
    if "\\" in reference:
        return "task031_fixture_reference_uses_non_posix_separator"
    path = Path(reference)
    if path.is_absolute():
        return "task031_fixture_reference_absolute"
    if any(part in {"", ".", ".."} for part in path.parts):
        return "task031_fixture_reference_traversal"
    if not reference.startswith(ALLOWED_FIXTURE_PREFIXES):
        return "task031_fixture_reference_unapproved_group"
    return None


def _fixture_group(reference: str) -> str:
    parts = Path(reference).parts
    if len(parts) >= 2 and parts[0] == "fixtures":
        return parts[1]
    return "unknown"


def _is_protocol_row(row: Mapping[str, str]) -> bool:
    return row.get("layer") == "protocol" or row.get("automation_target") in TASK031_TARGETS


def _is_task031_row(row: Mapping[str, str]) -> bool:
    domain = row.get("domain", "")
    item = row.get("item", "")
    reference = row.get("fixture_or_sequence", "")
    if _fixture_group(reference) in TASK031_FIXTURE_GROUPS:
        return _is_protocol_row(row) or row.get("test_type") in TASK031_TEST_TYPES
    if domain in {"stomp_signaling", "inter_device_communication"} and _is_protocol_row(row):
        return True
    return item.startswith(("WS_SIG_", "DEVICE_STOMP_")) and _is_protocol_row(row)


def _is_task032_out_of_scope_row(row: Mapping[str, str]) -> bool:
    return _fixture_group(row.get("fixture_or_sequence", "")) in TASK032_OUT_OF_SCOPE_FIXTURE_GROUPS


def _row_contract_kind(row: Mapping[str, str]) -> str:
    target = row.get("automation_target", "")
    test_type = row.get("test_type", "")
    if target == "protocol_negative_test" or test_type.startswith("negative_"):
        return "negative_protocol_fixture"
    if target == "protocol_sequence_or_fixture_test" or test_type == "sequence_positive_or_negative":
        return "protocol_sequence_or_fixture"
    return "positive_protocol_fixture"


def _read_fixture(path: Path, sequence_allowed: bool) -> tuple[str, list[str]]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return "malformed", ["task031_fixture_json_malformed"]
    except OSError:
        return "unreadable", ["task031_fixture_json_unreadable"]
    if loaded is None:
        return "invalid", ["task031_fixture_json_null"]
    if isinstance(loaded, dict):
        if loaded:
            return "object", []
        return "empty_object", ["task031_protocol_fixture_shape_invalid"]
    if sequence_allowed and isinstance(loaded, list) and loaded:
        return "sequence_list", []
    return "invalid_protocol_shape", ["task031_protocol_fixture_shape_invalid"]


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
    task031_rows = [row for row in rows if _is_task031_row(row)]
    task032_rows = [row for row in rows if _is_task032_out_of_scope_row(row)]
    target_counts = Counter(row.get("automation_target", "unknown") for row in task031_rows)
    test_type_counts = Counter(row.get("test_type", "unknown") for row in task031_rows)
    fixture_group_counts = Counter(_fixture_group(row.get("fixture_or_sequence", "")) for row in task031_rows)
    contract_kind_counts = Counter(_row_contract_kind(row) for row in task031_rows)
    priority_counts = Counter(row.get("priority", "unknown") for row in task031_rows)
    fixture_shape_counts: Counter[str] = Counter()
    missing_refs = 0
    invalid_refs = 0
    malformed_fixtures = 0
    invalid_shapes = 0

    for row in task031_rows:
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
            errors.append("task031_fixture_reference_resolves_outside_pack")
            continue
        if not fixture_path.is_file():
            missing_refs += 1
            errors.append("task031_fixture_reference_missing")
            continue
        sequence_allowed = row.get("automation_target") == "protocol_sequence_or_fixture_test"
        shape, fixture_errors = _read_fixture(fixture_path, sequence_allowed)
        fixture_shape_counts.update([shape])
        if "task031_fixture_json_malformed" in fixture_errors:
            malformed_fixtures += 1
        if "task031_protocol_fixture_shape_invalid" in fixture_errors:
            invalid_shapes += 1
        errors.extend(fixture_errors)

    analysis = {
        "status": "pass" if not errors else "blocked_pack_contract_validation_failed",
        "evidence_status": "likely" if not errors else "unknown",
        "raw_pack_storage": "ignored_local_quarantine",
        "raw_values_public": False,
        "source_alias": "api-layer-audit-pack-20260706",
        "task031_matrix_rows": len(task031_rows),
        "stomp_signaling_rows": fixture_group_counts.get("stomp_signaling", 0),
        "stomp_device_rows": fixture_group_counts.get("stomp_device", 0),
        "protocol_fixture_rows": target_counts.get("protocol_fixture_test", 0),
        "protocol_negative_rows": target_counts.get("protocol_negative_test", 0),
        "protocol_sequence_or_fixture_rows": target_counts.get("protocol_sequence_or_fixture_test", 0),
        "positive_protocol_schema_rows": test_type_counts.get("positive_protocol_schema", 0),
        "negative_invalid_fields_rows": test_type_counts.get("negative_invalid_fields", 0),
        "negative_malformed_base64_rows": test_type_counts.get("negative_malformed_base64", 0),
        "negative_malformed_json_rows": test_type_counts.get("negative_malformed_json", 0),
        "fixture_refs_checked": len(task031_rows),
        "fixture_refs_missing": missing_refs,
        "fixture_refs_invalid": invalid_refs,
        "fixture_json_malformed": malformed_fixtures,
        "protocol_fixture_shape_invalid": invalid_shapes,
        "counts_by_task031_automation_target": dict(sorted(target_counts.items())),
        "counts_by_task031_test_type": dict(sorted(test_type_counts.items())),
        "counts_by_task031_fixture_group": dict(sorted(fixture_group_counts.items())),
        "counts_by_contract_kind": dict(sorted(contract_kind_counts.items())),
        "counts_by_priority": dict(sorted(priority_counts.items())),
        "fixture_shape_counts": dict(sorted(fixture_shape_counts.items())),
        "task032_out_of_scope_protocol_rows": len(task032_rows),
        "task032_out_of_scope_fixture_groups": dict(
            sorted(Counter(_fixture_group(row.get("fixture_or_sequence", "")) for row in task032_rows).items())
        ),
        "offline_protocol_model": {
            "network_calls": "not_run",
            "websocket_connections": "not_run",
            "transport": "local_fixture_shape_validation_only",
            "message_delivery_oracle": "not_run",
            "device_pairing_oracle": "not_run",
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


def _task036_task031_area(summary: dict[str, Any]) -> dict[str, Any] | None:
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


def _validate_task030_summary(summary: dict[str, Any]) -> list[str]:
    errors = list(validate_task030_public_report(summary))
    if summary.get("task_id") != "TASK-030":
        errors.append("task030_summary_task_id_invalid")
    if summary.get("overall_status") != "pass":
        errors.append("task030_summary_not_pass")
    if summary.get("runtime_execution_status") != "not_run":
        errors.append("task030_runtime_status_not_not_run")
    if summary.get("live_api_execution_status") != "not_run":
        errors.append("task030_live_api_status_not_not_run")
    return sorted(set(errors))


def _validate_task036_summary(summary: dict[str, Any], task028_summary: dict[str, Any]) -> list[str]:
    errors = list(validate_task036_public_report(summary))
    if summary.get("task_id") != "TASK-036":
        errors.append("task036_summary_task_id_invalid")
    if summary.get("runtime_execution_status") != "not_run":
        errors.append("task036_runtime_status_not_not_run")
    if summary.get("live_api_execution_status") != "not_run":
        errors.append("task036_live_api_status_not_not_run")
    area = _task036_task031_area(summary)
    if area is None:
        errors.append("task036_task031_ledger_area_missing")
        return sorted(set(errors))
    coverage = task028_summary.get("coverage_summary", {})
    if not isinstance(coverage, dict):
        errors.append("task028_coverage_summary_invalid")
        return sorted(set(errors))
    layer_counts = coverage.get("counts_by_layer", {})
    target_counts = coverage.get("counts_by_automation_target", {})
    if area.get("known_protocol_rows") != layer_counts.get("protocol"):
        errors.append("task036_task031_protocol_row_count_mismatch")
    if area.get("known_protocol_fixture_tests") != target_counts.get("protocol_fixture_test"):
        errors.append("task036_task031_protocol_fixture_count_mismatch")
    if area.get("known_protocol_negative_tests") != target_counts.get("protocol_negative_test"):
        errors.append("task036_task031_protocol_negative_count_mismatch")
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
    fixture_groups = coverage.get("fixture_groups", {})
    errors: list[str] = []
    if pack_contract.get("stomp_signaling_rows") != fixture_groups.get("stomp_signaling"):
        errors.append("pack_stomp_signaling_count_mismatch_with_task028")
    if pack_contract.get("stomp_device_rows") != fixture_groups.get("stomp_device"):
        errors.append("pack_stomp_device_count_mismatch_with_task028")
    return errors


def build_report(
    task028_report_path: Path = DEFAULT_TASK028_REPORT,
    task030_report_path: Path = DEFAULT_TASK030_REPORT,
    task036_report_path: Path = DEFAULT_TASK036_REPORT,
    pack_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    task028_summary, task028_load_errors = _read_json_object(task028_report_path, "task028_summary")
    task030_summary, task030_load_errors = _read_json_object(task030_report_path, "task030_summary")
    task036_summary, task036_load_errors = _read_json_object(task036_report_path, "task036_summary")

    summary_errors = task028_load_errors + task030_load_errors + task036_load_errors
    if not task028_load_errors:
        summary_errors.extend(_validate_task028_summary(task028_summary))
    if not task030_load_errors:
        summary_errors.extend(_validate_task030_summary(task030_summary))
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
    fixture_groups = coverage.get("fixture_groups", {}) if isinstance(coverage, dict) else {}
    inventory_types = coverage.get("inventory_types", {}) if isinstance(coverage, dict) else {}
    task036_area = _task036_task031_area(task036_summary) if isinstance(task036_summary, dict) else None

    public_safety = {key: False for key in sorted(FORBIDDEN_PUBLIC_FLAGS)}
    public_safety.update(
        {
            "public_report_contains_only_aliases_counts_categories_status_and_blockers": True,
            "raw_pack_content_read_from_public_repo": False,
            "local_quarantine_pack_required_for_pack_backed_parametrization": True,
            "offline_protocol_fixture_validation_only": True,
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
                "known_protocol_rows": layers.get("protocol") if isinstance(layers, dict) else None,
                "known_protocol_fixture_tests": targets.get("protocol_fixture_test") if isinstance(targets, dict) else None,
                "known_protocol_negative_tests": targets.get("protocol_negative_test") if isinstance(targets, dict) else None,
                "known_stomp_signaling_fixture_group_count": fixture_groups.get("stomp_signaling") if isinstance(fixture_groups, dict) else None,
                "known_stomp_device_fixture_group_count": fixture_groups.get("stomp_device") if isinstance(fixture_groups, dict) else None,
                "known_datachannel_fixture_group_count": fixture_groups.get("datachannel") if isinstance(fixture_groups, dict) else None,
                "known_gamepad_fixture_group_count": fixture_groups.get("gamepad") if isinstance(fixture_groups, dict) else None,
                "known_stomp_signaling_inventory_count": inventory_types.get("stomp_signaling_message") if isinstance(inventory_types, dict) else None,
                "known_device_stomp_inventory_count": inventory_types.get("device_stomp_message") if isinstance(inventory_types, dict) else None,
            },
            "task030": {
                "source_report_alias": "task030_rest_negative_cache_sequences_summary",
                "status": task030_summary.get("overall_status", "unknown") if task030_summary else "unknown",
                "evidence_status": task030_summary.get("evidence_status", "unknown") if task030_summary else "unknown",
            },
            "task036": {
                "source_report_alias": "task036_api_layer_exhaustive_coverage_summary",
                "status": task036_summary.get("overall_status", "unknown") if task036_summary else "unknown",
                "evidence_status": task036_summary.get("evidence_status", "unknown") if task036_summary else "unknown",
                "task031_ledger_status": task036_area.get("status") if isinstance(task036_area, dict) else "unknown",
            },
        },
        "stomp_protocol_summary": {
            "source_reconciliation_status": "pass" if not summary_errors else "blocked",
            "known_protocol_rows_all_protocol_scope": layers.get("protocol") if isinstance(layers, dict) else None,
            "known_protocol_fixture_tests_all_protocol_scope": targets.get("protocol_fixture_test") if isinstance(targets, dict) else None,
            "known_protocol_negative_tests_all_protocol_scope": targets.get("protocol_negative_test") if isinstance(targets, dict) else None,
            "task031_scope_fixture_groups": sorted(TASK031_FIXTURE_GROUPS),
            "task032_out_of_scope_fixture_groups": sorted(TASK032_OUT_OF_SCOPE_FIXTURE_GROUPS),
            "all_protocol_rows_are_not_claimed_by_task031": True,
        },
        "pack_contract": pack_contract,
        "offline_execution_boundary": {
            "live_rest_backend_calls": "not_run",
            "auth_token_cookie_header_replay": "not_run",
            "websocket_stomp_connections": "not_run",
            "webrtc_datachannel_connections": "not_run",
            "android_adb_runtime_actions": "not_run",
            "apk_read_install_or_modification": "not_run",
            "transport_strategy": "offline_protocol_fixture_shape_validation_only",
        },
        "public_safety": public_safety,
        "blocked_reasons": sorted(set(summary_errors + pack_errors)),
        "unverified_areas": [
            "live STOMP/WebSocket behavior",
            "backend subscription routing or delivery behavior",
            "real device pairing behavior",
            "backend authorization and ACL enforcement",
            "Android runtime correlation with protocol evidence",
            "DataChannel and gamepad protocol behavior reserved for TASK-032",
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
        if public_safety.get("offline_protocol_fixture_validation_only") is not True:
            errors.append("offline_protocol_fixture_validation_only_flag_missing")

    summary = report.get("stomp_protocol_summary")
    if not isinstance(summary, dict):
        errors.append("stomp_protocol_summary_not_object")
    elif summary.get("all_protocol_rows_are_not_claimed_by_task031") is not True:
        errors.append("all_protocol_rows_overclaim_guard_missing")

    boundary = report.get("offline_execution_boundary")
    if not isinstance(boundary, dict):
        errors.append("offline_execution_boundary_not_object")
    elif any(value != "not_run" for key, value in boundary.items() if key != "transport_strategy"):
        errors.append("offline_execution_boundary_contains_executed_action")

    errors.extend(_public_safety_findings(report))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TASK-031 STOMP/device protocol contracts offline.")
    parser.add_argument("--task028-report", type=Path, default=DEFAULT_TASK028_REPORT, help="Tracked TASK-028 public summary.")
    parser.add_argument("--task030-report", type=Path, default=DEFAULT_TASK030_REPORT, help="Tracked TASK-030 public summary.")
    parser.add_argument("--task036-report", type=Path, default=DEFAULT_TASK036_REPORT, help="Tracked TASK-036 public summary.")
    parser.add_argument("--pack-root", type=Path, help="Optional ignored local API quarantine pack root.")
    parser.add_argument("--report", type=Path, help="Optional TASK-031 public-safe summary JSON output path.")
    args = parser.parse_args(argv)

    report = build_report(args.task028_report, args.task030_report, args.task036_report, args.pack_root)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "validation_status": report["overall_status"],
        "blocked_reason_count": len(report.get("blocked_reasons", [])),
        "pack_contract_status": report.get("pack_contract", {}).get("status"),
        "task031_matrix_rows": report.get("pack_contract", {}).get("task031_matrix_rows"),
        "stomp_signaling_rows": report.get("pack_contract", {}).get("stomp_signaling_rows"),
        "stomp_device_rows": report.get("pack_contract", {}).get("stomp_device_rows"),
        "report_alias": "task031_stomp_protocol_contracts_summary" if args.report else None,
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 1 if report["overall_status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
