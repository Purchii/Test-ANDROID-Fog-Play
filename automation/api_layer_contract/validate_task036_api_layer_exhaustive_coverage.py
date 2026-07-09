"""Validate TASK-036 exhaustive API-layer offline coverage boundaries.

This validator consumes the public-safe TASK-028 summary and, when an ignored
local quarantine pack is available, cross-checks it through the TASK-028
validator. Public output stays limited to aliases, counts, categories and
blocked/not-run statuses.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
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


TASK_ID = "TASK-036"
SCHEMA_VERSION = "task036-api-layer-exhaustive-coverage-v1"
TOOL_NAME = "validate_task036_api_layer_exhaustive_coverage"
TASK028_SCHEMA_VERSION = "task028-api-layer-contract-coverage-v1"

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

REQUIRED_FOLLOW_UPS = {
    "TASK-029",
    "TASK-030",
    "TASK-031",
    "TASK-032",
    "TASK-033",
    "TASK-034",
}

RAW_VALUE_RE = re.compile(
    r"\b(?:https?|wss?)://|(?<![\w-])/(?:api|log|ws|socket|stomp)[/\w{}.-]*|"
    r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])|"
    r"\b[a-fA-F0-9]{64}\b|"
    r"\b(?:authorization|bearer|cookie|session|token|secret|password|api[_-]?key|otp|captcha)[:=]\s*\S+",
    re.IGNORECASE,
)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return None, f"summary JSON is malformed: {exc.msg}."
    except OSError as exc:
        return None, f"summary JSON cannot be read: {exc}."
    if not isinstance(loaded, dict):
        return None, "summary JSON must be an object."
    return loaded, None


def _sum_count_map(value: Any, field_name: str) -> tuple[int | None, list[str]]:
    if not isinstance(value, Mapping):
        return None, [f"{field_name} must be an object."]
    total = 0
    errors: list[str] = []
    for key, count in value.items():
        if not isinstance(key, str) or not key.strip():
            errors.append(f"{field_name} contains an empty or non-string key.")
        if not isinstance(count, int) or count < 0:
            errors.append(f"{field_name}.{key} must be a non-negative integer.")
        else:
            total += count
    return total, errors


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
    if isinstance(value, str) and RAW_VALUE_RE.search(value):
        findings.append(f"{path} contains raw API/private/local evidence-like text.")
    return findings


def _validate_task028_summary(summary: dict[str, Any]) -> list[str]:
    errors = list(validate_task028_public_report(summary))
    if summary.get("schema_version") != TASK028_SCHEMA_VERSION:
        errors.append(f"TASK-028 summary schema_version must be {TASK028_SCHEMA_VERSION}.")
    if summary.get("task_id") != "TASK-028":
        errors.append("TASK-028 summary task_id must be TASK-028.")
    if summary.get("overall_status") != "pass":
        errors.append("TASK-028 summary overall_status must be pass before TASK-036 can build on it.")
    if summary.get("evidence_status") != "likely":
        errors.append("TASK-028 summary evidence_status must be likely.")
    if summary.get("runtime_execution_status") != "not_run":
        errors.append("TASK-028 summary runtime_execution_status must be not_run.")
    if summary.get("live_api_execution_status") != "not_run":
        errors.append("TASK-028 summary live_api_execution_status must be not_run.")

    archive = summary.get("archive_intake", {})
    coverage = summary.get("coverage_summary", {})
    if not isinstance(archive, dict):
        errors.append("archive_intake must be an object.")
        archive = {}
    if not isinstance(coverage, dict):
        errors.append("coverage_summary must be an object.")
        coverage = {}

    matrix_rows = archive.get("matrix_rows")
    if not isinstance(matrix_rows, int) or matrix_rows <= 0:
        errors.append("archive_intake.matrix_rows must be a positive integer.")
        matrix_rows = None
    if archive.get("required_files_present") is not True:
        errors.append("archive_intake.required_files_present must be true.")
    if archive.get("missing_fixture_refs") != 0:
        errors.append("archive_intake.missing_fixture_refs must be 0.")
    if matrix_rows is not None and archive.get("fixture_or_sequence_refs") != matrix_rows:
        errors.append("archive_intake.fixture_or_sequence_refs must equal matrix_rows.")

    count_fields = [
        "counts_by_layer",
        "counts_by_priority",
        "counts_by_test_type",
        "counts_by_automation_target",
        "counts_by_status",
    ]
    for field_name in count_fields:
        total, field_errors = _sum_count_map(coverage.get(field_name), f"coverage_summary.{field_name}")
        errors.extend(field_errors)
        if matrix_rows is not None and total is not None and total != matrix_rows:
            errors.append(f"coverage_summary.{field_name} total must equal matrix_rows.")

    group_checks = [
        ("fixture_groups", "fixture_json_files"),
        ("schema_groups", "schema_json_files"),
        ("inventory_types", "inventory_items"),
    ]
    for field_name, archive_field in group_checks:
        total, field_errors = _sum_count_map(coverage.get(field_name), f"coverage_summary.{field_name}")
        errors.extend(field_errors)
        expected = archive.get(archive_field)
        if isinstance(expected, int) and total is not None and total != expected:
            errors.append(f"coverage_summary.{field_name} total must equal archive_intake.{archive_field}.")

    follow_ups = summary.get("follow_up_task_decomposition")
    if not isinstance(follow_ups, list):
        errors.append("follow_up_task_decomposition must be a list.")
    else:
        present = {item.get("task_id") for item in follow_ups if isinstance(item, dict)}
        missing = sorted(REQUIRED_FOLLOW_UPS - present)
        if missing:
            errors.append(f"follow_up_task_decomposition missing required tasks: {missing}.")

    public_safety = summary.get("public_safety")
    if not isinstance(public_safety, dict):
        errors.append("public_safety must be an object.")
    else:
        for flag in sorted(FORBIDDEN_PUBLIC_FLAGS):
            if public_safety.get(flag) is not False:
                errors.append(f"public_safety.{flag} must be false.")

    return sorted(set(errors))


def _coverage_area_ledger(summary: dict[str, Any]) -> list[dict[str, Any]]:
    coverage = summary.get("coverage_summary", {})
    layers = coverage.get("counts_by_layer", {}) if isinstance(coverage, dict) else {}
    targets = coverage.get("counts_by_automation_target", {}) if isinstance(coverage, dict) else {}
    test_types = coverage.get("counts_by_test_type", {}) if isinstance(coverage, dict) else {}

    return [
        {
            "area": "rest_schema_fixture_contracts",
            "source_task": "TASK-029",
            "known_matrix_rows": layers.get("rest", 0),
            "known_fixture_schema_tests": targets.get("fixture_schema_test", 0),
            "known_negative_fixture_schema_tests": targets.get("fixture_schema_negative_test", 0),
            "status": "tracked_summary_validated_pack_parametrization_blocked_without_local_pack",
        },
        {
            "area": "rest_negative_cache_state_sequences",
            "source_task": "TASK-030",
            "known_sequence_rows": layers.get("state_machine_sequence", 0),
            "known_mock_http_tests": targets.get("mock_http_test", 0),
            "known_mock_http_sequence_tests": targets.get("mock_http_sequence_test", 0),
            "known_cache_behavior_tests": test_types.get("cache_behavior", 0),
            "status": "tracked_summary_validated_mock_transport_required",
        },
        {
            "area": "stomp_and_device_protocol_contracts",
            "source_task": "TASK-031",
            "known_protocol_rows": layers.get("protocol", 0),
            "known_protocol_fixture_tests": targets.get("protocol_fixture_test", 0),
            "known_protocol_negative_tests": targets.get("protocol_negative_test", 0),
            "status": "tracked_summary_validated_offline_protocol_fixtures_required",
        },
        {
            "area": "datachannel_and_gamepad_contracts",
            "source_task": "TASK-032",
            "known_datachannel_fixture_group_count": summary.get("coverage_summary", {})
            .get("fixture_groups", {})
            .get("datachannel", 0),
            "known_gamepad_fixture_group_count": summary.get("coverage_summary", {})
            .get("fixture_groups", {})
            .get("gamepad", 0),
            "status": "tracked_summary_validated_offline_protocol_fixtures_required",
        },
        {
            "area": "api_redaction_prod_safety_guards",
            "source_task": "TASK-033",
            "known_security_rows": layers.get("security", 0),
            "known_redaction_tests": test_types.get("security_redaction", 0),
            "status": "tracked_summary_validated_synthetic_guard_tests_required",
        },
        {
            "area": "approved_staging_or_live_exploration",
            "source_task": "TASK-034",
            "known_runtime_optional_rows": layers.get("runtime_optional", 0),
            "status": "blocked_until_prod_conditional_prerequisites_confirmed",
        },
    ]


def _pack_crosscheck(pack_root: Path | None, task028_summary: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    if pack_root is None:
        return {
            "status": "blocked_pack_root_not_provided",
            "evidence_status": "unknown",
            "raw_pack_storage": "ignored_local_quarantine",
            "raw_values_public": False,
        }, ["local quarantine API pack root was not provided for pack-backed parametrization."]
    if not pack_root.exists():
        return {
            "status": "blocked_missing_local_quarantine_pack",
            "evidence_status": "unknown",
            "raw_pack_storage": "ignored_local_quarantine",
            "raw_values_public": False,
        }, ["local quarantine API pack is not available in this worktree."]

    pack_report = build_task028_pack_report(pack_root)
    errors = validate_task028_public_report(pack_report)
    if pack_report.get("overall_status") != "pass":
        errors.extend(pack_report.get("blocked_reasons", []))

    compare_fields = [
        ("archive_intake", "matrix_rows"),
        ("archive_intake", "fixture_or_sequence_refs"),
        ("archive_intake", "fixture_json_files"),
        ("archive_intake", "schema_json_files"),
        ("archive_intake", "inventory_items"),
        ("coverage_summary", "counts_by_layer"),
        ("coverage_summary", "counts_by_test_type"),
        ("coverage_summary", "counts_by_automation_target"),
        ("coverage_summary", "fixture_groups"),
        ("coverage_summary", "schema_groups"),
    ]
    for section, field_name in compare_fields:
        if pack_report.get(section, {}).get(field_name) != task028_summary.get(section, {}).get(field_name):
            errors.append(f"local pack cross-check mismatch for {section}.{field_name}.")

    if errors:
        return {
            "status": "blocked_pack_crosscheck_failed",
            "evidence_status": "unknown",
            "raw_pack_storage": "ignored_local_quarantine",
            "raw_values_public": False,
        }, sorted(set(errors))
    return {
        "status": "pass",
        "evidence_status": "likely",
        "raw_pack_storage": "ignored_local_quarantine",
        "raw_values_public": False,
    }, []


def build_report(
    task028_report_path: Path,
    pack_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    task028_summary, load_error = _read_json(task028_report_path)
    summary_errors: list[str] = []
    pack_errors: list[str] = []
    if load_error:
        task028_summary = {}
        summary_errors.append(load_error)
    else:
        summary_errors.extend(_validate_task028_summary(task028_summary))

    pack_status, current_pack_errors = _pack_crosscheck(pack_root, task028_summary) if task028_summary else (
        {"status": "not_run_due_invalid_task028_summary", "evidence_status": "unknown"},
        [],
    )
    pack_errors.extend(current_pack_errors)
    errors = summary_errors + pack_errors
    if summary_errors:
        overall_status = "blocked"
        evidence_status = "unknown"
    elif pack_errors:
        overall_status = "partial_blocked"
        evidence_status = "likely_with_blockers"
    else:
        overall_status = "pass"
        evidence_status = "likely"

    live_blockers = [
        "approved staging or test backend alias is not confirmed",
        "synthetic user/session policy is not confirmed",
        "resource budget and rate limits are not confirmed",
        "cleanup/rollback/kill switch is not confirmed",
        "local-only raw evidence storage and redaction review are not confirmed",
        "QA A, QA B and Security pre-execution approvals are not confirmed",
    ]

    public_safety = {key: False for key in sorted(FORBIDDEN_PUBLIC_FLAGS)}
    public_safety.update(
        {
            "public_report_contains_only_aliases_counts_and_categories": True,
            "raw_pack_content_read_from_public_repo": False,
            "local_quarantine_pack_required_for_pack_backed_parametrization": True,
        }
    )

    archive = task028_summary.get("archive_intake", {}) if isinstance(task028_summary, dict) else {}
    coverage = task028_summary.get("coverage_summary", {}) if isinstance(task028_summary, dict) else {}
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "task_id": TASK_ID,
        "mode": "BOUNDED_AUTONOMOUS",
        "tool_name": TOOL_NAME,
        "overall_status": overall_status,
        "evidence_status": evidence_status,
        "production_safety_classification": "PROD_SAFE_OFFLINE_STATIC_AND_SYNTHETIC_ONLY",
        "runtime_execution_status": "not_run",
        "live_api_execution_status": "not_run",
        "source_summary": {
            "source_task_id": "TASK-028",
            "source_report_alias": "task028_api_layer_contract_coverage_summary",
            "evidence_status": task028_summary.get("evidence_status", "unknown") if task028_summary else "unknown",
            "matrix_rows": archive.get("matrix_rows"),
            "fixture_or_sequence_refs": archive.get("fixture_or_sequence_refs"),
            "fixture_json_files": archive.get("fixture_json_files"),
            "schema_json_files": archive.get("schema_json_files"),
            "inventory_items": archive.get("inventory_items"),
        },
        "coverage_area_ledger": _coverage_area_ledger(task028_summary) if task028_summary else [],
        "coverage_totals": {
            "counts_by_layer": coverage.get("counts_by_layer", {}),
            "counts_by_test_type": coverage.get("counts_by_test_type", {}),
            "counts_by_automation_target": coverage.get("counts_by_automation_target", {}),
            "counts_by_status": coverage.get("counts_by_status", {}),
            "fixture_groups": coverage.get("fixture_groups", {}),
            "schema_groups": coverage.get("schema_groups", {}),
            "inventory_types": coverage.get("inventory_types", {}),
        },
        "local_pack_crosscheck": pack_status,
        "exploratory_evidence_intake_gate": {
            "status": "blocked_missing_prod_conditional_prerequisites",
            "production_safety_classification": "PROD_CONDITIONAL",
            "live_rest_backend_calls": "not_run",
            "live_stomp_websocket_connections": "not_run",
            "live_datachannel_webrtc_connections": "not_run",
            "android_runtime_correlation": "not_run",
            "raw_endpoint_publication": "forbidden",
            "required_prerequisites": live_blockers,
        },
        "public_safety": public_safety,
        "blocked_reasons": sorted(set(errors)),
        "unverified_areas": [
            "pack-backed per-row fixture parametrization when local quarantine pack is absent",
            "live REST backend behavior",
            "live STOMP/WebSocket behavior",
            "live WebRTC/DataChannel behavior",
            "backend authorization and ACL enforcement",
            "real payment/order/session mutation behavior",
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
    }
    missing = sorted(required - set(report))
    if missing:
        errors.append(f"report missing required fields: {missing}.")
    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}.")
    if report.get("task_id") != TASK_ID:
        errors.append("task_id must be TASK-036.")
    if report.get("mode") != "BOUNDED_AUTONOMOUS":
        errors.append("mode must be BOUNDED_AUTONOMOUS.")
    if report.get("runtime_execution_status") != "not_run":
        errors.append("runtime_execution_status must be not_run.")
    if report.get("live_api_execution_status") != "not_run":
        errors.append("live_api_execution_status must be not_run.")
    if report.get("overall_status") not in {"pass", "partial_blocked", "blocked"}:
        errors.append("overall_status must be pass, partial_blocked or blocked.")

    public_safety = report.get("public_safety")
    if not isinstance(public_safety, dict):
        errors.append("public_safety must be an object.")
    else:
        for flag in sorted(FORBIDDEN_PUBLIC_FLAGS):
            if public_safety.get(flag) is not False:
                errors.append(f"public_safety.{flag} must be false.")
        if public_safety.get("public_report_contains_only_aliases_counts_and_categories") is not True:
            errors.append("public_safety.public_report_contains_only_aliases_counts_and_categories must be true.")

    gate = report.get("exploratory_evidence_intake_gate")
    if not isinstance(gate, dict):
        errors.append("exploratory_evidence_intake_gate must be an object.")
    elif gate.get("status") != "blocked_missing_prod_conditional_prerequisites":
        errors.append("exploratory_evidence_intake_gate.status must remain blocked without approvals.")

    errors.extend(_public_safety_findings(report))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TASK-036 API-layer exhaustive offline coverage.")
    parser.add_argument("--task028-report", type=Path, required=True, help="Tracked public-safe TASK-028 summary JSON.")
    parser.add_argument("--pack-root", type=Path, help="Optional ignored local API quarantine pack root.")
    parser.add_argument("--report", type=Path, help="Optional TASK-036 public-safe summary output path.")
    args = parser.parse_args(argv)

    report = build_report(args.task028_report, args.pack_root)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "validation_status": report["overall_status"],
        "blocked_reason_count": len(report.get("blocked_reasons", [])),
        "local_pack_crosscheck_status": report.get("local_pack_crosscheck", {}).get("status"),
        "matrix_rows": report.get("source_summary", {}).get("matrix_rows"),
        "report_path": args.report.as_posix() if args.report else None,
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 1 if report["overall_status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
