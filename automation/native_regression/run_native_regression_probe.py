"""Generate or validate TASK-024 native post-auth regression reports.

Default execution is fail-closed and performs no ADB, Android, APK, network or
production interaction. Runtime execution requires explicit `--allow-runtime`
and, for this repository version, an already collected public-safe input report.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "task024-native-regression-summary-v1"
SUITE_SCHEMA_VERSION = "task024-native-regression-suite-v1"
TASK_ID = "TASK-024"
MODE = "BOUNDED_AUTONOMOUS"
RAW_EVIDENCE_ROOT = Path(".qa_local/evidence/task-024")
PUBLIC_REPORT_ROOT = Path("docs/qa/reports")
DEFAULT_SUITE = Path("docs/qa/native-regression/task024_native_regression_suite.json")

TARGET_ALIASES = {
    "device_alias": "tv-tpv-013",
    "runtime_profile_alias": "tv-tpv-a12-013",
    "build_alias": "task-005-local-apk-001",
    "synthetic_user_alias": "qa-user-phone-001",
}

REQUIRED_CASE_IDS = {f"NR-{index:03d}" for index in range(1, 11)}
OPTIONAL_CASE_IDS = {"NR-011", "NR-012"}
RUN_STATUSES = {"pass", "pass_with_known_anomalies", "partial", "blocked", "fail"}
RUNTIME_STATUSES = {"pass", "partial", "blocked", "not_run", "fail"}
CASE_STATUSES = {"pass", "fail", "blocked", "blocked_by_boundary", "not_run", "known_anomaly"}
EVIDENCE_STATUSES = {"confirmed", "likely", "hypothesis", "unknown"}
BOUNDARY_STATUSES = {"blocked_by_boundary", "not_run_out_of_scope", "blocked", "classified_not_entered"}
NON_PASS_CASE_STATUSES = {"fail", "blocked", "blocked_by_boundary", "not_run"}

FALSE_PUBLIC_SAFETY_FLAGS = {
    "raw_phone_otp_public",
    "raw_device_identifiers_public",
    "raw_screenshots_public",
    "raw_xml_public",
    "raw_logs_public",
    "payment_webview_stream_entered",
    "profile_account_mutation_entered",
}
FALSE_COVERAGE_CLAIMS = {
    "exhaustive_app_navigation",
    "complete_dynamic_value_inventory",
    "payment_or_stream_covered",
}

URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
LOCAL_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users|tmp|var|private)/|\.qa_local[\\/])", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<![\w+])\+?\d[\d\s().-]{8,}\d(?!\w)")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?\b")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
ANDROID_ID_RE = re.compile(r"\b[0-9a-fA-F]{16}\b")
HEX_HASH_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")
SECRET_PAIR_RE = re.compile(
    r"\b(token|secret|password|cookie|session|authorization|api[_-]?key|bearer|otp)\s*[:=]\s*[^\s,;]+",
    re.IGNORECASE,
)
RAW_ARTIFACT_RE = re.compile(r"\.(?:png|jpg|jpeg|webp|mp4|mov|log|txt|xml|apk|aab|apks|xapk)$", re.IGNORECASE)
PRIVATE_ROUTE_RE = re.compile(r"\b(?:deeplink|endpoint|header|payload|activity|package|class)\s*[:=]", re.IGNORECASE)
FIXED_VALUE_DUMP_RE = re.compile(
    r"\b(?:game_title|server_alias|server_count|ping_ms|gpu|cpu|tariff|price|qr_target|account_label)\s*[:=]",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_output_path(path: str | Path, *, public_output: bool = False) -> bool:
    normalized = Path(path)
    if normalized.is_absolute() or ".." in normalized.parts:
        return False
    base = PUBLIC_REPORT_ROOT if public_output else RAW_EVIDENCE_ROOT
    expected_parts = ("docs", "qa", "reports") if public_output else (".qa_local", "evidence", "task-024")
    if normalized.parts[: len(expected_parts)] != expected_parts:
        return False
    if public_output and normalized.suffix != ".json":
        return False
    try:
        resolved_base = base.resolve(strict=False)
        candidate = base
        for part in normalized.parts[len(expected_parts) : -1]:
            candidate = candidate / part
            if candidate.exists():
                candidate.resolve(strict=True).relative_to(resolved_base)
    except (OSError, ValueError):
        return False
    return True


def public_safety_findings(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            findings.extend(public_safety_findings(child, f"{path}.{key}"))
        return findings
    if isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(public_safety_findings(child, f"{path}[{index}]"))
        return findings
    if not isinstance(value, str) or not value:
        return findings
    if URL_RE.search(value):
        findings.append(f"{path} contains a URL-like value.")
    if LOCAL_PATH_RE.search(value):
        findings.append(f"{path} contains a raw local path.")
    if PHONE_RE.search(value):
        findings.append(f"{path} contains a phone-like value.")
    if IP_RE.search(value):
        findings.append(f"{path} contains an IP-like value.")
    if MAC_RE.search(value):
        findings.append(f"{path} contains a MAC-like value.")
    if ANDROID_ID_RE.search(value):
        findings.append(f"{path} contains an Android-ID-like value.")
    if HEX_HASH_RE.search(value):
        findings.append(f"{path} contains a hash-like value.")
    if SECRET_PAIR_RE.search(value):
        findings.append(f"{path} contains a secret-like key/value.")
    if RAW_ARTIFACT_RE.search(value):
        findings.append(f"{path} contains a raw artifact path.")
    if PRIVATE_ROUTE_RE.search(value):
        findings.append(f"{path} contains private route/internal metadata.")
    if FIXED_VALUE_DUMP_RE.search(value):
        findings.append(f"{path} contains a fixed dynamic-value dump.")
    return findings


def default_blocked_report(reason: str = "--allow-runtime was not provided") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "task_id": TASK_ID,
        "mode": MODE,
        "run_status": "blocked",
        "overall_status": "blocked",
        "runtime_execution_status": "not_run",
        "runtime_lane": TARGET_ALIASES,
        "blocked_reasons": [reason],
        "phase_gates": {
            "phase_a_repository_hygiene": "required_before_runtime",
            "phase_b_model_validator": "required_before_runtime",
            "phase_c_runtime": "not_run",
        },
        "regression_cases": [
            {
                "case_id": case_id,
                "status": "not_run",
                "evidence_status": "unknown",
                "reason": reason,
            }
            for case_id in sorted(REQUIRED_CASE_IDS)
        ],
        "session_persistence_checkpoints": [],
        "boundary_ledger": [],
        "known_anomalies_rechecked": [],
        "new_anomalies": [],
        "public_safety": {
            "raw_phone_otp_public": False,
            "raw_device_identifiers_public": False,
            "raw_screenshots_public": False,
            "raw_xml_public": False,
            "raw_logs_public": False,
            "payment_webview_stream_entered": False,
            "profile_account_mutation_entered": False,
        },
        "coverage_claims": {
            "exhaustive_app_navigation": False,
            "complete_dynamic_value_inventory": False,
            "payment_or_stream_covered": False,
            "selected_lane_native_regression_only": True,
        },
        "dynamic_data_policy": {
            "assert_fixed_game_titles": False,
            "assert_fixed_server_rows": False,
            "assert_fixed_prices": False,
            "assert_raw_qr_targets": False,
        },
    }


def load_json_object(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return None, [f"{path.as_posix()} was not found."]
    except json.JSONDecodeError as exc:
        return None, [f"{path.as_posix()} is not valid JSON: {exc.msg}"]
    if not isinstance(loaded, dict):
        return None, [f"{path.as_posix()} must contain a JSON object."]
    return loaded, []


def validate_suite(suite: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if suite.get("schema_version") != SUITE_SCHEMA_VERSION:
        reasons.append(f"suite.schema_version must be {SUITE_SCHEMA_VERSION}.")
    if suite.get("task_id") != TASK_ID:
        reasons.append("suite.task_id must be TASK-024.")
    if suite.get("runtime_lane") != TARGET_ALIASES:
        reasons.append("suite.runtime_lane must match the selected TASK-024 lane aliases.")
    policy = suite.get("dynamic_data_policy")
    if not isinstance(policy, dict):
        reasons.append("suite.dynamic_data_policy must be an object.")
    else:
        for key in ("assert_fixed_game_titles", "assert_fixed_server_rows", "assert_fixed_prices", "assert_raw_qr_targets"):
            if policy.get(key) is not False:
                reasons.append(f"suite.dynamic_data_policy.{key} must be false.")
    cases = suite.get("cases")
    if not isinstance(cases, list):
        return reasons + ["suite.cases must be a list."]
    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            reasons.append(f"suite.cases[{index}] must be an object.")
            continue
        case_id = case.get("case_id")
        if case_id in seen:
            reasons.append(f"suite.cases[{index}].case_id is duplicated.")
        if not isinstance(case_id, str) or case_id not in REQUIRED_CASE_IDS | OPTIONAL_CASE_IDS:
            reasons.append(f"suite.cases[{index}].case_id is not recognized.")
        else:
            seen.add(case_id)
        if not isinstance(case.get("title"), str) or not case["title"].strip():
            reasons.append(f"suite.cases[{index}].title is required.")
    missing = sorted(REQUIRED_CASE_IDS - seen)
    if missing:
        reasons.append(f"suite is missing required cases: {missing}.")
    return sorted(set(reasons))


def validate_report_shape(report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    required = (
        "schema_version",
        "task_id",
        "runtime_lane",
        "run_status",
        "runtime_execution_status",
        "regression_cases",
        "session_persistence_checkpoints",
        "boundary_ledger",
        "known_anomalies_rechecked",
        "new_anomalies",
        "public_safety",
        "coverage_claims",
        "dynamic_data_policy",
    )
    for field in required:
        if field not in report:
            reasons.append(f"{field} is required.")
    if report.get("schema_version") != SCHEMA_VERSION:
        reasons.append(f"schema_version must be {SCHEMA_VERSION}.")
    if report.get("task_id") != TASK_ID:
        reasons.append("task_id must be TASK-024.")
    if report.get("runtime_lane") != TARGET_ALIASES:
        reasons.append("runtime_lane must match the selected TASK-024 lane aliases.")
    if report.get("run_status") not in RUN_STATUSES:
        reasons.append("run_status must be recognized.")
    if report.get("runtime_execution_status") not in RUNTIME_STATUSES:
        reasons.append("runtime_execution_status must be recognized.")
    if report.get("run_status") in {"pass", "pass_with_known_anomalies"} and report.get("runtime_execution_status") != "pass":
        reasons.append("run_status pass variants require runtime_execution_status=pass.")
    if report.get("runtime_execution_status") == "not_run" and report.get("run_status") != "blocked":
        reasons.append("runtime_execution_status=not_run requires run_status=blocked.")
    reasons.extend(public_safety_findings(report))
    reasons.extend(_validate_regression_cases(report.get("regression_cases")))
    reasons.extend(_validate_aggregate_case_status(report.get("run_status"), report.get("regression_cases")))
    reasons.extend(_validate_session_checkpoints(report.get("session_persistence_checkpoints")))
    reasons.extend(_validate_boundary_ledger(report.get("boundary_ledger")))
    reasons.extend(_validate_public_safety(report.get("public_safety")))
    reasons.extend(_validate_coverage_claims(report.get("coverage_claims")))
    reasons.extend(_validate_dynamic_data_policy(report.get("dynamic_data_policy")))
    reasons.extend(_validate_anomaly_list(report.get("known_anomalies_rechecked"), "known_anomalies_rechecked"))
    reasons.extend(_validate_anomaly_list(report.get("new_anomalies"), "new_anomalies"))
    return sorted(set(reasons))


def _validate_regression_cases(cases: Any) -> list[str]:
    if not isinstance(cases, list):
        return ["regression_cases must be a list."]
    reasons: list[str] = []
    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            reasons.append(f"regression_cases[{index}] must be an object.")
            continue
        case_id = case.get("case_id")
        if case_id in seen:
            reasons.append(f"regression_cases[{index}].case_id is duplicated.")
        if case_id in REQUIRED_CASE_IDS | OPTIONAL_CASE_IDS:
            seen.add(case_id)
        else:
            reasons.append(f"regression_cases[{index}].case_id is not recognized.")
        status = case.get("status")
        if status not in CASE_STATUSES:
            reasons.append(f"regression_cases[{index}].status is not recognized.")
        if case.get("evidence_status") not in EVIDENCE_STATUSES:
            reasons.append(f"regression_cases[{index}].evidence_status is not recognized.")
        if status == "pass" and case.get("evidence_status") != "confirmed":
            reasons.append(f"regression_cases[{index}].evidence_status must be confirmed for pass.")
        if status in {"blocked", "blocked_by_boundary", "not_run", "fail", "known_anomaly"} and not case.get("reason"):
            reasons.append(f"regression_cases[{index}].reason is required for {status}.")
        if status == "pass" and not case.get("evidence_ids"):
            reasons.append(f"regression_cases[{index}].evidence_ids are required for pass.")
        if case.get("boundary_entered") is True:
            reasons.append(f"regression_cases[{index}].boundary_entered must not be true.")
    missing = sorted(REQUIRED_CASE_IDS - seen)
    if missing:
        reasons.append(f"regression_cases missing required cases: {missing}.")
    return reasons


def _validate_aggregate_case_status(run_status: Any, cases: Any) -> list[str]:
    if not isinstance(cases, list) or run_status not in {"pass", "pass_with_known_anomalies"}:
        return []
    reasons: list[str] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        status = case.get("status")
        if status in NON_PASS_CASE_STATUSES:
            reasons.append(f"run_status={run_status} cannot include regression_cases[{index}].status={status}.")
        if run_status == "pass" and status == "known_anomaly":
            reasons.append(f"run_status=pass cannot include regression_cases[{index}].status=known_anomaly.")
    return reasons


def _validate_session_checkpoints(checkpoints: Any) -> list[str]:
    if not isinstance(checkpoints, list):
        return ["session_persistence_checkpoints must be a list."]
    reasons: list[str] = []
    seen: set[str] = set()
    for index, checkpoint in enumerate(checkpoints):
        if not isinstance(checkpoint, dict):
            reasons.append(f"session_persistence_checkpoints[{index}] must be an object.")
            continue
        checkpoint_id = checkpoint.get("checkpoint_id")
        if not isinstance(checkpoint_id, str) or not checkpoint_id.strip():
            reasons.append(f"session_persistence_checkpoints[{index}].checkpoint_id is required.")
        elif checkpoint_id in seen:
            reasons.append(f"session_persistence_checkpoints[{index}].checkpoint_id is duplicated.")
        else:
            seen.add(checkpoint_id)
        status = checkpoint.get("status")
        if status not in CASE_STATUSES:
            reasons.append(f"session_persistence_checkpoints[{index}].status is not recognized.")
        if checkpoint.get("evidence_status") not in EVIDENCE_STATUSES:
            reasons.append(f"session_persistence_checkpoints[{index}].evidence_status is not recognized.")
        if status == "pass":
            if checkpoint.get("evidence_status") != "confirmed":
                reasons.append(f"session_persistence_checkpoints[{index}].evidence_status must be confirmed for pass.")
            if not checkpoint.get("evidence_ids"):
                reasons.append(f"session_persistence_checkpoints[{index}].evidence_ids are required for pass.")
        if status in {"blocked", "blocked_by_boundary", "not_run", "fail", "known_anomaly"} and not checkpoint.get("reason"):
            reasons.append(f"session_persistence_checkpoints[{index}].reason is required for {status}.")
    return reasons


def _validate_boundary_ledger(boundaries: Any) -> list[str]:
    if not isinstance(boundaries, list):
        return ["boundary_ledger must be a list."]
    reasons: list[str] = []
    seen: set[str] = set()
    for index, boundary in enumerate(boundaries):
        if not isinstance(boundary, dict):
            reasons.append(f"boundary_ledger[{index}] must be an object.")
            continue
        boundary_id = boundary.get("boundary_id")
        if not isinstance(boundary_id, str) or not boundary_id.strip():
            reasons.append(f"boundary_ledger[{index}].boundary_id is required.")
        elif boundary_id in seen:
            reasons.append(f"boundary_ledger[{index}].boundary_id is duplicated.")
        else:
            seen.add(boundary_id)
        if boundary.get("status") not in BOUNDARY_STATUSES:
            reasons.append(f"boundary_ledger[{index}].status must be a boundary-safe terminal status.")
        if boundary.get("evidence_status") != "confirmed":
            reasons.append(f"boundary_ledger[{index}].evidence_status must be confirmed.")
        if boundary.get("entered") is not False:
            reasons.append(f"boundary_ledger[{index}].entered must be false.")
        if boundary.get("result") == "pass":
            reasons.append(f"boundary_ledger[{index}].result must not be pass.")
        if not boundary.get("evidence_ids"):
            reasons.append(f"boundary_ledger[{index}].evidence_ids are required.")
    return reasons


def _validate_public_safety(flags: Any) -> list[str]:
    if not isinstance(flags, dict):
        return ["public_safety must be an object."]
    reasons: list[str] = []
    for key in FALSE_PUBLIC_SAFETY_FLAGS:
        if flags.get(key) is not False:
            reasons.append(f"public_safety.{key} must be false.")
    return reasons


def _validate_coverage_claims(claims: Any) -> list[str]:
    if not isinstance(claims, dict):
        return ["coverage_claims must be an object."]
    reasons: list[str] = []
    for key in FALSE_COVERAGE_CLAIMS:
        if claims.get(key) is not False:
            reasons.append(f"coverage_claims.{key} must be false.")
    if claims.get("selected_lane_native_regression_only") is not True:
        reasons.append("coverage_claims.selected_lane_native_regression_only must be true.")
    return reasons


def _validate_dynamic_data_policy(policy: Any) -> list[str]:
    if not isinstance(policy, dict):
        return ["dynamic_data_policy must be an object."]
    reasons: list[str] = []
    for key in ("assert_fixed_game_titles", "assert_fixed_server_rows", "assert_fixed_prices", "assert_raw_qr_targets"):
        if policy.get(key) is not False:
            reasons.append(f"dynamic_data_policy.{key} must be false.")
    return reasons


def _validate_anomaly_list(items: Any, field: str) -> list[str]:
    if not isinstance(items, list):
        return [f"{field} must be a list."]
    reasons: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            reasons.append(f"{field}[{index}] must be an object.")
            continue
        if item.get("evidence_status") not in EVIDENCE_STATUSES:
            reasons.append(f"{field}[{index}].evidence_status is not recognized.")
    return reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TASK-024 native post-auth regression gate.")
    parser.add_argument("--allow-runtime", action="store_true", help="Explicitly allow PROD_CONDITIONAL runtime mode.")
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE, help="Regression suite definition JSON.")
    parser.add_argument("--input-report", type=Path, default=None, help="Prebuilt public-safe runtime report to validate/write.")
    parser.add_argument("--raw-output", type=Path, default=None, help="Local raw output path under .qa_local/evidence/task-024/.")
    parser.add_argument("--public-output", type=Path, default=None, help="Public summary path under docs/qa/reports/*.json.")
    args = parser.parse_args(argv)

    raw_output_valid = args.raw_output is None or validate_output_path(args.raw_output, public_output=False)
    public_output_valid = args.public_output is None or validate_output_path(args.public_output, public_output=True)
    suite, suite_load_errors = load_json_object(args.suite)
    suite_errors = suite_load_errors if suite is None else validate_suite(suite)

    if not raw_output_valid:
        report = default_blocked_report("raw output path must stay under .qa_local/evidence/task-024/")
    elif not public_output_valid:
        report = default_blocked_report("public output path must stay under docs/qa/reports/*.json")
    elif suite_errors:
        report = default_blocked_report("; ".join(suite_errors))
    elif not args.allow_runtime:
        report = default_blocked_report()
    elif args.input_report is None:
        report = default_blocked_report("--allow-runtime was provided, but no approved TASK-024 runtime collector/input report was provided")
        report["runtime_execution_status"] = "blocked"
    else:
        loaded_report, load_errors = load_json_object(args.input_report)
        if loaded_report is None:
            report = default_blocked_report("; ".join(load_errors))
        else:
            errors = validate_report_shape(loaded_report)
            report = loaded_report if not errors else default_blocked_report("; ".join(errors))

    output_paths_valid = raw_output_valid and public_output_valid
    if args.public_output is not None and output_paths_valid:
        args.public_output.parent.mkdir(parents=True, exist_ok=True)
        args.public_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.raw_output is not None and output_paths_valid:
        args.raw_output.parent.mkdir(parents=True, exist_ok=True)
        args.raw_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
