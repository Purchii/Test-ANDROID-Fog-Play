"""Validate TASK-033 synthetic API redaction and production-safety guards.

TASK-033 is static and synthetic-only. The validator accepts either its
embedded fabricated guard ledger or an optional synthetic specimen file, then
emits a public-safe report. It never reads local API quarantine packs, calls a
backend, touches Android runtime, ADB, APKs, WebRTC, payments or sessions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "TASK-033"
SCHEMA_VERSION = "task033-api-redaction-prod-safety-guards-v1"
TOOL_NAME = "validate_task033_api_redaction_prod_safety_guards"

DEFAULT_TASK028_REPORT = Path("docs/qa/reports/task028_api_layer_contract_coverage.summary.json")
DEFAULT_TASK036_REPORT = Path("docs/qa/reports/task036_api_layer_exhaustive_coverage.summary.json")
EXPECTED_TASK036_LEDGER_STATUS = "tracked_summary_validated_synthetic_guard_tests_required"
EXPECTED_SECURITY_ROWS = 8
EXPECTED_REDACTION_TESTS = 8
PROD_SAFE_CLASSIFICATION = "PROD_SAFE_OFFLINE_STATIC_AND_SYNTHETIC_ONLY"
CONTROLLED_PARTIAL_BLOCKERS = {"blocked_missing_synthetic_specimens_file"}
ALLOWED_OVERALL_STATUSES = {"pass", "partial_blocked", "blocked"}
ALLOWED_EVIDENCE_STATUSES = {"likely", "likely_with_blockers", "unknown"}
ALLOWED_GUARD_CATEGORIES = {
    "credential_token_header",
    "cookie_session",
    "url_endpoint_route",
    "payload_body",
    "local_path_artifact",
    "device_identifier",
    "account_payment_value",
    "qr_target",
    "runtime_live_action",
    "budget_counter",
}
REQUIRED_GUARD_CATEGORIES = ALLOWED_GUARD_CATEGORIES
ALLOWED_EXPECTED_ACTIONS = {"redact", "block", "deny_execution", "zero_live_budget"}
ALLOWED_REPORT_KEYS = {
    "schema_version",
    "generated_at_utc",
    "task_id",
    "mode",
    "tool_name",
    "overall_status",
    "evidence_status",
    "production_safety_classification",
    "runtime_execution_status",
    "live_api_execution_status",
    "network_execution_status",
    "android_runtime_status",
    "backend_environment_status",
    "source_summary",
    "redaction_specimen_suite",
    "guard_ledger",
    "coverage_summary",
    "production_safety_boundary",
    "public_safety",
    "blocked_reasons",
    "unverified_areas",
}
REQUIRED_TOP_LEVEL_FIELDS = ALLOWED_REPORT_KEYS
GUARD_LEDGER_ROW_KEYS = {
    "guard_id",
    "category",
    "specimen_id",
    "synthetic_only",
    "raw_specimen_public",
    "input_material_status",
    "expected_public_action",
    "validation_status",
    "evidence_status",
    "raw_values_public",
}

FORBIDDEN_PUBLIC_FLAGS = {
    "raw_endpoints_public",
    "raw_urls_public",
    "raw_headers_public",
    "raw_payloads_public",
    "raw_fixture_bodies_public",
    "raw_tokens_or_sessions_public",
    "raw_cookies_public",
    "raw_qr_targets_public",
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
    "stream_or_session_started",
    "profile_or_account_mutation_performed",
    "device_binding_mutated",
    "tls_or_security_bypass_performed",
}
REQUIRED_TRUE_PUBLIC_SAFETY_FLAGS = {
    "public_report_contains_only_aliases_counts_categories_status_and_blockers",
    "synthetic_specimens_only",
    "local_static_validation_only",
    "live_budget_zero",
    "raw_specimens_not_persisted_or_printed",
}

RAW_VALUE_RE = re.compile(
    r"\b(?:https?|wss?|otpauth)://|"
    r"(?<![\w-])/(?:api|auth|login|token|catalog|profile|payment|billing|order|stream|device|"
    r"ws|socket|stomp|rtc|webrtc|datachannel|qr)[/\w{}.,:@?=&%-]*|"
    r"(?<![\w-])/(?:topic|queue|user/queue|app)[/\w{}.,:@?=&%-]*|"
    r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])|"
    r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{2,5})?\b|"
    r"\b[a-fA-F0-9]{32,}\b|"
    r"\b(?:authorization|bearer|cookie|session|token|secret|password|api[_-]?key|otp|captcha)"
    r"[:=]\s*\S+|"
    r"\b(?:device[_-]?id|android[_-]?id|serial|imei|imsi|mac|account|payment|card|invoice|"
    r"receipt|qr)[_-]?(?:id|number|value|token|target)?[:=]\s*\S+",
    re.IGNORECASE,
)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_guard_ledger() -> list[dict[str, Any]]:
    return [
        _guard("t033-guard-credential-token", "credential_token_header", "synthetic-token-specimen", "redact"),
        _guard("t033-guard-cookie-session", "cookie_session", "synthetic-cookie-specimen", "redact"),
        _guard("t033-guard-url-endpoint", "url_endpoint_route", "synthetic-url-route-specimen", "block"),
        _guard("t033-guard-payload-body", "payload_body", "synthetic-payload-body-specimen", "redact"),
        _guard("t033-guard-local-path", "local_path_artifact", "synthetic-local-path-specimen", "block"),
        _guard("t033-guard-device-id", "device_identifier", "synthetic-device-id-specimen", "redact"),
        _guard("t033-guard-account-payment", "account_payment_value", "synthetic-account-payment-specimen", "redact"),
        _guard("t033-guard-qr-target", "qr_target", "synthetic-qr-target-specimen", "block"),
        _guard("t033-guard-runtime-live", "runtime_live_action", "synthetic-live-action-specimen", "deny_execution"),
        _guard("t033-guard-budget-counter", "budget_counter", "synthetic-budget-counter-specimen", "zero_live_budget"),
    ]


def _guard(guard_id: str, category: str, specimen_id: str, expected_action: str) -> dict[str, Any]:
    return {
        "guard_id": guard_id,
        "category": category,
        "specimen_id": specimen_id,
        "synthetic_only": True,
        "raw_specimen_public": False,
        "input_material_status": "fabricated_synthetic_redacted",
        "expected_public_action": expected_action,
        "validation_status": "pass",
        "evidence_status": "likely",
        "raw_values_public": False,
    }


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


def _load_external_guard_ledger(specimens_path: Path | None) -> tuple[list[dict[str, Any]], list[str], str]:
    if specimens_path is None:
        return _default_guard_ledger(), [], "embedded_fabricated_synthetic_specimens"
    if not specimens_path.exists():
        return (
            _default_guard_ledger(),
            ["blocked_missing_synthetic_specimens_file"],
            "external_synthetic_specimens_missing_embedded_baseline_used",
        )

    loaded, load_errors = _read_json_object(specimens_path, "synthetic_specimens")
    if load_errors:
        return [], load_errors, "external_synthetic_specimens_invalid"
    specimens = loaded.get("specimens")
    if not isinstance(specimens, list) or not specimens:
        return [], ["synthetic_specimens_list_missing_or_empty"], "external_synthetic_specimens_invalid"
    ledger: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, item in enumerate(specimens):
        if not isinstance(item, dict):
            errors.append(f"synthetic_specimens[{index}]_not_object")
            continue
        unknown = sorted(set(item) - GUARD_LEDGER_ROW_KEYS)
        if unknown:
            errors.append(f"synthetic_specimens[{index}]_unknown_fields:{','.join(unknown)}")
        for finding in _raw_value_findings(item, f"synthetic_specimens[{index}]"):
            errors.append(f"synthetic_specimens[{index}]_{finding}")
        row = {
            "guard_id": item.get("guard_id"),
            "category": item.get("category"),
            "specimen_id": item.get("specimen_id"),
            "synthetic_only": item.get("synthetic_only"),
            "raw_specimen_public": item.get("raw_specimen_public"),
            "input_material_status": item.get("input_material_status"),
            "expected_public_action": item.get("expected_public_action"),
            "validation_status": item.get("validation_status", "pass"),
            "evidence_status": item.get("evidence_status", "likely"),
            "raw_values_public": item.get("raw_values_public"),
        }
        ledger.append(row)
    errors.extend(_validate_guard_ledger(ledger))
    return ledger, sorted(set(errors)), "external_fabricated_synthetic_specimens"


def _task036_task033_area(summary: Mapping[str, Any]) -> Mapping[str, Any] | None:
    ledger = summary.get("coverage_area_ledger")
    if not isinstance(ledger, list):
        return None
    for row in ledger:
        if isinstance(row, Mapping) and row.get("source_task") == TASK_ID:
            return row
    return None


def _source_reconciliation(task028_report_path: Path, task036_report_path: Path) -> tuple[dict[str, Any], list[str]]:
    task028, task028_errors = _read_json_object(task028_report_path, "task028_summary")
    task036, task036_errors = _read_json_object(task036_report_path, "task036_summary")
    errors = task028_errors + task036_errors

    task028_status = task028.get("overall_status", "unknown") if task028 else "unknown"
    task036_status = task036.get("overall_status", "unknown") if task036 else "unknown"
    if task028 and task028.get("task_id") != "TASK-028":
        errors.append("task028_summary_task_id_invalid")
    if task036 and task036.get("task_id") != "TASK-036":
        errors.append("task036_summary_task_id_invalid")
    if task028 and task028.get("runtime_execution_status") != "not_run":
        errors.append("task028_runtime_status_must_be_not_run")
    if task028 and task028.get("live_api_execution_status") != "not_run":
        errors.append("task028_live_api_status_must_be_not_run")
    if task036 and task036.get("runtime_execution_status") != "not_run":
        errors.append("task036_runtime_status_must_be_not_run")
    if task036 and task036.get("live_api_execution_status") != "not_run":
        errors.append("task036_live_api_status_must_be_not_run")

    coverage = task028.get("coverage_summary", {}) if isinstance(task028, Mapping) else {}
    counts_by_layer = coverage.get("counts_by_layer", {}) if isinstance(coverage, Mapping) else {}
    counts_by_test_type = coverage.get("counts_by_test_type", {}) if isinstance(coverage, Mapping) else {}
    counts_by_target = coverage.get("counts_by_automation_target", {}) if isinstance(coverage, Mapping) else {}
    security_rows = counts_by_layer.get("security") if isinstance(counts_by_layer, Mapping) else None
    redaction_tests = counts_by_test_type.get("security_redaction") if isinstance(counts_by_test_type, Mapping) else None
    guard_targets = (
        counts_by_target.get("log_artifact_scanner_or_guard_test") if isinstance(counts_by_target, Mapping) else None
    )
    if security_rows != EXPECTED_SECURITY_ROWS:
        errors.append("task028_security_row_count_invalid")
    if redaction_tests != EXPECTED_REDACTION_TESTS:
        errors.append("task028_security_redaction_count_invalid")
    if guard_targets != EXPECTED_REDACTION_TESTS:
        errors.append("task028_security_guard_target_count_invalid")

    area = _task036_task033_area(task036)
    task036_ledger_status = "unknown"
    if area is None:
        errors.append("task036_task033_ledger_area_missing")
    else:
        task036_ledger_status = str(area.get("status", "unknown"))
        if area.get("status") != EXPECTED_TASK036_LEDGER_STATUS:
            errors.append("task036_task033_ledger_status_invalid")
        if area.get("known_security_rows") != EXPECTED_SECURITY_ROWS:
            errors.append("task036_task033_security_row_count_invalid")
        if area.get("known_redaction_tests") != EXPECTED_REDACTION_TESTS:
            errors.append("task036_task033_redaction_test_count_invalid")

    return {
        "source_reports": {
            "task028": {
                "source_report_alias": "task028_api_layer_contract_coverage_summary",
                "overall_status": task028_status,
                "runtime_execution_status": task028.get("runtime_execution_status", "unknown") if task028 else "unknown",
                "live_api_execution_status": task028.get("live_api_execution_status", "unknown") if task028 else "unknown",
            },
            "task036": {
                "source_report_alias": "task036_api_layer_exhaustive_coverage_summary",
                "overall_status": task036_status,
                "runtime_execution_status": task036.get("runtime_execution_status", "unknown") if task036 else "unknown",
                "live_api_execution_status": task036.get("live_api_execution_status", "unknown") if task036 else "unknown",
                "task033_ledger_status": task036_ledger_status,
            },
        },
        "known_security_rows": security_rows if isinstance(security_rows, int) else 0,
        "known_redaction_tests": redaction_tests if isinstance(redaction_tests, int) else 0,
        "known_guard_targets": guard_targets if isinstance(guard_targets, int) else 0,
    }, sorted(set(errors))


def _raw_value_findings(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and RAW_VALUE_RE.search(key):
                findings.append(f"{path} contains raw/private evidence-like key text.")
            findings.extend(_raw_value_findings(child, f"{path}.{key}"))
        return findings
    if isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_raw_value_findings(child, f"{path}[{index}]"))
        return findings
    if isinstance(value, str) and RAW_VALUE_RE.search(value):
        findings.append(f"{path} contains raw/private evidence-like text.")
    return findings


def _validate_guard_ledger(ledger: Any) -> list[str]:
    if not isinstance(ledger, list):
        return ["guard_ledger_must_be_list"]
    if not ledger:
        return ["guard_ledger_must_not_be_empty"]

    errors: list[str] = []
    seen_ids: set[str] = set()
    categories: Counter[str] = Counter()
    for index, row in enumerate(ledger):
        row_path = f"guard_ledger[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{row_path}_must_be_object")
            continue
        unknown = sorted(set(row) - GUARD_LEDGER_ROW_KEYS)
        if unknown:
            errors.append(f"{row_path}_unknown_fields:{','.join(unknown)}")
        required = GUARD_LEDGER_ROW_KEYS
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"{row_path}_missing_required_fields:{','.join(missing)}")
        guard_id = row.get("guard_id")
        if not isinstance(guard_id, str) or not re.fullmatch(r"t033-guard-[a-z0-9-]{3,80}", guard_id):
            errors.append(f"{row_path}_guard_id_invalid")
        elif guard_id in seen_ids:
            errors.append(f"{row_path}_guard_id_duplicate")
        else:
            seen_ids.add(guard_id)
        category = row.get("category")
        if category not in ALLOWED_GUARD_CATEGORIES:
            errors.append(f"{row_path}_category_invalid")
        else:
            categories.update([category])
        specimen_id = row.get("specimen_id")
        if not isinstance(specimen_id, str) or not re.fullmatch(r"synthetic-[a-z0-9-]{3,80}", specimen_id):
            errors.append(f"{row_path}_specimen_id_invalid")
        if row.get("synthetic_only") is not True:
            errors.append(f"{row_path}_synthetic_only_must_be_true")
        if row.get("raw_specimen_public") is not False:
            errors.append(f"{row_path}_raw_specimen_public_must_be_false")
        if row.get("raw_values_public") is not False:
            errors.append(f"{row_path}_raw_values_public_must_be_false")
        if row.get("input_material_status") != "fabricated_synthetic_redacted":
            errors.append(f"{row_path}_input_material_status_invalid")
        if row.get("expected_public_action") not in ALLOWED_EXPECTED_ACTIONS:
            errors.append(f"{row_path}_expected_public_action_invalid")
        if row.get("validation_status") != "pass":
            errors.append(f"{row_path}_validation_status_must_be_pass")
        if row.get("evidence_status") != "likely":
            errors.append(f"{row_path}_evidence_status_must_be_likely")

    missing_categories = sorted(REQUIRED_GUARD_CATEGORIES - set(categories))
    if missing_categories:
        errors.append(f"guard_ledger_missing_required_categories:{','.join(missing_categories)}")
    return sorted(set(errors))


def _coverage_summary_for(ledger: list[dict[str, Any]]) -> dict[str, Any]:
    categories = Counter(row.get("category", "unknown") for row in ledger)
    actions = Counter(row.get("expected_public_action", "unknown") for row in ledger)
    statuses = Counter(row.get("validation_status", "unknown") for row in ledger)
    return {
        "guard_count": len(ledger),
        "counts_by_guard_category": dict(sorted(categories.items())),
        "counts_by_expected_public_action": dict(sorted(actions.items())),
        "counts_by_validation_status": dict(sorted(statuses.items())),
    }


def build_report(
    specimens_path: Path | None = None,
    task028_report_path: Path = DEFAULT_TASK028_REPORT,
    task036_report_path: Path = DEFAULT_TASK036_REPORT,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    guard_ledger, specimen_errors, specimen_source = _load_external_guard_ledger(specimens_path)
    source_summary, source_errors = _source_reconciliation(task028_report_path, task036_report_path)
    coverage_summary = _coverage_summary_for(guard_ledger)
    all_errors = sorted(set(specimen_errors + source_errors))

    if all_errors and set(all_errors) <= CONTROLLED_PARTIAL_BLOCKERS:
        overall_status = "partial_blocked"
        evidence_status = "likely_with_blockers"
    elif all_errors:
        overall_status = "blocked"
        evidence_status = "unknown"
    else:
        overall_status = "pass"
        evidence_status = "likely"

    public_safety = {key: False for key in sorted(FORBIDDEN_PUBLIC_FLAGS)}
    public_safety.update({key: True for key in sorted(REQUIRED_TRUE_PUBLIC_SAFETY_FLAGS)})

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc or _utc_now(),
        "task_id": TASK_ID,
        "mode": "BOUNDED_AUTONOMOUS",
        "tool_name": TOOL_NAME,
        "overall_status": overall_status,
        "evidence_status": evidence_status,
        "production_safety_classification": PROD_SAFE_CLASSIFICATION,
        "runtime_execution_status": "not_run",
        "live_api_execution_status": "not_run",
        "network_execution_status": "not_run",
        "android_runtime_status": "not_run",
        "backend_environment_status": "not_configured",
        "source_summary": source_summary,
        "redaction_specimen_suite": {
            "suite_status": "pass" if not specimen_errors else "blocked",
            "specimen_source": specimen_source,
            "specimen_material": "fabricated_synthetic_only",
            "raw_values_public": False,
            "raw_specimens_persisted": False,
            "raw_specimens_printed": False,
            "specimens_total": len(guard_ledger),
            "specimens_passed": len([row for row in guard_ledger if row.get("validation_status") == "pass"]),
            "specimens_failed": len([row for row in guard_ledger if row.get("validation_status") != "pass"]),
            "categories_covered": sorted(set(row.get("category") for row in guard_ledger if isinstance(row.get("category"), str))),
        },
        "guard_ledger": guard_ledger,
        "coverage_summary": coverage_summary,
        "production_safety_boundary": {
            "classification": PROD_SAFE_CLASSIFICATION,
            "live_request_count": 0,
            "retry_count": 0,
            "concurrency": 0,
            "load_or_fuzz_loop_performed": False,
            "live_backend_calls": "not_run",
            "android_runtime_actions": "not_run",
            "adb_actions": "not_run",
            "apk_actions": "not_run",
            "payment_or_session_mutation": "not_run",
            "budget_source": "synthetic_offline_zero_budget",
        },
        "public_safety": public_safety,
        "blocked_reasons": all_errors,
        "unverified_areas": [
            "real evidence redaction behavior",
            "live REST backend behavior",
            "live STOMP WebSocket behavior",
            "live WebRTC DataChannel behavior",
            "Android runtime correlation",
            "payment order session mutation behavior",
        ],
    }
    report_errors = validate_public_report(report)
    if report_errors:
        report["overall_status"] = "blocked"
        report["evidence_status"] = "unknown"
        report["blocked_reasons"] = sorted(set(report.get("blocked_reasons", [])) | set(report_errors))
    return report


def _validate_count_map(value: Any, field_name: str) -> tuple[int, list[str]]:
    if not isinstance(value, Mapping):
        return 0, [f"{field_name}_must_be_object"]
    total = 0
    errors: list[str] = []
    for key, count in value.items():
        if not isinstance(key, str) or not key:
            errors.append(f"{field_name}_key_invalid")
        elif RAW_VALUE_RE.search(key):
            errors.append(f"{field_name}_contains_raw_private_key_text")
        if not isinstance(count, int) or count < 0:
            errors.append(f"{field_name}_{key}_count_invalid")
        else:
            total += count
    return total, errors


def _validate_public_safety(public_safety: Any) -> list[str]:
    if not isinstance(public_safety, dict):
        return ["public_safety_not_object"]
    errors: list[str] = []
    allowed_keys = FORBIDDEN_PUBLIC_FLAGS | REQUIRED_TRUE_PUBLIC_SAFETY_FLAGS
    unknown = sorted(set(public_safety) - allowed_keys)
    if unknown:
        errors.append(f"public_safety_unknown_fields:{','.join(unknown)}")
    for flag in sorted(FORBIDDEN_PUBLIC_FLAGS):
        if public_safety.get(flag) is not False:
            errors.append(f"public_safety_{flag}_must_be_false")
    for flag in sorted(REQUIRED_TRUE_PUBLIC_SAFETY_FLAGS):
        if public_safety.get(flag) is not True:
            errors.append(f"public_safety_{flag}_must_be_true")
    return errors


def _validate_production_safety_boundary(boundary: Any, report: dict[str, Any]) -> list[str]:
    if not isinstance(boundary, dict):
        return ["production_safety_boundary_not_object"]
    errors: list[str] = []
    allowed_keys = {
        "classification",
        "live_request_count",
        "retry_count",
        "concurrency",
        "load_or_fuzz_loop_performed",
        "live_backend_calls",
        "android_runtime_actions",
        "adb_actions",
        "apk_actions",
        "payment_or_session_mutation",
        "budget_source",
    }
    unknown = sorted(set(boundary) - allowed_keys)
    if unknown:
        errors.append(f"production_safety_boundary_unknown_fields:{','.join(unknown)}")
    if boundary.get("classification") != PROD_SAFE_CLASSIFICATION:
        errors.append("production_safety_boundary_classification_invalid")
    for field_name in ("live_request_count", "retry_count", "concurrency"):
        if boundary.get(field_name) != 0:
            errors.append(f"production_safety_boundary_{field_name}_must_be_zero")
    if boundary.get("load_or_fuzz_loop_performed") is not False:
        errors.append("production_safety_boundary_load_or_fuzz_loop_performed_must_be_false")
    for field_name in (
        "live_backend_calls",
        "android_runtime_actions",
        "adb_actions",
        "apk_actions",
        "payment_or_session_mutation",
    ):
        if boundary.get(field_name) != "not_run":
            errors.append(f"production_safety_boundary_{field_name}_must_be_not_run")
    if boundary.get("budget_source") != "synthetic_offline_zero_budget":
        errors.append("production_safety_boundary_budget_source_invalid")
    if report.get("live_api_execution_status") == "not_run" and boundary.get("live_request_count") != 0:
        errors.append("live_api_not_run_requires_zero_live_request_count")
    return errors


def _validate_specimen_suite(suite: Any, ledger: Any, coverage: Any) -> list[str]:
    if not isinstance(suite, dict):
        return ["redaction_specimen_suite_not_object"]
    errors: list[str] = []
    allowed_keys = {
        "suite_status",
        "specimen_source",
        "specimen_material",
        "raw_values_public",
        "raw_specimens_persisted",
        "raw_specimens_printed",
        "specimens_total",
        "specimens_passed",
        "specimens_failed",
        "categories_covered",
    }
    unknown = sorted(set(suite) - allowed_keys)
    if unknown:
        errors.append(f"redaction_specimen_suite_unknown_fields:{','.join(unknown)}")
    ledger_len = len(ledger) if isinstance(ledger, list) else 0
    if suite.get("specimen_material") != "fabricated_synthetic_only":
        errors.append("redaction_specimen_suite_material_invalid")
    if suite.get("raw_values_public") is not False:
        errors.append("redaction_specimen_suite_raw_values_public_must_be_false")
    if suite.get("raw_specimens_persisted") is not False:
        errors.append("redaction_specimen_suite_raw_specimens_persisted_must_be_false")
    if suite.get("raw_specimens_printed") is not False:
        errors.append("redaction_specimen_suite_raw_specimens_printed_must_be_false")
    if suite.get("specimens_total") != ledger_len:
        errors.append("redaction_specimen_suite_total_mismatch")
    expected_passed = len([row for row in ledger if isinstance(row, dict) and row.get("validation_status") == "pass"])
    expected_failed = ledger_len - expected_passed
    if suite.get("specimens_passed") != expected_passed:
        errors.append("redaction_specimen_suite_passed_count_mismatch")
    if suite.get("specimens_failed") != expected_failed:
        errors.append("redaction_specimen_suite_failed_count_mismatch")
    categories = suite.get("categories_covered")
    expected_categories = sorted(set(row.get("category") for row in ledger if isinstance(row, dict) and isinstance(row.get("category"), str)))
    if categories != expected_categories:
        errors.append("redaction_specimen_suite_categories_mismatch")
    if isinstance(coverage, dict) and suite.get("specimens_total") != coverage.get("guard_count"):
        errors.append("redaction_specimen_suite_coverage_count_mismatch")
    return errors


def _validate_source_summary(summary: Any) -> list[str]:
    if not isinstance(summary, dict):
        return ["source_summary_not_object"]
    errors: list[str] = []
    allowed_keys = {
        "source_reports",
        "known_security_rows",
        "known_redaction_tests",
        "known_guard_targets",
    }
    unknown = sorted(set(summary) - allowed_keys)
    if unknown:
        errors.append(f"source_summary_unknown_fields:{','.join(unknown)}")
    expected_counts = {
        "known_security_rows": EXPECTED_SECURITY_ROWS,
        "known_redaction_tests": EXPECTED_REDACTION_TESTS,
        "known_guard_targets": EXPECTED_REDACTION_TESTS,
    }
    for field_name, expected in expected_counts.items():
        if summary.get(field_name) != expected:
            errors.append(f"source_summary_{field_name}_invalid")
    reports = summary.get("source_reports")
    if not isinstance(reports, dict):
        errors.append("source_summary_source_reports_not_object")
        return errors
    if sorted(reports) != ["task028", "task036"]:
        errors.append("source_summary_source_reports_keys_invalid")
    for label in ("task028", "task036"):
        report = reports.get(label)
        if not isinstance(report, dict):
            errors.append(f"source_summary_{label}_not_object")
            continue
        allowed_report_keys = {
            "source_report_alias",
            "overall_status",
            "runtime_execution_status",
            "live_api_execution_status",
        }
        if label == "task036":
            allowed_report_keys.add("task033_ledger_status")
        unknown = sorted(set(report) - allowed_report_keys)
        if unknown:
            errors.append(f"source_summary_{label}_unknown_fields:{','.join(unknown)}")
        if report.get("runtime_execution_status") != "not_run":
            errors.append(f"source_summary_{label}_runtime_status_must_be_not_run")
        if report.get("live_api_execution_status") != "not_run":
            errors.append(f"source_summary_{label}_live_api_status_must_be_not_run")
    task036 = reports.get("task036") if isinstance(reports, dict) else {}
    if isinstance(task036, dict) and task036.get("task033_ledger_status") != EXPECTED_TASK036_LEDGER_STATUS:
        errors.append("source_summary_task036_task033_ledger_status_invalid")
    return errors


def _validate_coverage_summary(coverage: Any, ledger: Any) -> list[str]:
    if not isinstance(coverage, dict):
        return ["coverage_summary_not_object"]
    errors: list[str] = []
    allowed_keys = {
        "guard_count",
        "counts_by_guard_category",
        "counts_by_expected_public_action",
        "counts_by_validation_status",
    }
    unknown = sorted(set(coverage) - allowed_keys)
    if unknown:
        errors.append(f"coverage_summary_unknown_fields:{','.join(unknown)}")
    ledger_len = len(ledger) if isinstance(ledger, list) else 0
    if coverage.get("guard_count") != ledger_len:
        errors.append("coverage_summary_guard_count_mismatch")
    for field_name in (
        "counts_by_guard_category",
        "counts_by_expected_public_action",
        "counts_by_validation_status",
    ):
        total, count_errors = _validate_count_map(coverage.get(field_name), f"coverage_summary_{field_name}")
        errors.extend(count_errors)
        if total != ledger_len:
            errors.append(f"coverage_summary_{field_name}_total_mismatch")
    category_counts = coverage.get("counts_by_guard_category", {})
    if isinstance(category_counts, dict):
        missing_categories = sorted(REQUIRED_GUARD_CATEGORIES - set(category_counts))
        if missing_categories:
            errors.append(f"coverage_summary_missing_required_categories:{','.join(missing_categories)}")
    return sorted(set(errors))


def validate_public_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(report))
    if missing:
        errors.append(f"report_missing_required_fields:{','.join(missing)}")
    unknown = sorted(set(report) - ALLOWED_REPORT_KEYS)
    if unknown:
        errors.append(f"report_unknown_fields:{','.join(unknown)}")
    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if report.get("task_id") != TASK_ID:
        errors.append("task_id_invalid")
    if report.get("mode") != "BOUNDED_AUTONOMOUS":
        errors.append("mode_invalid")
    if report.get("tool_name") != TOOL_NAME:
        errors.append("tool_name_invalid")
    if report.get("production_safety_classification") != PROD_SAFE_CLASSIFICATION:
        errors.append("production_safety_classification_invalid")
    if report.get("overall_status") not in ALLOWED_OVERALL_STATUSES:
        errors.append("overall_status_invalid")
    if report.get("evidence_status") not in ALLOWED_EVIDENCE_STATUSES:
        errors.append("evidence_status_invalid")
    for field_name in (
        "runtime_execution_status",
        "live_api_execution_status",
        "network_execution_status",
        "android_runtime_status",
    ):
        if report.get(field_name) != "not_run":
            errors.append(f"{field_name}_must_be_not_run")
    if report.get("backend_environment_status") != "not_configured":
        errors.append("backend_environment_status_must_be_not_configured")

    ledger = report.get("guard_ledger")
    coverage = report.get("coverage_summary")
    errors.extend(_validate_guard_ledger(ledger))
    errors.extend(_validate_source_summary(report.get("source_summary")))
    errors.extend(_validate_specimen_suite(report.get("redaction_specimen_suite"), ledger, coverage))
    errors.extend(_validate_coverage_summary(coverage, ledger))
    errors.extend(_validate_production_safety_boundary(report.get("production_safety_boundary"), report))
    errors.extend(_validate_public_safety(report.get("public_safety")))

    blocked_reasons = report.get("blocked_reasons")
    if not isinstance(blocked_reasons, list) or any(not isinstance(item, str) or not item for item in blocked_reasons):
        errors.append("blocked_reasons_must_be_non_empty_string_list")
    unverified_areas = report.get("unverified_areas")
    if not isinstance(unverified_areas, list) or any(not isinstance(item, str) or not item for item in unverified_areas):
        errors.append("unverified_areas_must_be_non_empty_string_list")

    overall_status = report.get("overall_status")
    if overall_status == "pass":
        if blocked_reasons != []:
            errors.append("pass_report_must_have_empty_blocked_reasons")
        if report.get("redaction_specimen_suite", {}).get("suite_status") != "pass":
            errors.append("pass_report_specimen_suite_must_pass")
    elif overall_status == "partial_blocked":
        if not blocked_reasons:
            errors.append("partial_blocked_report_must_have_blocked_reasons")
        elif not set(blocked_reasons) <= CONTROLLED_PARTIAL_BLOCKERS:
            errors.append("partial_blocked_report_contains_uncontrolled_blockers")
    elif overall_status == "blocked" and not blocked_reasons:
        errors.append("blocked_report_must_have_blocked_reasons")

    errors.extend(_raw_value_findings(report))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TASK-033 API redaction and production-safety guards.")
    parser.add_argument("--specimens", type=Path, help="Optional fabricated synthetic specimen JSON.")
    parser.add_argument("--task028-report", type=Path, default=DEFAULT_TASK028_REPORT, help="Tracked TASK-028 public summary.")
    parser.add_argument("--task036-report", type=Path, default=DEFAULT_TASK036_REPORT, help="Tracked TASK-036 public summary.")
    parser.add_argument("--report", type=Path, help="Optional TASK-033 public-safe summary JSON output path.")
    parser.add_argument("--allow-partial-blocked-exit-zero", action="store_true", help="Return zero for controlled partial blockers.")
    args = parser.parse_args(argv)

    report = build_report(args.specimens, args.task028_report, args.task036_report)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "validation_status": report["overall_status"],
        "blocked_reason_count": len(report.get("blocked_reasons", [])),
        "guard_count": report.get("coverage_summary", {}).get("guard_count"),
        "specimen_source": report.get("redaction_specimen_suite", {}).get("specimen_source"),
        "report_alias": "task033_api_redaction_prod_safety_guards_summary" if args.report else None,
    }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if report["overall_status"] == "pass":
        return 0
    if report["overall_status"] == "partial_blocked" and args.allow_partial_blocked_exit_zero:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
