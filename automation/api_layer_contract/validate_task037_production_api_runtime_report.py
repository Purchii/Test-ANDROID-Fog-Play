"""Validate TASK-037 public-safe production API/runtime exploratory report.

The TASK-037 report may summarize bounded live/read-only coverage, but it must
never publish raw endpoints, device identifiers, local paths, tokens, payloads
or private values. Raw captures belong only under ignored local evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


TASK_ID = "TASK-037"
SCHEMA_VERSION = "task037-production-api-runtime-exploratory-v1"
TOOL_NAME = "validate_task037_production_api_runtime_report"

ALLOWED_OVERALL_STATUSES = {
    "blocked_pending_preflight",
    "blocked_preflight_failed",
    "partial_blocked",
    "partial_read_only_covered",
    "pass_read_only_safe_lane",
}
ALLOWED_EXECUTION_STATUSES = {
    "not_run",
    "blocked_by_preflight",
    "blocked_by_boundary",
    "blocked_by_tooling",
    "blocked_by_external_state",
    "covered",
    "unknown_not_verified",
}
ALLOWED_EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
ALLOWED_API_CATEGORIES = {
    "config",
    "catalog",
    "reference_dictionary",
    "available_status",
    "synthetic_profile_status",
    "synthetic_entitlement_status",
    "auth_session_bootstrap",
}
ALLOWED_RUNTIME_CATEGORIES = {
    "app_launch",
    "current_screen_alias",
    "screenshot_xml_checkpoint",
    "log_snippet_check",
    "boundary_recovery",
    "external_system_recovery",
}
FORBIDDEN_BOUNDARY_CATEGORIES = {
    "stream_start",
    "order",
    "payment",
    "profile_account_mutation",
    "device_binding_mutation",
    "destructive_revoke_update_delete",
}
FORBIDDEN_PUBLIC_FLAGS = {
    "raw_endpoints_public",
    "raw_urls_public",
    "raw_headers_public",
    "raw_payloads_public",
    "raw_cookies_public",
    "raw_tokens_or_sessions_public",
    "raw_qr_targets_public",
    "raw_device_identifiers_public",
    "raw_local_paths_public",
    "raw_secrets_public",
    "real_user_data_public",
    "mutation_performed",
    "stream_or_session_started",
    "order_or_payment_performed",
    "device_binding_mutated",
    "tls_or_security_bypass_performed",
    "apk_modified_or_decompiled",
}
REQUIRED_TOP_LEVEL_FIELDS = {
    "task_id",
    "schema_version",
    "tool_name",
    "mode",
    "production_safety_classification",
    "overall_status",
    "evidence_status",
    "runtime_execution_status",
    "live_api_execution_status",
    "safe_lane",
    "budget",
    "preflight",
    "coverage_summary",
    "api_coverage_ledger",
    "runtime_coverage_ledger",
    "boundary_ledger",
    "anomaly_ledger",
    "public_safety",
    "blocked_reasons",
    "unverified_areas",
}

RAW_VALUE_RE = re.compile(
    r"\b(?:https?|wss?)://|"
    r"(?<![\w-])/(?:api|auth|login|token|catalog|profile|payment|order|stream|device)[/\w{}.?=&%-]*|"
    r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])|"
    r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{2,5})?\b|"
    r"\b[a-fA-F0-9]{32,}\b|"
    r"\b(?:authorization|bearer|cookie|session|token|secret|password|api[_-]?key|otp|captcha)[:=]\s*\S+",
    re.IGNORECASE,
)


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return None, f"report JSON is malformed: {exc.msg}."
    except OSError as exc:
        return None, f"report JSON cannot be read: {exc}."
    if not isinstance(loaded, dict):
        return None, "report JSON must be an object."
    return loaded, None


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


def _validate_string_set(
    value: Any,
    field_name: str,
    allowed: set[str],
    *,
    required: bool = True,
) -> list[str]:
    if value is None and not required:
        return []
    if not isinstance(value, str):
        return [f"{field_name} must be a string."]
    if value not in allowed:
        return [f"{field_name} has unsupported value {value!r}."]
    return []


def _validate_count_map(value: Any, field_name: str) -> tuple[int, list[str]]:
    if not isinstance(value, Mapping):
        return 0, [f"{field_name} must be an object."]
    total = 0
    errors: list[str] = []
    for key, count in value.items():
        if not isinstance(key, str) or not key:
            errors.append(f"{field_name} contains an empty or non-string key.")
        elif RAW_VALUE_RE.search(key):
            errors.append(f"{field_name} contains raw/private evidence-like key text.")
        if not isinstance(count, int) or count < 0:
            errors.append(f"{field_name}.{key} must be a non-negative integer.")
        else:
            total += count
    return total, errors


def _validate_evidence_ids(value: Any, field_name: str, *, require_non_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        return [f"{field_name} must be a list."]
    errors: list[str] = []
    if require_non_empty and not value:
        errors.append(f"{field_name} must contain at least one evidence id.")
    for item in value:
        if not isinstance(item, str):
            errors.append(f"{field_name} items must be strings.")
        elif not re.fullmatch(r"rt037-[a-z0-9][a-z0-9-]{2,80}", item):
            errors.append(f"{field_name} contains invalid evidence id {item!r}.")
    return errors


def _validate_preflight(report: dict[str, Any]) -> list[str]:
    preflight = report.get("preflight")
    if not isinstance(preflight, dict):
        return ["preflight must be an object."]
    errors: list[str] = []
    required = {
        "owner_safe_lane_recorded",
        "synthetic_secret_preflight",
        "target_preflight",
        "raw_evidence_storage_preflight",
        "redaction_preflight",
        "forbidden_action_guard_preflight",
    }
    missing = sorted(required - set(preflight))
    if missing:
        errors.append(f"preflight missing required fields: {missing}.")
    if preflight.get("owner_safe_lane_recorded") is not True:
        errors.append("preflight.owner_safe_lane_recorded must be true.")
    for field_name in required - {"owner_safe_lane_recorded"}:
        value = preflight.get(field_name)
        if not isinstance(value, dict):
            errors.append(f"preflight.{field_name} must be an object.")
            continue
        errors.extend(
            _validate_string_set(
                value.get("status"),
                f"preflight.{field_name}.status",
                {"confirmed", "blocked", "not_run", "pass"},
            )
        )
        errors.extend(
            _validate_string_set(
                value.get("evidence_status"),
                f"preflight.{field_name}.evidence_status",
                ALLOWED_EVIDENCE_STATUSES,
            )
        )
        if value.get("raw_values_printed") is not False:
            errors.append(f"preflight.{field_name}.raw_values_printed must be false.")
    return errors


def _validate_safe_lane(report: dict[str, Any]) -> list[str]:
    safe_lane = report.get("safe_lane")
    if not isinstance(safe_lane, dict):
        return ["safe_lane must be an object."]
    errors: list[str] = []
    if safe_lane.get("environment") != "production":
        errors.append("safe_lane.environment must be production.")
    if safe_lane.get("target_alias") != "task037-approved-tv-target":
        errors.append("safe_lane.target_alias must be task037-approved-tv-target.")
    if safe_lane.get("target_raw_value_public") is not False:
        errors.append("safe_lane.target_raw_value_public must be false.")
    if safe_lane.get("synthetic_user_allowed") is not True:
        errors.append("safe_lane.synthetic_user_allowed must be true.")
    if safe_lane.get("raw_secret_values_public") is not False:
        errors.append("safe_lane.raw_secret_values_public must be false.")
    allowed_api_scope = safe_lane.get("allowed_api_scope")
    if not isinstance(allowed_api_scope, list) or not allowed_api_scope:
        errors.append("safe_lane.allowed_api_scope must be a non-empty list.")
    else:
        unsupported = sorted(set(allowed_api_scope) - ALLOWED_API_CATEGORIES)
        if unsupported:
            errors.append(f"safe_lane.allowed_api_scope contains unsupported categories: {unsupported}.")
    blocked_actions = safe_lane.get("blocked_actions")
    if not isinstance(blocked_actions, list):
        errors.append("safe_lane.blocked_actions must be a list.")
    else:
        missing = sorted(FORBIDDEN_BOUNDARY_CATEGORIES - set(blocked_actions))
        if missing:
            errors.append(f"safe_lane.blocked_actions missing forbidden categories: {missing}.")
    return errors


def _validate_budget(report: dict[str, Any]) -> list[str]:
    budget = report.get("budget")
    if not isinstance(budget, dict):
        return ["budget must be an object."]
    errors: list[str] = []
    if budget.get("concurrency") != 1:
        errors.append("budget.concurrency must be 1.")
    if budget.get("retry_cap") != 3:
        errors.append("budget.retry_cap must be 3.")
    if budget.get("load_or_fuzz_loop_performed") is not False:
        errors.append("budget.load_or_fuzz_loop_performed must be false.")
    requests = budget.get("total_live_request_count")
    if not isinstance(requests, int) or requests < 0:
        errors.append("budget.total_live_request_count must be a non-negative integer.")
    retries = budget.get("total_retry_count")
    if not isinstance(retries, int) or retries < 0 or retries > 3:
        errors.append("budget.total_retry_count must be an integer from 0 to 3.")
    return errors


def _validate_api_ledger(report: dict[str, Any]) -> list[str]:
    ledger = report.get("api_coverage_ledger")
    if not isinstance(ledger, list):
        return ["api_coverage_ledger must be a list."]
    errors: list[str] = []
    covered_count = 0
    for index, row in enumerate(ledger):
        row_path = f"api_coverage_ledger[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{row_path} must be an object.")
            continue
        errors.extend(_validate_string_set(row.get("category"), f"{row_path}.category", ALLOWED_API_CATEGORIES))
        errors.extend(
            _validate_string_set(row.get("execution_status"), f"{row_path}.execution_status", ALLOWED_EXECUTION_STATUSES)
        )
        errors.extend(
            _validate_string_set(row.get("evidence_status"), f"{row_path}.evidence_status", ALLOWED_EVIDENCE_STATUSES)
        )
        errors.extend(
            _validate_evidence_ids(
                row.get("evidence_ids"),
                f"{row_path}.evidence_ids",
                require_non_empty=row.get("execution_status") == "covered",
            )
        )
        request_count = row.get("request_count")
        retry_count = row.get("retry_count")
        if not isinstance(request_count, int) or request_count < 0:
            errors.append(f"{row_path}.request_count must be a non-negative integer.")
        if not isinstance(retry_count, int) or retry_count < 0 or retry_count > 3:
            errors.append(f"{row_path}.retry_count must be an integer from 0 to 3.")
        if row.get("mutation_performed") is not False:
            errors.append(f"{row_path}.mutation_performed must be false.")
        if row.get("raw_values_public") is not False:
            errors.append(f"{row_path}.raw_values_public must be false.")
        if row.get("execution_status") == "covered":
            covered_count += 1
    if report.get("live_api_execution_status") == "partial_read_only_covered" and covered_count == 0:
        errors.append("live_api_execution_status partial_read_only_covered requires at least one covered API row.")
    return errors


def _validate_runtime_ledger(report: dict[str, Any]) -> list[str]:
    ledger = report.get("runtime_coverage_ledger")
    if not isinstance(ledger, list):
        return ["runtime_coverage_ledger must be a list."]
    errors: list[str] = []
    covered_count = 0
    for index, row in enumerate(ledger):
        row_path = f"runtime_coverage_ledger[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{row_path} must be an object.")
            continue
        errors.extend(_validate_string_set(row.get("category"), f"{row_path}.category", ALLOWED_RUNTIME_CATEGORIES))
        errors.extend(
            _validate_string_set(row.get("execution_status"), f"{row_path}.execution_status", ALLOWED_EXECUTION_STATUSES)
        )
        errors.extend(
            _validate_string_set(row.get("evidence_status"), f"{row_path}.evidence_status", ALLOWED_EVIDENCE_STATUSES)
        )
        errors.extend(
            _validate_evidence_ids(
                row.get("evidence_ids"),
                f"{row_path}.evidence_ids",
                require_non_empty=row.get("execution_status") == "covered",
            )
        )
        if row.get("raw_values_public") is not False:
            errors.append(f"{row_path}.raw_values_public must be false.")
        checkpoint_fields = {
            "screen_alias",
            "state_category",
            "focus_action_category",
            "risk_hypothesis_note",
        }
        missing_checkpoint_fields = sorted(checkpoint_fields - set(row))
        if missing_checkpoint_fields:
            errors.append(f"{row_path} missing runtime checkpoint fields: {missing_checkpoint_fields}.")
        for field_name in checkpoint_fields & set(row):
            if not isinstance(row.get(field_name), str) or not row.get(field_name):
                errors.append(f"{row_path}.{field_name} must be a non-empty string.")
        if row.get("execution_status") == "covered":
            covered_count += 1
    if report.get("runtime_execution_status") == "partial_runtime_correlated" and covered_count == 0:
        errors.append("runtime_execution_status partial_runtime_correlated requires at least one covered runtime row.")
    return errors


def _validate_boundary_and_anomaly_ledgers(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    boundary_ledger = report.get("boundary_ledger")
    if not isinstance(boundary_ledger, list):
        errors.append("boundary_ledger must be a list.")
    else:
        for index, row in enumerate(boundary_ledger):
            row_path = f"boundary_ledger[{index}]"
            if not isinstance(row, dict):
                errors.append(f"{row_path} must be an object.")
                continue
            errors.extend(
                _validate_string_set(row.get("category"), f"{row_path}.category", FORBIDDEN_BOUNDARY_CATEGORIES)
            )
            if row.get("execution_status") != "blocked_by_boundary":
                errors.append(f"{row_path}.execution_status must be blocked_by_boundary.")
            if row.get("action_performed") is not False:
                errors.append(f"{row_path}.action_performed must be false.")
            if row.get("navigation_followed") is not False:
                errors.append(f"{row_path}.navigation_followed must be false.")
            errors.extend(_validate_evidence_ids(row.get("evidence_ids"), f"{row_path}.evidence_ids"))
    anomaly_ledger = report.get("anomaly_ledger")
    if not isinstance(anomaly_ledger, list):
        errors.append("anomaly_ledger must be a list.")
    else:
        for index, row in enumerate(anomaly_ledger):
            row_path = f"anomaly_ledger[{index}]"
            if not isinstance(row, dict):
                errors.append(f"{row_path} must be an object.")
                continue
            required = {
                "anomaly_id",
                "trigger_action",
                "expected_result",
                "observed_result",
                "evidence_status",
                "public_safe_alias",
                "likely_or_hypothesis_cause",
            }
            missing = sorted(required - set(row))
            if missing:
                errors.append(f"{row_path} missing required fields: {missing}.")
            errors.extend(
                _validate_string_set(
                    row.get("evidence_status"), f"{row_path}.evidence_status", ALLOWED_EVIDENCE_STATUSES
                )
            )
            errors.extend(_validate_evidence_ids(row.get("evidence_ids", []), f"{row_path}.evidence_ids"))
            for field_name in ("public_safe_alias", "likely_or_hypothesis_cause"):
                if field_name in row and (not isinstance(row.get(field_name), str) or not row.get(field_name)):
                    errors.append(f"{row_path}.{field_name} must be a non-empty string.")
    return errors


def _validate_public_safety(report: dict[str, Any]) -> list[str]:
    public_safety = report.get("public_safety")
    if not isinstance(public_safety, dict):
        return ["public_safety must be an object."]
    errors: list[str] = []
    for flag in sorted(FORBIDDEN_PUBLIC_FLAGS):
        if public_safety.get(flag) is not False:
            errors.append(f"public_safety.{flag} must be false.")
    return errors


def _validate_coverage_summary(report: dict[str, Any]) -> list[str]:
    summary = report.get("coverage_summary")
    if not isinstance(summary, dict):
        return ["coverage_summary must be an object."]
    errors: list[str] = []
    for field_name in ("counts_by_api_category", "counts_by_runtime_category", "counts_by_execution_status"):
        _, field_errors = _validate_count_map(summary.get(field_name), f"coverage_summary.{field_name}")
        errors.extend(field_errors)
    return errors


def validate_public_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(report))
    if missing:
        errors.append(f"report missing required fields: {missing}.")
    if report.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}.")
    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}.")
    if report.get("tool_name") != TOOL_NAME:
        errors.append(f"tool_name must be {TOOL_NAME}.")
    if report.get("mode") != "BOUNDED_AUTONOMOUS":
        errors.append("mode must be BOUNDED_AUTONOMOUS.")
    if report.get("production_safety_classification") != "PROD_CONDITIONAL_LIVE_READ_ONLY_SAFE_LANE":
        errors.append("production_safety_classification must be PROD_CONDITIONAL_LIVE_READ_ONLY_SAFE_LANE.")
    errors.extend(
        _validate_string_set(report.get("overall_status"), "overall_status", ALLOWED_OVERALL_STATUSES)
    )
    errors.extend(_validate_string_set(report.get("evidence_status"), "evidence_status", ALLOWED_EVIDENCE_STATUSES))
    errors.extend(
        _validate_string_set(
            report.get("runtime_execution_status"),
            "runtime_execution_status",
            {"not_run", "blocked", "partial_runtime_correlated", "unknown"},
        )
    )
    errors.extend(
        _validate_string_set(
            report.get("live_api_execution_status"),
            "live_api_execution_status",
            {"not_run", "blocked", "partial_read_only_covered", "unknown"},
        )
    )
    errors.extend(_validate_safe_lane(report))
    errors.extend(_validate_budget(report))
    errors.extend(_validate_preflight(report))
    errors.extend(_validate_coverage_summary(report))
    errors.extend(_validate_api_ledger(report))
    errors.extend(_validate_runtime_ledger(report))
    errors.extend(_validate_boundary_and_anomaly_ledgers(report))
    errors.extend(_validate_public_safety(report))
    if report.get("overall_status") == "pass_read_only_safe_lane":
        if report.get("live_api_execution_status") != "partial_read_only_covered":
            errors.append("overall_status pass_read_only_safe_lane requires live_api_execution_status partial_read_only_covered.")
        if report.get("runtime_execution_status") != "partial_runtime_correlated":
            errors.append("overall_status pass_read_only_safe_lane requires runtime_execution_status partial_runtime_correlated.")
        if report.get("unverified_areas"):
            errors.append("overall_status pass_read_only_safe_lane requires empty unverified_areas.")
        api_rows = report.get("api_coverage_ledger", [])
        if isinstance(api_rows, list):
            not_covered = [
                row.get("category")
                for row in api_rows
                if isinstance(row, dict) and row.get("execution_status") != "covered"
            ]
            if not_covered:
                errors.append("overall_status pass_read_only_safe_lane requires every API row to be covered.")
            not_confirmed = [
                row.get("category")
                for row in api_rows
                if isinstance(row, dict) and row.get("evidence_status") != "confirmed"
            ]
            if not_confirmed:
                errors.append("overall_status pass_read_only_safe_lane requires every API row evidence_status to be confirmed.")
            non_positive_requests = [
                row.get("category")
                for row in api_rows
                if isinstance(row, dict)
                and (not isinstance(row.get("request_count"), int) or row.get("request_count", 0) <= 0)
            ]
            if non_positive_requests:
                errors.append("overall_status pass_read_only_safe_lane requires every API row request_count to be positive.")
            request_sum = sum(
                row.get("request_count", 0)
                for row in api_rows
                if isinstance(row, dict) and isinstance(row.get("request_count"), int)
            )
            budget = report.get("budget", {})
            if isinstance(budget, dict) and budget.get("total_live_request_count") != request_sum:
                errors.append("overall_status pass_read_only_safe_lane requires budget.total_live_request_count to equal API row request_count sum.")
    if not isinstance(report.get("blocked_reasons"), list):
        errors.append("blocked_reasons must be a list.")
    if not isinstance(report.get("unverified_areas"), list):
        errors.append("unverified_areas must be a list.")
    errors.extend(_raw_value_findings(report))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path, help="TASK-037 public-safe summary JSON.")
    args = parser.parse_args(argv)

    report, read_error = _read_json(args.report)
    if read_error:
        print(read_error, file=sys.stderr)
        return 2
    assert report is not None
    errors = validate_public_report(report)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"{TASK_ID} public report validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
